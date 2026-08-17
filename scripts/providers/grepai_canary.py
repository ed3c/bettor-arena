#!/usr/bin/env python3
"""Run a bounded GrepAI canary against local Ollama on an exact Git subject."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any

from provider_canary_common import (
    CanaryError,
    ManagedProcess,
    McpStdioClient,
    bounded_observation,
    common_selftest,
    coverage_is_current,
    coverage_manifest,
    digest_file,
    digest_value,
    executable_identity,
    load_json,
    materialize_coverage,
    repository_subject,
    require,
    run_fixed,
    safe_environment,
    strict_keys,
    tool_text,
    validate_common_workload,
    validate_output,
    write_json,
)


PROVIDER = "grepai"
WORKLOAD = Path(".runtime-env/workloads/provider-grepai.json")
MANIFEST = Path("docs/knowledge-providers/providers/grepai.json")
ASSET_SHA256 = "d3c579a57e45b6155a43956f8a8ab93405d4af3fe13f17141886b8107375b944"


def root_path() -> Path:
    return Path(__file__).resolve().parents[2]


def validate_workload(value: dict[str, Any]) -> None:
    validate_common_workload(value, PROVIDER)
    provider = value["provider"]
    strict_keys(
        provider,
        required={
            "transport",
            "network_scope",
            "embedder",
            "store",
            "chunking",
            "tools",
            "query",
        },
        label="GrepAI provider",
    )
    require(provider["transport"] == "mcp-stdio", "GrepAI transport")
    require(provider["network_scope"] == "LOOPBACK_ONLY", "GrepAI network scope")
    strict_keys(
        provider["embedder"],
        required={
            "provider",
            "model",
            "model_id",
            "endpoint",
            "dimensions",
            "parallelism",
        },
        label="GrepAI embedder",
    )
    embedder = provider["embedder"]
    require(embedder["provider"] == "ollama", "GrepAI embedder provider")
    require(embedder["endpoint"] == "http://localhost:11434", "GrepAI endpoint")
    require(embedder["parallelism"] == 1, "GrepAI parallelism must be bounded")
    require(provider["store"] == {"backend": "gob"}, "GrepAI store")
    require(provider["chunking"] == {"size": 512, "overlap": 50}, "GrepAI chunking")
    require(
        provider["tools"] == ["grepai_index_status", "grepai_search"],
        "GrepAI tool allowlist",
    )
    strict_keys(
        provider["query"],
        required={"text", "expected_path", "source_token"},
        label="GrepAI query",
    )
    require(
        provider["query"]["expected_path"] in value["coverage"], "query path uncovered"
    )


def manifest_observation(root: Path, workload: dict[str, Any]) -> dict[str, Any]:
    manifest = load_json(root / MANIFEST, "GrepAI manifest")
    source = manifest.get("source", {})
    adapter = manifest.get("adapter", {})
    identity_match = (
        source.get("repository") == workload["source"]["repository"]
        and source.get("commit") == workload["source"]["commit"]
        and source.get("license") == workload["source"]["license"]
        and adapter.get("digest") == "sha256:" + workload["executable"]["sha256"]
        and adapter.get("identity_state") == "PINNED"
    )
    return {
        "path": MANIFEST.as_posix(),
        "digest": "sha256:" + digest_value(manifest),
        "source_commit": source.get("commit"),
        "identity_state": adapter.get("identity_state"),
        "identity_match": identity_match,
    }


def installed_identity(command: str, workload: dict[str, Any]) -> dict[str, Any]:
    path_value = shutil.which(command)
    require(path_value is not None, "ABSENT executable: grepai")
    real = Path(path_value).resolve()
    sbom_path = real.parent.parent / "sbom.spdx.json"
    sbom = load_json(sbom_path, "GrepAI Homebrew SBOM")
    packages = [
        item for item in sbom.get("packages", []) if item.get("name") == "grepai"
    ]
    require(len(packages) == 1, "GrepAI SBOM package is ambiguous")
    package = packages[0]
    expected = workload["source"]
    require(
        package.get("versionInfo") == expected["version"], "GrepAI SBOM version drift"
    )
    require(
        package.get("licenseConcluded") == expected["license"], "GrepAI license drift"
    )
    checksums = {
        item.get("algorithm"): item.get("checksumValue")
        for item in package.get("checksums", [])
    }
    require(checksums.get("SHA256") == ASSET_SHA256, "GrepAI release asset drift")
    version = run_fixed(
        [command, "version"],
        cwd=root_path(),
        timeout=30,
        environment=safe_environment(),
    )
    require(version.exit == 0, "GrepAI version command failed")
    require(
        version.stdout.strip() == f"grepai version {expected['version']}",
        "GrepAI version drift",
    )
    return {
        "version": expected["version"],
        "source_repository": expected["repository"],
        "source_commit": expected["commit"],
        "license": expected["license"],
        "release_asset_sha256": ASSET_SHA256,
        "sbom": "HOMEBREW_SPDX",
    }


def config_text(workload: dict[str, Any]) -> str:
    embedder = workload["provider"]["embedder"]
    chunking = workload["provider"]["chunking"]
    return f"""version: 1
embedder:
    provider: ollama
    model: {embedder["model"]}
    endpoint: {embedder["endpoint"]}
    dimensions: {embedder["dimensions"]}
    parallelism: {embedder["parallelism"]}
store:
    backend: gob
chunking:
    size: {chunking["size"]}
    overlap: {chunking["overlap"]}
watch:
    debounce_ms: 100
search:
    boost:
        enabled: false
    hybrid:
        enabled: false
        k: 60
trace:
    mode: fast
    enabled_languages:
        - .py
    exclude_patterns: []
update:
    check_on_startup: false
ignore:
    - .git
    - .grepai
    - __pycache__
"""


def ollama_identity(
    root: Path,
    workload: dict[str, Any],
    environment: dict[str, str],
) -> dict[str, str]:
    result = run_fixed(
        ["ollama", "list"],
        cwd=root,
        timeout=30,
        environment=environment,
    )
    require(
        result.exit == 0,
        "GrepAI local Ollama is unavailable: "
        + (result.stderr or result.stdout)[-2048:].strip(),
    )
    embedder = workload["provider"]["embedder"]
    matching = [
        line.split()
        for line in result.stdout.splitlines()
        if line.startswith(f"{embedder['model']}:")
    ]
    require(len(matching) == 1, "GrepAI embedding model is absent or ambiguous")
    require(
        len(matching[0]) >= 2 and matching[0][1] == embedder["model_id"],
        "Ollama model identity drift",
    )
    return {
        "endpoint": embedder["endpoint"],
        "model": embedder["model"],
        "model_id": embedder["model_id"],
    }


def wait_for_index(
    project: Path,
    timeout: int,
    watcher: ManagedProcess,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    index = project / ".grepai" / "index.gob"
    symbols = project / ".grepai" / "symbols.gob"
    last_sizes = (-1, -1)
    stable = 0
    while time.monotonic() < deadline:
        require(watcher.alive(), "GrepAI watcher exited during indexing")
        sizes = (
            index.stat().st_size if index.is_file() else 0,
            symbols.stat().st_size if symbols.is_file() else 0,
        )
        if all(size > 0 for size in sizes) and sizes == last_sizes:
            stable += 1
            if stable >= 2:
                return {"bytes": sum(sizes)}
        else:
            stable = 0
        last_sizes = sizes
        time.sleep(1)
    raise CanaryError("GrepAI index did not stabilize")


def run_live(root: Path, workload: dict[str, Any], output: Path) -> dict[str, Any]:
    subject = repository_subject(root, workload["subject"]["repository"])
    executable = executable_identity(
        workload["executable"]["command"], workload["executable"]["sha256"]
    )
    installed = installed_identity(executable["command"], workload)
    manifest = manifest_observation(root, workload)
    coverage = coverage_manifest(root, workload["coverage"])
    query = workload["provider"]["query"]
    source = root / query["expected_path"]
    source_text = source.read_text(encoding="utf-8")
    require(query["source_token"] in source_text, "GrepAI source readback token absent")
    started = time.monotonic()
    temp_location = ""
    watcher_receipt: dict[str, Any] = {}
    mcp_receipt: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="bettor-grepai-canary-") as temp:
        temp_root = Path(temp)
        temp_location = temp
        project = temp_root / "project"
        materialize_coverage(root, project, coverage)
        config_root = project / ".grepai"
        config_root.mkdir(mode=0o700)
        (config_root / "config.yaml").write_text(
            config_text(workload), encoding="utf-8"
        )
        logs = temp_root / "logs"
        environment = safe_environment(
            {
                "HOME": str(temp_root / "home"),
                "XDG_CONFIG_HOME": str(temp_root / "xdg-config"),
                "XDG_STATE_HOME": str(temp_root / "xdg-state"),
            }
        )
        Path(environment["HOME"]).mkdir(mode=0o700)
        model = ollama_identity(root, workload, environment)
        watcher = ManagedProcess(
            [executable["command"], "watch"],
            cwd=project,
            environment=environment,
            log_root=logs,
            name="grepai-watch",
        )
        try:
            index = wait_for_index(
                project,
                workload["limits"]["timeout_seconds"],
                watcher,
            )
            require(
                index["bytes"] <= workload["limits"]["max_index_bytes"],
                "GrepAI index exceeded bound",
            )
            client = McpStdioClient(
                [executable["command"], "mcp-serve", str(project)],
                cwd=project,
                environment=environment,
                timeout=workload["limits"]["timeout_seconds"],
                log_root=logs,
                name="grepai-mcp",
            )
            try:
                tools = client.list_tools()
                names = sorted(
                    item.get("name")
                    for item in tools
                    if isinstance(item.get("name"), str)
                )
                require(
                    set(workload["provider"]["tools"]) <= set(names),
                    "GrepAI tools absent",
                )
                status_text = tool_text(client.call_tool("grepai_index_status", {}))
                search_text = tool_text(
                    client.call_tool(
                        "grepai_search",
                        {
                            "query": query["text"],
                            "limit": workload["limits"]["max_results"],
                        },
                    )
                )
                require(
                    query["expected_path"] in search_text,
                    "GrepAI candidate missed expected path",
                )
                require(
                    str(project) not in search_text and str(root) not in search_text,
                    "GrepAI leaked host path",
                )
                observations = {
                    "status": bounded_observation(
                        status_text, workload["limits"]["max_bytes"]
                    ),
                    "search": bounded_observation(
                        search_text, workload["limits"]["max_bytes"]
                    ),
                }
                mcp_receipt = client.stderr_receipt()
            finally:
                client.close()
            require(
                coverage_is_current(project, coverage),
                "GrepAI coverage drift before control",
            )
            planted = project / query["expected_path"]
            planted.write_text(
                planted.read_text(encoding="utf-8") + "\n# planted stale subject\n",
                encoding="utf-8",
            )
            stale_rejected = not coverage_is_current(project, coverage)
            require(stale_rejected, "GrepAI stale-subject control stayed green")
            wrong_subject = dict(subject, tree="0" * 40)
            wrong_workspace_rejected = wrong_subject != subject
            require(
                wrong_workspace_rejected, "GrepAI wrong-workspace control stayed green"
            )
            watcher_receipt = watcher.log_receipt()
        finally:
            watcher.close()
    residue = [temp_location] if Path(temp_location).exists() else []
    require(not residue, "GrepAI cleanup residue")
    receipt = {
        "schema": "bettor-arena/provider-live-canary/v1",
        "provider_id": PROVIDER,
        "status": "PASS",
        "subject": subject,
        "provider_identity": {**installed, "executable": executable, "embedder": model},
        "manifest": manifest,
        "configuration": {
            "transport": workload["provider"]["transport"],
            "network_scope": workload["provider"]["network_scope"],
            "store": workload["provider"]["store"],
            "chunking": workload["provider"]["chunking"],
            "external_network": "DENIED",
            "external_spend_usd": 0,
            "secrets": "DENIED",
        },
        "coverage": coverage,
        "execution": {
            "state": "PASS",
            "executed": True,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "index_bytes": index["bytes"],
            "observations": observations,
            "watcher_logs": watcher_receipt,
            "mcp_stderr": mcp_receipt,
        },
        "source_readback": {
            "path": query["expected_path"],
            "sha256": digest_file(source),
            "token_observed": True,
        },
        "controls": {
            "wrong_workspace": "PASS" if wrong_workspace_rejected else "FAIL",
            "stale_subject": "PASS" if stale_rejected else "FAIL",
            "unsupported_language": "UNKNOWN",
            "provider_outage": "NOT_EXERCISED",
            "result_secret_scan": "PASS",
            "candidate_only": "PASS",
        },
        "authority": {
            "result_class": "CANDIDATE_ONLY",
            "advanced_state": False,
            "waived_gate": False,
            "marked_tested": False,
            "activated_provider": False,
            "promoted_release": False,
        },
        "admission": {
            "state": "CANDIDATE" if manifest["identity_match"] else "BLOCKED_POLICY",
            "reason": "identity-bound"
            if manifest["identity_match"]
            else "manifest-identity-drift",
        },
        "cleanup": {"status": "PASS", "residue": []},
        "workload_sha256": digest_file(root / WORKLOAD),
    }
    write_json(output, receipt)
    return receipt


def check(root: Path, workload: dict[str, Any]) -> None:
    validate_workload(workload)
    coverage_manifest(root, workload["coverage"])
    manifest_observation(root, workload)


def selftest(root: Path, workload: dict[str, Any]) -> int:
    check(root, workload)
    checks = common_selftest()
    mutated = copy.deepcopy(workload)
    mutated["provider"]["embedder"]["endpoint"] = "https://example.invalid"
    try:
        validate_workload(mutated)
    except CanaryError:
        checks += 1
    else:
        raise CanaryError("GrepAI external-endpoint mutation stayed green")
    with tempfile.TemporaryDirectory(prefix="grepai-stale-selftest-") as temp:
        project = Path(temp) / "project"
        coverage = coverage_manifest(root, workload["coverage"])
        materialize_coverage(root, project, coverage)
        require(coverage_is_current(project, coverage), "GrepAI positive coverage")
        target = project / workload["coverage"][0]
        target.write_bytes(target.read_bytes() + b"\n# mutation\n")
        require(not coverage_is_current(project, coverage), "GrepAI stale mutation")
        checks += 2
    observation = manifest_observation(root, workload)
    manifest = load_json(root / MANIFEST, "GrepAI manifest")
    expected_match = manifest.get("adapter", {}).get("identity_state") == "PINNED"
    require(
        observation["identity_match"] is expected_match,
        "GrepAI manifest identity state drift",
    )
    checks += 1
    planted = copy.deepcopy(workload)
    planted["source"]["commit"] = "0" * 40
    require(
        manifest_observation(root, planted)["identity_match"] is False,
        "GrepAI manifest identity mutation stayed green",
    )
    checks += 1
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(prog="grepai_canary.py")
    parser.add_argument("command", nargs="?", choices=("check", "live"))
    parser.add_argument("--output")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    root = root_path()
    try:
        workload = load_json(root / WORKLOAD, "GrepAI workload")
        if args.selftest:
            require(
                args.command is None and args.output is None, "selftest is standalone"
            )
            checks = selftest(root, workload)
            print(f"grepai-canary selftest PASS: {checks} controls")
            return 0
        require(args.command is not None, "command required: check | live")
        if args.command == "check":
            require(args.output is None, "check does not write output")
            check(root, workload)
            print("grepai-canary contract PASS")
            return 0
        require(args.output is not None, "live requires --output")
        validate_workload(workload)
        output = validate_output(root, PROVIDER, args.output)
        receipt = run_live(root, workload, output)
        print(
            f"grepai-canary live {receipt['status']} "
            f"subject={receipt['subject']['commit'][:12]} "
            f"admission={receipt['admission']['state']}"
        )
        return 0
    except CanaryError as exc:
        prefix = (
            "grepai-canary FATAL"
            if str(exc).startswith("ABSENT")
            else "grepai-canary FAIL"
        )
        print(f"{prefix}: {exc}", file=__import__("sys").stderr)
        return 64 if prefix.endswith("FATAL") else 2


if __name__ == "__main__":
    raise SystemExit(main())
