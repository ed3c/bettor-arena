#!/usr/bin/env python3
"""Schema-conformant corrections applied after the one-shot migration."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

module_path = ROOT / ".arena/modules/agent-runtime-integration/module.json"
module = json.loads(module_path.read_text(encoding="utf-8"))
for loop in module["loops"]:
    if loop["id"] == "skill-execution":
        loop["class"] = "aggregate"
        loop["external_policy"] = "control-only"
        break
else:
    raise SystemExit("skill-execution loop was not generated")
module_path.write_text(json.dumps(module, indent=2) + "\n", encoding="utf-8")

composition_path = ROOT / ".arena/compositions/bettor-arena.requirements.json"
composition = json.loads(composition_path.read_text(encoding="utf-8"))
for requirement in composition["modules"]:
    if requirement["id"] == "agent-runtime-integration":
        components = set(requirement["components"])
        components.add("portable_skill_execution")
        requirement["components"] = sorted(components)
        break
else:
    raise SystemExit("agent-runtime-integration composition requirement is absent")
composition_path.write_text(
    json.dumps(composition, indent=2) + "\n",
    encoding="utf-8",
)
print("skill-execution module and composition: schema-conformant")
