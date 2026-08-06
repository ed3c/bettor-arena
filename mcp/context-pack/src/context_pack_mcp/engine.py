from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import stat
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "repo-context-pack/v1"
MIN_BUDGET_BYTES = 1_024
MAX_BUDGET_BYTES = 65_536
DEFAULT_MAX_SOURCE_BYTES = 2 * 1024 * 1024


class ContextPackError(ValueError):
    """A fail-closed input, source-integrity, parse, or budget error."""


@dataclass(frozen=True)
class _SourceSnapshot:
    relative_path: str
    text: str
    source_bytes: int
    sha256: str


@dataclass(frozen=True)
class _Scope:
    qualified_name: str
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


class _ScopeCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.scopes: list[_Scope] = []

    def _visit_scope(self, node: ast.AST, name: str) -> None:
        self.stack.append(name)
        assert isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        self.scopes.append(_Scope(".".join(self.stack), node))
        self.generic_visit(node)
        self.stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_scope(node, node.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_scope(node, node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_scope(node, node.name)


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _optional_text(value: str, limit: int = 280) -> tuple[str, bool]:
    normalized = _normalize_text(value)
    if len(normalized) <= limit:
        return normalized, False
    return normalized[: limit - 1] + "…", True


def _signature(scope: _Scope) -> str:
    node = scope.node
    if isinstance(node, ast.ClassDef):
        bases = [ast.unparse(base) for base in node.bases]
        bases.extend(
            f"{ast.unparse(keyword.arg) if keyword.arg else '**'}={ast.unparse(keyword.value)}"
            for keyword in node.keywords
        )
        suffix = f"({', '.join(bases)})" if bases else ""
        return f"class {scope.qualified_name}{suffix}"

    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    type_params = getattr(node, "type_params", [])
    type_suffix = f"[{', '.join(ast.unparse(item) for item in type_params)}]" if type_params else ""
    return f"{prefix} {scope.qualified_name}{type_suffix}({ast.unparse(node.args)}){returns}"


class _SemanticCollector(ast.NodeVisitor):
    def __init__(self, root: ast.FunctionDef | ast.AsyncFunctionDef, path: str) -> None:
        self.root = root
        self.path = path
        self.evidence: list[dict[str, Any]] = []

    def _add(self, kind: str, node: ast.AST, text: str, mandatory: bool = False) -> None:
        rendered, text_truncated = (
            (_normalize_text(text), False) if mandatory else _optional_text(text)
        )
        self.evidence.append(
            {
                "kind": kind,
                "source_ref": f"{self.path}:{getattr(node, 'lineno', 0)}",
                "line_start": getattr(node, "lineno", 0),
                "line_end": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                "text": rendered,
                "text_truncated": text_truncated,
                "mandatory": mandatory,
            }
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node is self.root:
            self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node is self.root:
            self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return

    def visit_If(self, node: ast.If) -> None:
        self._add("guard", node, f"if {ast.unparse(node.test)}")
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self._add("guard", node, f"while {ast.unparse(node.test)}")
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self._add("guard", node, ast.unparse(node))
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        self._add("raise", node, ast.unparse(node))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self._add("mutation", node, ast.unparse(node))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._add("mutation", node, ast.unparse(node))
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._add("mutation", node, ast.unparse(node))
        self.generic_visit(node)

    def visit_Delete(self, node: ast.Delete) -> None:
        self._add("mutation", node, ast.unparse(node))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        is_dynamic = (
            isinstance(node.func, ast.Name)
            and node.func.id in {"eval", "exec", "getattr", "setattr", "delattr"}
        ) or not isinstance(node.func, (ast.Name, ast.Attribute))
        self._add(
            "unresolved_dynamic_call" if is_dynamic else "call",
            node,
            ast.unparse(node),
            mandatory=is_dynamic,
        )
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        self._add("return", node, ast.unparse(node))
        self.generic_visit(node)


def _encoded_size(payload: dict[str, Any]) -> int:
    return len(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _stabilize_size(payload: dict[str, Any]) -> int:
    size = 0
    for _ in range(4):
        payload["context_bytes"] = size
        measured = _encoded_size(payload)
        if measured == size:
            return measured
        size = measured
    payload["context_bytes"] = size
    return _encoded_size(payload)


class RepositoryContextEngine:
    """Build deterministic, source-bound Python context packs inside one repository root."""

    def __init__(
        self,
        root: Path,
        *,
        max_source_bytes: int = DEFAULT_MAX_SOURCE_BYTES,
        cache_entries: int = 128,
    ) -> None:
        resolved = root.resolve(strict=True)
        if not resolved.is_dir():
            raise ContextPackError(f"repository root is not a directory: {resolved}")
        self.root = resolved
        self.max_source_bytes = max_source_bytes
        self.cache_entries = cache_entries
        self._cache: OrderedDict[tuple[str, str, str, int], dict[str, Any]] = OrderedDict()

    @property
    def root_id(self) -> str:
        return hashlib.sha256(str(self.root).encode("utf-8")).hexdigest()[:12]

    def status(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "ready",
            "root_id": self.root_id,
            "read_only": True,
            "languages": ["python"],
            "allowed_suffixes": [".py"],
            "max_source_bytes": self.max_source_bytes,
            "budget_bytes": {"min": MIN_BUDGET_BYTES, "max": MAX_BUDGET_BYTES},
            "cache_entries": {"current": len(self._cache), "max": self.cache_entries},
            "completeness": "partial",
        }

    def _read_source(self, relative_path: str) -> _SourceSnapshot:
        if not relative_path or Path(relative_path).is_absolute():
            raise ContextPackError("relative_path must be a non-empty repository-relative path")
        parts = Path(relative_path).parts
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise ContextPackError("relative_path must not contain traversal or empty components")
        normalized = Path(*parts).as_posix()
        suffix = Path(parts[-1]).suffix
        if suffix != ".py":
            raise ContextPackError(f"unsupported source type {suffix!r}; only .py is admitted")
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise ContextPackError("secure repository traversal is unsupported on this operating system")
        common_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        directory_flags = common_flags | os.O_DIRECTORY
        directory_fd: int | None = None
        descriptor: int | None = None
        try:
            directory_fd = os.open(self.root, directory_flags)
            for component in parts[:-1]:
                next_fd = os.open(component, directory_flags, dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = next_fd
            descriptor = os.open(parts[-1], common_flags, dir_fd=directory_fd)
        except OSError as exc:
            raise ContextPackError(
                "path could not be opened inside the repository without following symlinks"
            ) from exc
        finally:
            if directory_fd is not None:
                os.close(directory_fd)
        assert descriptor is not None
        with os.fdopen(descriptor, "rb") as source_file:
            before = os.fstat(source_file.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ContextPackError("path is not a regular file")
            if before.st_size > self.max_source_bytes:
                raise ContextPackError(
                    f"source exceeds max_source_bytes: {before.st_size} > {self.max_source_bytes}"
                )
            raw = source_file.read(self.max_source_bytes + 1)
            after = os.fstat(source_file.fileno())
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if len(raw) > self.max_source_bytes:
            raise ContextPackError(f"source exceeds max_source_bytes: > {self.max_source_bytes}")
        if identity_before != identity_after or len(raw) != after.st_size:
            raise ContextPackError("source changed while it was being read; retry with a fresh snapshot")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContextPackError("source is not valid UTF-8") from exc
        return _SourceSnapshot(normalized, text, len(raw), hashlib.sha256(raw).hexdigest())

    def build_python_context_pack(
        self,
        relative_path: str,
        *,
        symbol: str | None = None,
        max_bytes: int = 16_000,
    ) -> dict[str, Any]:
        if not MIN_BUDGET_BYTES <= max_bytes <= MAX_BUDGET_BYTES:
            raise ContextPackError(
                f"max_bytes must be between {MIN_BUDGET_BYTES} and {MAX_BUDGET_BYTES}"
            )
        requested_symbol = (symbol or "").strip()
        snapshot = self._read_source(relative_path)
        cache_key = (snapshot.relative_path, snapshot.sha256, requested_symbol, max_bytes)
        if cache_key in self._cache:
            cached = self._cache.pop(cache_key)
            self._cache[cache_key] = cached
            return copy.deepcopy(cached)

        try:
            tree = ast.parse(snapshot.text, filename=snapshot.relative_path)
        except SyntaxError as exc:
            raise ContextPackError(
                f"Python parse failed at {snapshot.relative_path}:{exc.lineno}: {exc.msg}"
            ) from exc

        collector = _ScopeCollector()
        collector.visit(tree)
        if requested_symbol:
            exact = [scope for scope in collector.scopes if scope.qualified_name == requested_symbol]
            if not exact:
                raise ContextPackError(f"symbol not found: {requested_symbol}")
            selected = [
                scope
                for scope in collector.scopes
                if scope.qualified_name == requested_symbol
                or scope.qualified_name.startswith(requested_symbol + ".")
            ]
        else:
            selected = collector.scopes

        evidence: list[dict[str, Any]] = []
        for scope in selected:
            node = scope.node
            for decorator in node.decorator_list:
                decorator_text, decorator_truncated = _optional_text("@" + ast.unparse(decorator))
                evidence.append(
                    {
                        "kind": "decorator",
                        "source_ref": f"{snapshot.relative_path}:{decorator.lineno}",
                        "line_start": decorator.lineno,
                        "line_end": getattr(decorator, "end_lineno", decorator.lineno),
                        "text": decorator_text,
                        "text_truncated": decorator_truncated,
                        "mandatory": False,
                    }
                )
            evidence.append(
                {
                    "kind": "signature",
                    "source_ref": f"{snapshot.relative_path}:{node.lineno}",
                    "line_start": node.lineno,
                    "line_end": node.lineno,
                    "text": _normalize_text(_signature(scope)),
                    "text_truncated": False,
                    "mandatory": True,
                }
            )
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                semantics = _SemanticCollector(node, snapshot.relative_path)
                semantics.visit(node)
                evidence.extend(semantics.evidence)

        unique: dict[tuple[str, int, str], dict[str, Any]] = {}
        for item in evidence:
            unique[(item["kind"], item["line_start"], item["text"])] = item
        evidence = sorted(unique.values(), key=lambda item: (item["line_start"], item["kind"], item["text"]))
        mandatory = [item for item in evidence if item["mandatory"]]
        optional = [item for item in evidence if not item["mandatory"]]
        priority = {"guard": 0, "raise": 1, "mutation": 2, "call": 3, "return": 4, "decorator": 5}
        optional.sort(key=lambda item: (priority.get(item["kind"], 99), item["line_start"], item["text"]))

        def assemble(selected_evidence: list[dict[str, Any]]) -> dict[str, Any]:
            ordered = sorted(
                selected_evidence,
                key=lambda item: (item["line_start"], item["kind"], item["text"]),
            )
            payload: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "language": "python",
                "completeness": "partial",
                "relative_path": snapshot.relative_path,
                "symbol": requested_symbol or None,
                "source_sha256": snapshot.sha256,
                "source_bytes": snapshot.source_bytes,
                "max_bytes": max_bytes,
                "context_bytes": 0,
                "truncated": len(ordered) < len(evidence),
                "evidence_count": len(ordered),
                "omitted_evidence_count": len(evidence) - len(ordered),
                "evidence": ordered,
            }
            _stabilize_size(payload)
            return payload

        selected_evidence = list(mandatory)
        payload = assemble(selected_evidence)
        if payload["context_bytes"] > max_bytes:
            raise ContextPackError(
                "mandatory signature/dynamic-call evidence exceeds max_bytes; increase the budget"
            )
        for item in optional:
            candidate = assemble(selected_evidence + [item])
            if candidate["context_bytes"] <= max_bytes:
                selected_evidence.append(item)
                payload = candidate
        payload = assemble(selected_evidence)

        self._cache[cache_key] = copy.deepcopy(payload)
        while len(self._cache) > self.cache_entries:
            self._cache.popitem(last=False)
        return payload
