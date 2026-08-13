#!/usr/bin/env python3
"""Schema-conformant correction applied after the one-shot surface migration."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / ".arena/modules/agent-runtime-integration/module.json"
module = json.loads(PATH.read_text(encoding="utf-8"))
for loop in module["loops"]:
    if loop["id"] == "skill-execution":
        loop["class"] = "aggregate"
        loop["external_policy"] = "control-only"
        break
else:
    raise SystemExit("skill-execution loop was not generated")
PATH.write_text(json.dumps(module, indent=2) + "\n", encoding="utf-8")
print("skill-execution module enums: schema-conformant")
