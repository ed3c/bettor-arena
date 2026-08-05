import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { LocalContext } from "./contracts";

function json(path: string): Record<string, unknown> {
  return JSON.parse(readFileSync(path, "utf8"));
}

function jsonl(path: string): Array<Record<string, unknown>> {
  const text = readFileSync(path, "utf8").trim();
  return text ? text.split("\n").map((line) => JSON.parse(line)) : [];
}

export function loadLocalContext(root: string, task: string): LocalContext {
  if (task.trim().length < 8) throw new Error("task must contain at least 8 characters");
  return {
    root,
    task: task.trim(),
    source: json(join(root, "data/source.json")),
    evidence: jsonl(join(root, "data/evidence.jsonl")),
    claims: jsonl(join(root, "data/claims.jsonl")),
    unknowns: JSON.parse(readFileSync(join(root, "data/unknowns.json"), "utf8")),
    decisions: jsonl(join(root, "data/decisions.jsonl")),
  };
}
