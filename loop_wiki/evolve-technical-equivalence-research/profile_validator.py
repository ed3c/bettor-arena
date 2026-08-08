#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROFILE = ROOT / "profile" / "technical-equivalence.md"

REQUIRED = [
    "P1 部署拓撲",
    "P2 規模",
    "P3 延遲與 SLO",
    "P4 故障模式與回滾",
    "P5 成本與運算開銷",
    "P6 工具鏈與框架",
    "P7 資料流與儲存",
    "P8 安全與權限邊界",
    "P9 可觀測性",
    "V1 核心主張與底層機制",
    "V2 前提假設與適用邊界",
    "V3 反例／失敗模式",
    "V4 與競品／替代方案對比",
    "V5 實證／數據佐證",
    "技術實現等價物（必做）",
    "每一缺口都要給技術實現等價物",
    "最多六題",
    "candidate",
    "technical_equivalent",
    "[推論]",
]
STAGES = ["1. 敘事脈絡理解", "2. 量規覆蓋稽核與缺口", "3. Path B", "4. 已充足整理"]


def validate(text: str) -> list[str]:
    errors = [
        f"missing required profile clause: {item}"
        for item in REQUIRED
        if item not in text
    ]
    positions = [text.find(stage) for stage in STAGES]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        errors.append("Path B stages are absent or out of order")
    return errors


def main() -> int:
    if sys.argv[1:] == ["--selftest"]:
        good = PROFILE.read_text(encoding="utf-8")
        if validate(good):
            print("SELFTEST RED: canonical profile invalid", file=sys.stderr)
            return 2
        missing = good.replace("技術實現等價物（必做）", "removed", 1)
        swapped = (
            good.replace(STAGES[0], "SWAP")
            .replace(STAGES[1], STAGES[0])
            .replace("SWAP", STAGES[1])
        )
        if not validate(missing) or not validate(swapped):
            print("SELFTEST RED: planted prompt defects escaped", file=sys.stderr)
            return 2
        for schema in sorted((ROOT / "schemas").glob("*.json")):
            json.loads(schema.read_text(encoding="utf-8"))
        print(
            "SELFTEST GREEN: profile good; missing-clause and stage-swap controls red"
        )
        return 0
    errors = validate(PROFILE.read_text(encoding="utf-8"))
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
