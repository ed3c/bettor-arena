#!/usr/bin/env python3
"""Hash-bound technical-equivalence packet runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent
PROFILE = ROOT / "profile" / "technical-equivalence.md"
REQUEST_SCHEMA = "technical-equivalence-request@1.0.0"
COMMERCIAL_SPDX_ALLOWLIST = {
    "0BSD",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "CC0-1.0",
    "ISC",
    "MIT",
    "Unlicense",
}
ADAPTER_TIMEOUT_SECONDS = 45 * 60


class ContractError(RuntimeError):
    pass


class VerificationFailure(RuntimeError):
    pass


class AdapterExit(RuntimeError):
    def __init__(self, code: int, receipt: Path):
        super().__init__(f"Gemini adapter exited {code}; receipt={receipt}")
        self.code = code


def canonical_bytes(payload: dict[str, Any], digest_field: str | None = None) -> bytes:
    body = dict(payload)
    if digest_field:
        body.pop(digest_field, None)
    return json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(payload: dict[str, Any], digest_field: str | None = None) -> str:
    return (
        "sha256:" + hashlib.sha256(canonical_bytes(payload, digest_field)).hexdigest()
    )


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ContractError(f"input absent: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"JSON object required: {path}")
    return value


def validate_request(request: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "request_id",
        "original_intent_ssot",
        "technical_viewpoint",
        "source_anchors",
        "fixed_context",
        "iteration_context",
        "emergent_context",
        "target_binding",
        "request_digest",
    }
    missing = sorted(required - request.keys())
    if missing:
        raise ContractError(f"request missing fields: {', '.join(missing)}")
    if request["schema_version"] != REQUEST_SCHEMA:
        raise ContractError(f"unsupported request schema: {request['schema_version']}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", str(request["request_id"])):
        raise ContractError("request_id is not path-safe")
    if not isinstance(request["source_anchors"], list) or not request["source_anchors"]:
        raise ContractError("source_anchors must be a non-empty list")
    for lane in ("fixed_context", "iteration_context", "emergent_context"):
        if not isinstance(request[lane], list):
            raise ContractError(f"{lane} must be a list")
    expected = digest(request, "request_digest")
    if request["request_digest"] != expected:
        raise ContractError(
            f"request digest mismatch: declared {request['request_digest']}, computed {expected}"
        )


def git_head(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ContractError(f"target-peer is not a git checkout: {repo}")
    return result.stdout.strip()


def assert_head_bound(repo: Path, relative_path: Path, current_bytes: bytes) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"HEAD:{relative_path.as_posix()}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout != current_bytes:
        raise ContractError(
            f"canonical source {relative_path} is not the bytes at HEAD; commit it before sync"
        )


def write_immutable(path: Path, payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != encoded:
            raise ContractError(f"immutable packet collision: {path}")
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)


def build_prompt(request: dict[str, Any]) -> str:
    profile = PROFILE.read_text(encoding="utf-8")
    anchors = json.dumps(request["source_anchors"], ensure_ascii=False, indent=2)
    return (
        "# Technical viewpoint → implementation-equivalent research\n\n"
        f"## Original intent SSOT\n{request['original_intent_ssot']}\n\n"
        f"## Technical viewpoint\n{request['technical_viewpoint']}\n\n"
        f"## Source anchors\n```json\n{anchors}\n```\n\n"
        f"{profile}\n\n{structured_output_contract()}\n"
    )


def parse_gap_topics(markdown: str) -> tuple[list[str], list[str]]:
    segment = markdown
    marker = re.search(r"可直接當研究題目|研究題目清單|研究題目", markdown)
    if marker:
        segment = markdown[marker.start() :]
    topics = [
        match.group(1).strip().strip("《》")
        for match in re.finditer(
            r"(?:^|\n)\s*(?:題目[一二三四五六七八九十]+|[0-9]{1,2})[.\)、:：]\s*《?([^\n》]+)》?",
            segment,
        )
        if len(match.group(1).strip()) > 6
    ]
    return topics[:6], topics[6:]


def structured_output_contract() -> str:
    return """

## 機器可讀候選附錄（必做）

報告末尾必須附上一個 fenced `json` block，且根物件只有
`technical_equivalence_candidates` 陣列。每個公開候選至少包含：
`candidate_id`、`claim`、`repo_url`、精確 40-hex `commit`、`spdx`、
`source_urls`、`code_anchors`、三個布林值 `load_bearing`、
`equivalence_uncertain`、`wrong_decision_costly`、`inference:false`，以及
`code_audit:{"status":"not_exercised"}`、`probe:{"status":"not_exercised"}`。
研究階段不得假造本機 audit/probe receipt。若沒有公開可驗實作，仍須輸出至少一個
`inference:true` 的候選並寫明 claim、source_urls 與可證偽條件；不得輸出空陣列。
""".strip()


def extract_structured_candidates(markdown: str) -> list[dict[str, Any]]:
    """Extract the explicit candidate appendix; prose is never treated as evidence."""
    candidates: list[dict[str, Any]] = []
    for match in re.finditer(
        r"```(?:json)?\s*\n?(.*?)```", markdown, re.DOTALL | re.IGNORECASE
    ):
        try:
            payload = json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        raw = payload.get("technical_equivalence_candidates")
        if not isinstance(raw, list):
            continue
        for item in raw:
            if not isinstance(item, dict):
                raise VerificationFailure(
                    "candidate appendix entries must be JSON objects"
                )
            candidates.append(item)
    return candidates


def plan_gap_prompts(
    primary_prompt: str, primary_report: str
) -> tuple[list[str], dict[str, Any]]:
    selected, truncated = parse_gap_topics(primary_report)
    if selected:
        prompts = [
            (
                "基於以下已知相關資訊，針對下列單一主題做一輪深度研究、建立完整知識體系："
                "補齊已知資訊未涵蓋的深度、機制、實作細節與外部佐證，勿重複已知內容。\n\n"
                "**技術實現等價物（必做）**：找出實現此主題的開源可商用庫（套件名 + repo 連結 + 授權條款）；"
                "若無公開實現等價物，則推論等價的生產環境配置並標為 `[推論]`。\n\n"
                f"## 研究主題\n{topic}\n\n## 原始研究請求\n{primary_prompt}\n\n"
                f"## 前一輪深度研究報告\n{primary_report}\n\n{structured_output_contract()}"
            )
            for topic in selected
        ]
        mode = "single-topic-fanout"
    else:
        prompts = [
            (
                "基於以下已知相關資訊，針對報告中所有未編號缺口做聚焦深度研究補齊，勿重複已知。\n\n"
                "**每一缺口都要給技術實現等價物**：優先開源可商用庫（套件名 + repo + 授權）；"
                "若無公開實現等價物，推論生產環境配置並標 `[推論]`。\n\n"
                f"## 原始研究請求\n{primary_prompt}\n\n## 前一輪深度研究報告\n{primary_report}\n\n"
                f"{structured_output_contract()}"
            )
        ]
        mode = "batch-fallback"
    return prompts, {
        "mode": mode,
        "selected": selected,
        "truncated": truncated,
        "selected_count": len(selected),
        "truncated_count": len(truncated),
        "max": 6,
    }


def collect_live_research(
    primary_prompt: str,
    invoke: Callable[[str, str], str],
) -> tuple[list[tuple[str, str]], list[dict[str, Any]], dict[str, Any]]:
    """Run primary + bounded gap research and return exact reports and candidates."""
    primary_report = invoke("primary", primary_prompt)
    if not primary_report.strip():
        raise VerificationFailure("Gemini primary research returned an empty report")
    prompts, ledger = plan_gap_prompts(primary_prompt, primary_report)
    reports = [("primary", primary_report)]
    for index, prompt in enumerate(prompts, start=1):
        label = f"gap-{index:02d}"
        report = invoke(label, prompt)
        if not report.strip():
            raise VerificationFailure(
                f"Gemini {label} research returned an empty report"
            )
        reports.append((label, report))

    candidates: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    for _label, report in reports:
        for candidate in extract_structured_candidates(report):
            fingerprint = canonical_bytes(candidate)
            if fingerprint not in seen:
                candidates.append(candidate)
                seen.add(fingerprint)
    if not candidates:
        raise VerificationFailure(
            "Gemini live research produced no machine-readable candidate appendix; "
            "an inference:true candidate is required when no public implementation exists"
        )
    return reports, candidates, ledger


def validate_result(result: dict[str, Any], research_digest: str) -> None:
    required = {
        "schema_version",
        "upstream_research_request_digest",
        "provider",
        "raw_markdown",
        "candidates",
        "research_result_digest",
    }
    missing = sorted(required - result.keys())
    if missing:
        raise ContractError(f"research result missing fields: {', '.join(missing)}")
    if result["schema_version"] != "technical-equivalence-research-result@1.0.0":
        raise ContractError(
            f"unsupported research result schema: {result['schema_version']}"
        )
    if result["upstream_research_request_digest"] != research_digest:
        raise ContractError("research result upstream digest mismatch")
    expected = digest(result, "research_result_digest")
    if result["research_result_digest"] != expected:
        raise ContractError(
            f"research result digest mismatch: declared {result['research_result_digest']}, computed {expected}"
        )
    if (
        not isinstance(result["raw_markdown"], str)
        or not result["raw_markdown"].strip()
    ):
        raise ContractError("research result raw_markdown must be non-empty")
    if not isinstance(result["candidates"], list) or not result["candidates"]:
        raise VerificationFailure(
            "research result requires a non-empty machine-readable candidate appendix; "
            "use an inference:true candidate when no public implementation exists"
        )


def grounding(candidate: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if candidate.get("inference") is True:
        for field in (
            "candidate_id",
            "claim",
            "source_urls",
            "falsification_conditions",
        ):
            if field not in candidate:
                raise ContractError(f"inference candidate missing field: {field}")
        if not str(candidate["claim"]).strip():
            raise ContractError("inference candidate claim must be non-empty")
        urls = candidate["source_urls"]
        if (
            not isinstance(urls, list)
            or not urls
            or any(not re.fullmatch(r"https://[^\s]+", str(url)) for url in urls)
        ):
            raise ContractError(
                "inference candidate requires primary https source_urls"
            )
        conditions = candidate["falsification_conditions"]
        if (
            not isinstance(conditions, list)
            or not conditions
            or any(not str(condition).strip() for condition in conditions)
        ):
            raise ContractError("inference candidate requires falsification_conditions")
        return "[推論]", ["producer explicitly declared no public verified equivalent"]
    risk_fields = ("load_bearing", "equivalence_uncertain", "wrong_decision_costly")
    if any(not isinstance(candidate.get(field), bool) for field in risk_fields):
        reasons.append("rebuild-trigger classification incomplete")
    for field in (
        "candidate_id",
        "claim",
        "repo_url",
        "commit",
        "spdx",
        "source_urls",
        "code_anchors",
    ):
        if field not in candidate:
            raise ContractError(f"candidate missing field: {field}")
    repo_url = candidate.get("repo_url")
    if not isinstance(repo_url, str) or not re.fullmatch(r"https://[^\s]+", repo_url):
        reasons.append("repo_url absent or not https")
    if not re.fullmatch(r"[0-9a-f]{40}", str(candidate.get("commit") or "")):
        reasons.append("exact 40-hex commit absent")
    if candidate.get("spdx") not in COMMERCIAL_SPDX_ALLOWLIST:
        reasons.append("SPDX absent or outside commercial allowlist")
    urls = candidate.get("source_urls")
    if (
        not isinstance(urls, list)
        or not urls
        or any(not re.fullmatch(r"https://[^\s]+", str(u)) for u in urls)
    ):
        reasons.append("primary source URLs absent or invalid")
    anchors = candidate.get("code_anchors")
    if not isinstance(anchors, list) or not anchors:
        reasons.append("code anchors absent")
    checkout = Path(str(candidate.get("checkout_path") or ""))
    if not checkout.is_dir():
        reasons.append("audited checkout absent")
    else:
        head = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
        )
        remote = subprocess.run(
            ["git", "-C", str(checkout), "remote", "get-url", "origin"],
            text=True,
            capture_output=True,
            check=False,
        )
        if head.returncode != 0 or head.stdout.strip() != candidate.get("commit"):
            reasons.append("audited checkout HEAD does not bind candidate commit")
        if remote.returncode != 0 or remote.stdout.strip().removesuffix(".git") != str(
            repo_url
        ).removesuffix(".git"):
            reasons.append("audited checkout origin does not bind repo URL")

    audit_data, audit_error = verified_evidence(
        candidate.get("code_audit"), "technical-equivalence-code-audit-receipt@1.0.0"
    )
    if audit_error:
        reasons.append(f"code audit {audit_error}")
    elif (
        audit_data.get("repo_url") != repo_url
        or audit_data.get("repo_commit") != candidate.get("commit")
        or audit_data.get("checkout_path") != str(checkout)
        or not set(candidate.get("code_anchors") or []).issubset(
            set(audit_data.get("code_anchors") or [])
        )
        or not audit_data.get("audited_files")
    ):
        reasons.append("code audit receipt bindings mismatch")

    probe_data, probe_error = verified_evidence(
        candidate.get("probe"), "technical-equivalence-probe-receipt@1.0.0"
    )
    if probe_error:
        reasons.append(f"real probe {probe_error}")
    elif (
        probe_data.get("repo_commit") != candidate.get("commit")
        or probe_data.get("exit") != 0
        or not isinstance(probe_data.get("command"), list)
        or not probe_data.get("command")
        or not probe_data.get("stdout_sha256")
        or not str(probe_data.get("observed_behavior") or "").strip()
    ):
        reasons.append("real probe receipt bindings mismatch")
    if any(candidate.get(field) is True for field in risk_fields):
        comparison, comparison_error = verified_evidence(
            candidate.get("rebuild_comparison"),
            "technical-equivalence-rebuild-comparison@1.0.0",
        )
        if comparison_error:
            reasons.append(f"load-bearing rebuild comparison {comparison_error}")
        elif (
            comparison.get("repo_commit") != candidate.get("commit")
            or not isinstance(comparison.get("baseline"), dict)
            or not isinstance(comparison.get("alternative"), dict)
            or not comparison.get("decision")
        ):
            reasons.append("load-bearing rebuild comparison bindings mismatch")
    return (
        ("candidate", reasons)
        if reasons
        else (
            "technical_equivalent",
            ["code audit, real probe and required rebuild comparison passed"],
        )
    )


def verified_evidence(value: Any, schema: str) -> tuple[dict[str, Any], str | None]:
    if not isinstance(value, dict) or value.get("status") != "passed":
        return {}, "not exercised"
    path_value, declared = value.get("path"), value.get("sha256")
    if not isinstance(path_value, str) or not isinstance(declared, str):
        return {}, "physical receipt path/digest absent"
    path = Path(path_value)
    if not path.is_file():
        return {}, "physical receipt absent"
    raw = path.read_bytes()
    actual = "sha256:" + hashlib.sha256(raw).hexdigest()
    if actual != declared:
        return {}, "receipt digest mismatch"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}, "receipt is invalid JSON"
    if not isinstance(payload, dict) or payload.get("schema_version") != schema:
        return {}, "receipt schema mismatch"
    return payload, None


def process_result(
    result_path: Path,
    research: dict[str, Any],
    run_dir: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    result = load_json(result_path)
    validate_result(result, research["research_request_digest"])
    selected, truncated = parse_gap_topics(result["raw_markdown"])
    classified = []
    for raw in result["candidates"]:
        if not isinstance(raw, dict):
            raise ContractError("candidate entries must be objects")
        state, reasons = grounding(raw)
        item = dict(raw)
        item["grounding_state"] = state
        item["grounding_reasons"] = reasons
        classified.append(item)
    verification = {
        "schema_version": "technical-equivalence-verification-bundle@1.0.0",
        "upstream_research_result_digest": result["research_result_digest"],
        "gap_topics": {
            "selected": selected,
            "truncated": truncated,
            "selected_count": len(selected),
            "truncated_count": len(truncated),
            "max": 6,
        },
        "candidates": classified,
        "semantic_loss_ledger": [
            {"mechanism": "P1-P9/V1-V5 rubric", "status": "preserved"},
            {"mechanism": "Path B four stages", "status": "preserved"},
            {
                "mechanism": "single/batch gap prompts",
                "status": "adapted",
                "note": "media-specific @aiDotEngineer fallback removed from host-neutral core",
            },
            {
                "mechanism": "browser/login/card-box v6.6",
                "status": "excluded",
                "note": "owned by optional upstream context/runtime adapter",
            },
        ],
        "semantic_judge": {
            "actor": "fresh-zero-context-semantic-judge",
            "preferred": "opus",
            "fallback": "codex",
            "status": "NOT_EXERCISED",
            "quality_status": "operational_substitute",
        },
    }
    verification["verification_bundle_digest"] = digest(
        verification, "verification_bundle_digest"
    )
    result_key = result["research_result_digest"].split(":", 1)[1][:12]
    verification_path = run_dir / f"verification-bundle.{result_key}.json"
    write_immutable(verification_path, verification)
    artifacts = {"verification_bundle": str(verification_path)}
    if not any(
        item["grounding_state"] == "technical_equivalent" for item in classified
    ):
        return verification, artifacts
    judge_packet = {
        "schema_version": "technical-equivalence-judge-packet@1.0.0",
        "upstream_verification_bundle_digest": verification[
            "verification_bundle_digest"
        ],
        "independence_contract": "fresh-zero-context",
        "allowed_context": [
            "technical viewpoint",
            "source anchors",
            "candidate evidence",
            "semantic-loss ledger",
        ],
        "forbidden_context": [
            "producer conversation",
            "other judge verdict",
            "desired promotion outcome",
        ],
        "task": "Reject any technical_equivalent classification not entailed by its code-audit, probe and rebuild receipts.",
        "candidates": classified,
        "semantic_loss_ledger": verification["semantic_loss_ledger"],
    }
    judge_packet["judge_packet_digest"] = digest(judge_packet, "judge_packet_digest")
    judge_key = verification["verification_bundle_digest"].split(":", 1)[1][:12]
    judge_path = run_dir / f"judge-packet.{judge_key}.json"
    write_immutable(judge_path, judge_packet)
    artifacts.update(
        {
            "judge_packet": str(judge_path),
            "expected_judge_result": str(run_dir / f"judge-result.{judge_key}.json"),
        }
    )
    return verification, artifacts


def validate_judge_result(
    path: Path, verification_digest: str, judge_packet_digest: str
) -> dict[str, Any]:
    result = load_json(path)
    required = {
        "schema_version",
        "upstream_verification_bundle_digest",
        "upstream_judge_packet_digest",
        "judge_id",
        "independence_contract",
        "verdict",
        "findings",
        "quality_status",
        "execution_receipt",
        "judge_result_digest",
    }
    missing = sorted(required - result.keys())
    if missing:
        raise ContractError(f"judge result missing fields: {', '.join(missing)}")
    if result["schema_version"] != "technical-equivalence-judge-result@1.0.0":
        raise ContractError(
            f"unsupported judge result schema: {result['schema_version']}"
        )
    if result["upstream_verification_bundle_digest"] != verification_digest:
        raise ContractError("judge result upstream digest mismatch")
    if result["upstream_judge_packet_digest"] != judge_packet_digest:
        raise ContractError("judge result is not bound to the exact zero-access packet")
    if result["independence_contract"] != "fresh-zero-context":
        raise ContractError("judge result did not use fresh-zero-context contract")
    if result["judge_id"] not in {"codex", "opus"}:
        raise ContractError("judge_id must be codex or opus")
    if result["quality_status"] not in {
        "operational_substitute",
        "calibrated_equivalent",
    }:
        raise ContractError("judge quality_status is not admitted")
    if result["verdict"] not in {"PASS", "FAIL"}:
        raise ContractError("judge verdict must be PASS or FAIL")
    execution, execution_error = verified_evidence(
        result.get("execution_receipt"),
        "technical-equivalence-judge-execution-receipt@1.0.0",
    )
    if execution_error:
        raise ContractError(f"judge execution_receipt {execution_error}")
    if (
        execution.get("judge_packet_digest") != judge_packet_digest
        or execution.get("judge_id") != result["judge_id"]
        or execution.get("independence_contract") != "fresh-zero-context"
        or execution.get("verdict") != result["verdict"]
        or execution.get("carrier")
        not in {"codex-cli-fresh-session", "opus-fresh-session"}
        or not str(execution.get("session_id") or "").strip()
    ):
        raise ContractError("judge execution_receipt bindings mismatch")
    if result["quality_status"] == "calibrated_equivalent":
        calibration, calibration_error = verified_evidence(
            result.get("calibration_receipt"),
            "technical-equivalence-judge-calibration@1.0.0",
        )
        if calibration_error:
            raise ContractError(
                f"calibrated judge lacks calibration receipt: {calibration_error}"
            )
        if (
            calibration.get("paired_cases", 0) < 40
            or calibration.get("blinded_batches", 0) < 2
            or calibration.get("exact_agreement", 0) < 0.90
            or calibration.get("cohen_kappa", 0) < 0.80
            or calibration.get("critical_false_pass") != 0
            or not calibration.get("human_adjudication_receipts")
        ):
            raise ContractError("judge calibration thresholds not met")
    expected = digest(result, "judge_result_digest")
    if result["judge_result_digest"] != expected:
        raise ContractError("judge result digest mismatch")
    return result


def artifact(path: str, content: str) -> dict[str, str]:
    return {
        "path": path,
        "encoding": "utf-8",
        "sha256": "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "content": content,
    }


def build_sync_bundle(
    request: dict[str, Any],
    target_peer: Path,
    target_head: str,
    verification: dict[str, Any],
    judge: dict[str, Any],
    run_dir: Path,
) -> Path:
    arena = ROOT.parents[1]
    source_head = git_head(arena)
    profile_bytes = PROFILE.read_bytes()
    assert_head_bound(arena, PROFILE.relative_to(arena), profile_bytes)
    profile = profile_bytes.decode("utf-8")
    prefix = ".skill-bindings/dr-research-loop/technical-equivalence"
    manifest = {
        "schema_version": "technical-equivalence-mirror-manifest@1.0.0",
        "canonical_owner": "bettor-arena/loop_wiki/evolve-technical-equivalence-research",
        "source_commit": source_head,
        "source_profile_sha256": "sha256:"
        + hashlib.sha256(profile.encode("utf-8")).hexdigest(),
        "request_digest": request["request_digest"],
        "verification_bundle_digest": verification["verification_bundle_digest"],
        "judge_result_digest": judge["judge_result_digest"],
        "judge_quality_status": judge["quality_status"],
        "target_binding": prefix,
    }
    manifest_text = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    ledger_text = (
        json.dumps(
            {
                "schema_version": "technical-equivalence-semantic-loss-ledger@1.0.0",
                "upstream_verification_bundle_digest": verification[
                    "verification_bundle_digest"
                ],
                "entries": verification["semantic_loss_ledger"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    readme = (
        "# Generated technical-equivalence binding\n\n"
        "Generated from bettor-arena. Do not hand-edit this directory. "
        "M1–M14 remain the skill-bettor monetization rubric; M12 composes PROFILE.md.\n"
    )
    artifacts = [
        artifact(f"{prefix}/README.md", readme),
        artifact(f"{prefix}/PROFILE.md", profile),
        artifact(f"{prefix}/source-manifest.json", manifest_text),
        artifact(f"{prefix}/semantic-loss-ledger.json", ledger_text),
    ]
    composition_path = target_peer / "loop_wiki/_template_dr/PROMPT.md"
    if not composition_path.is_file() or composition_path.is_symlink():
        raise ContractError(
            "target M12 composition owner is absent or not a regular file"
        )
    composition_before = composition_path.read_text(encoding="utf-8")
    pointer = f"{prefix}/PROFILE.md"
    composition_after = composition_before
    if pointer not in composition_before:
        lines = composition_before.splitlines(keepends=True)
        indexes = [
            index for index, line in enumerate(lines) if line.startswith("| M12 |")
        ]
        if len(indexes) != 1:
            raise ContractError("target M12 row is absent or ambiguous")
        index = indexes[0]
        newline = "\n" if lines[index].endswith("\n") else ""
        row = lines[index].rstrip("\n").rstrip()
        if not row.endswith("|"):
            raise ContractError("target M12 row is not a markdown table row")
        lines[index] = row[:-1].rstrip() + f"；profile={pointer} |" + newline
        composition_after = "".join(lines)
    composition_update = {
        "path": "loop_wiki/_template_dr/PROMPT.md",
        "encoding": "utf-8",
        "expected_sha256": "sha256:"
        + hashlib.sha256(composition_before.encode("utf-8")).hexdigest(),
        "sha256": "sha256:"
        + hashlib.sha256(composition_after.encode("utf-8")).hexdigest(),
        "content": composition_after,
    }
    bundle = {
        "schema_version": "technical-equivalence-sync-bundle@1.0.0",
        "status": "candidate_until_human_admit",
        "request_digest": request["request_digest"],
        "verification_bundle_digest": verification["verification_bundle_digest"],
        "judge_result_digest": judge["judge_result_digest"],
        "source_commit": source_head,
        "expected_target_head": target_head,
        "target_binding": prefix,
        "artifacts": artifacts,
        "composition_updates": [composition_update],
    }
    bundle["sync_bundle_digest"] = digest(bundle, "sync_bundle_digest")
    sync_key = judge["judge_result_digest"].split(":", 1)[1][:12]
    path = run_dir / f"sync-bundle.{sync_key}.json"
    write_immutable(path, bundle)
    return path


def execute_gemini_adapter(
    source_peer: Path,
    research: dict[str, Any],
    run_dir: Path,
) -> tuple[Path, Path]:
    source_peer = source_peer.resolve()
    source_head = git_head(source_peer)
    registry = load_json(ROOT / "adapter-registry.json")
    adapter_id = research["adapter_id"]
    declared = registry.get("adapters", {}).get(adapter_id)
    if (
        not isinstance(declared, dict)
        or declared.get("allowlisted_entry") != "automate.js"
    ):
        raise ContractError(f"adapter is not allowlisted: {adapter_id}")
    required = declared.get("required_files")
    if not isinstance(required, list) or not required:
        raise ContractError(f"adapter registry has no required files: {adapter_id}")
    source_files: dict[str, str] = {}
    for name in required:
        path = source_peer / str(name)
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"adapter required regular file absent: {path}")
        source_files[str(name)] = (
            "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        )
    pinned = declared.get("pinned_source")
    if not isinstance(pinned, dict):
        raise ContractError(f"adapter has no pinned source identity: {adapter_id}")
    if source_head != pinned.get("commit"):
        raise ContractError(
            f"adapter source commit drift: pinned {pinned.get('commit')}, got {source_head}; live revalidation required"
        )
    if source_files != pinned.get("files"):
        raise ContractError(
            "adapter source file digest drift; live revalidation required"
        )
    try:
        dependency_probe = subprocess.run(
            ["npm", "ls", "--depth=0", "--json"],
            cwd=source_peer,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError(
            f"adapter dependency probe could not execute: {exc}"
        ) from exc
    if dependency_probe.returncode != 0:
        raise ContractError(
            f"adapter dependency probe failed ({dependency_probe.returncode}); live revalidation required"
        )
    try:
        dependency_payload = json.loads(dependency_probe.stdout)
    except json.JSONDecodeError as exc:
        raise ContractError("adapter dependency probe returned invalid JSON") from exc
    actual_dependencies = {
        name: value.get("version")
        for name, value in dependency_payload.get("dependencies", {}).items()
        if isinstance(value, dict)
    }
    if actual_dependencies != pinned.get("top_level_dependencies"):
        raise ContractError(
            "adapter installed dependency versions drift; live revalidation required"
        )
    run_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = run_dir / "adapter-receipt.json"
    invocations: list[dict[str, Any]] = []
    gap_ledger: dict[str, Any] | None = None

    def invoke(label: str, prompt: str) -> str:
        prompt_path = run_dir / f"gemini-{label}-prompt.md"
        raw_path = run_dir / f"gemini-{label}-result.md"
        if prompt_path.exists() and prompt_path.read_text(encoding="utf-8") != prompt:
            raise ContractError(f"immutable prompt collision: {prompt_path}")
        prompt_path.write_text(prompt, encoding="utf-8")
        argv = [
            "node",
            str(source_peer / "automate.js"),
            "--dr-once",
            str(prompt_path),
            str(raw_path),
        ]
        try:
            completed = subprocess.run(
                argv,
                cwd=source_peer,
                text=True,
                capture_output=True,
                check=False,
                timeout=ADAPTER_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            invocations.append(
                {
                    "label": label,
                    "argv": argv,
                    "prompt_sha256": "sha256:"
                    + hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "output_sha256": None,
                    "raw_exit": 124,
                    "stdout_tail": str(exc.stdout or "")[-8000:],
                    "stderr_tail": f"adapter timeout after {ADAPTER_TIMEOUT_SECONDS}s",
                }
            )
            raise AdapterExit(124, receipt_path) from exc
        except OSError as exc:
            invocations.append(
                {
                    "label": label,
                    "argv": argv,
                    "prompt_sha256": "sha256:"
                    + hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "output_sha256": None,
                    "raw_exit": 64,
                    "stdout_tail": "",
                    "stderr_tail": f"adapter process could not execute: {exc}",
                }
            )
            raise ContractError(f"adapter process could not execute: {exc}") from exc
        raw = raw_path.read_text(encoding="utf-8") if raw_path.is_file() else ""
        invocations.append(
            {
                "label": label,
                "argv": argv,
                "prompt_sha256": "sha256:"
                + hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "output_sha256": (
                    "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
                    if raw
                    else None
                ),
                "raw_exit": completed.returncode,
                "structured_candidate_count": len(extract_structured_candidates(raw))
                if raw
                else 0,
                "stdout_tail": completed.stdout[-8000:],
                "stderr_tail": completed.stderr[-8000:],
            }
        )
        if completed.returncode != 0:
            raise AdapterExit(completed.returncode, receipt_path)
        return raw

    def write_receipt(status: str, failure: str | None = None) -> dict[str, Any]:
        receipt: dict[str, Any] = {
            "schema_version": "technical-equivalence-adapter-receipt@1.0.0",
            "adapter_id": adapter_id,
            "source_peer": str(source_peer),
            "source_commit": source_head,
            "source_files": source_files,
            "top_level_dependencies": actual_dependencies,
            "research_request_digest": research["research_request_digest"],
            "status": status,
            "gap_ledger": gap_ledger,
            "invocations": invocations,
        }
        if failure:
            receipt["failure"] = failure
        receipt["adapter_receipt_digest"] = digest(receipt, "adapter_receipt_digest")
        write_immutable(receipt_path, receipt)
        return receipt

    try:
        reports, candidates, gap_ledger = collect_live_research(
            research["prompt"], invoke
        )
    except AdapterExit as exc:
        write_receipt("failed", str(exc))
        raise
    except VerificationFailure as exc:
        write_receipt("failed", str(exc))
        raise VerificationFailure(f"{exc}; receipt={receipt_path}") from exc
    except ContractError as exc:
        write_receipt("failed", str(exc))
        raise

    receipt = write_receipt("passed")
    combined = "\n\n".join(f"<!-- {label} -->\n{report}" for label, report in reports)
    result = {
        "schema_version": "technical-equivalence-research-result@1.0.0",
        "upstream_research_request_digest": research["research_request_digest"],
        "provider": "gemini-deep-research",
        "adapter_receipt_digest": receipt["adapter_receipt_digest"],
        "raw_markdown": combined,
        "gap_ledger": gap_ledger,
        "candidates": candidates,
    }
    result["research_result_digest"] = digest(result, "research_result_digest")
    result_path = run_dir / "research-result.json"
    write_immutable(result_path, result)
    return result_path, receipt_path


def run(args: argparse.Namespace) -> int:
    request = load_json(args.request.resolve())
    validate_request(request)
    target = args.target_peer.resolve()
    target_head = git_head(target)
    if (
        request["target_binding"]
        != ".skill-bindings/dr-research-loop/technical-equivalence"
    ):
        raise ContractError("target_binding is outside the admitted mirror path")
    if args.execute_gemini and args.research_result:
        raise ContractError(
            "--execute-gemini and --research-result are mutually exclusive"
        )
    if args.execute_gemini and args.source_peer is None:
        raise ContractError("--execute-gemini requires --source-peer")

    run_root = Path(os.environ.get("EQUIVALENCE_RUN_ROOT", ROOT / "_runs")).resolve()
    run_dir = (
        run_root
        / request["request_id"]
        / request["request_digest"].split(":", 1)[1][:12]
    )
    prompt = build_prompt(request)
    research = {
        "schema_version": "technical-equivalence-research-request@1.0.0",
        "request_id": request["request_id"],
        "upstream_request_digest": request["request_digest"],
        "provider": "gemini-deep-research",
        "adapter_id": "antigravity-dr-once-v1",
        "max_gap_topics": 6,
        "prompt": prompt,
        "prompt_digest": "sha256:" + hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    }
    research["research_request_digest"] = digest(research, "research_request_digest")
    research_path = run_dir / "research-request.json"
    write_immutable(research_path, research)

    state = "research_required"
    route_exit = 0
    artifacts = {"research_request": str(research_path)}
    next_edge = "provide_research_result_or_execute_gemini"
    result_path = args.research_result.resolve() if args.research_result else None
    if args.execute_gemini:
        result_path, adapter_receipt = execute_gemini_adapter(
            args.source_peer, research, run_dir
        )
        artifacts["adapter_receipt"] = str(adapter_receipt)
    if result_path:
        verification, result_artifacts = process_result(result_path, research, run_dir)
        artifacts["research_result"] = str(result_path)
        artifacts.update(result_artifacts)
        if "expected_judge_result" not in result_artifacts:
            state = "candidate_ready"
            next_edge = "audit_probe_and_if_required_rebuild_then_supply_enriched_research_result"
        else:
            state = "judge_required"
            next_edge = "fresh_zero_context_judge_then_rerun"
        judge_result_path = (
            Path(result_artifacts["expected_judge_result"])
            if "expected_judge_result" in result_artifacts
            else None
        )
        if judge_result_path is not None and judge_result_path.is_file():
            judge_packet = load_json(Path(result_artifacts["judge_packet"]))
            judge = validate_judge_result(
                judge_result_path,
                verification["verification_bundle_digest"],
                judge_packet["judge_packet_digest"],
            )
            artifacts["judge_result"] = str(judge_result_path)
            if judge["verdict"] == "FAIL":
                state = "verification_failed"
                next_edge = "repair_findings_and_reverify"
                route_exit = 2
            else:
                sync_path = build_sync_bundle(
                    request, target, target_head, verification, judge, run_dir
                )
                artifacts["sync_bundle"] = str(sync_path)
                state = "human_required"
                next_edge = "external_human_admit_then_target_side_apply"

    route = {
        "schema_version": "technical-equivalence-route-result@1.0.0",
        "request_id": request["request_id"],
        "request_digest": request["request_digest"],
        "state": state,
        "target_peer": str(target),
        "expected_target_head": target_head,
        "artifacts": artifacts,
        "next_edge": next_edge,
        "exit_semantics": "0=valid state;2=declared verification failure;64=contract/tool failure",
    }
    route["route_result_digest"] = digest(route, "route_result_digest")
    route_path = run_dir / f"route-result.{state.replace('_', '-')}.json"
    write_immutable(route_path, route)
    print(f"PASS: route_result={route_path}")
    return route_exit


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    sub = value.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("--request", type=Path, required=True)
    run_p.add_argument("--target-peer", type=Path, required=True)
    run_p.add_argument("--source-peer", type=Path)
    run_p.add_argument("--research-result", type=Path)
    run_p.add_argument("--execute-gemini", action="store_true")
    return value


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "run":
            return run(args)
        raise ContractError(f"unsupported command: {args.command}")
    except AdapterExit as exc:
        print(f"equivalence adapter failure: {exc}", file=sys.stderr)
        return exc.code
    except VerificationFailure as exc:
        print(f"equivalence FAIL: {exc}", file=sys.stderr)
        return 2
    except ContractError as exc:
        print(f"equivalence FATAL: {exc}", file=sys.stderr)
        return 64
    except OSError as exc:
        print(f"equivalence FATAL: operating-system error: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
