import { existsSync, readFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import { assertSourceRefs, refsShapeStatus } from "./contracts";
import { verifyMinimumLineage } from "./minimum_lineage";

const args = Bun.argv.slice(2);
const repoIndex = args.indexOf("--repo");
const root = repoIndex >= 0 ? args[repoIndex + 1] : undefined;
if (!root || !isAbsolute(root)) throw new Error("usage: verify_generated_repo.ts --repo <absolute-path>");
verifyMinimumLineage(root);
const required = [
  "AGENTS.md",
  ".agents/skills/seed-repo-operator/SKILL.md",
  "data/source.json",
  "data/evidence.jsonl",
  "data/claims.jsonl",
  "data/unknowns.json",
  "data/decisions.jsonl",
  "data/lineage.json",
  "data/artifact-manifest.json",
  "data/build-receipt.json",
  "data/call-plan.json",
  "data/call-results.jsonl",
  "scripts/plan.ts",
];
for (const path of required) if (!existsSync(join(root, path))) throw new Error(`generated repo missing: ${path}`);
const source = JSON.parse(readFileSync(join(root, "data/source.json"), "utf8"));
const lineage = JSON.parse(readFileSync(join(root, "data/lineage.json"), "utf8"));
if (source.human_gate !== "required_before_seed_admit" || lineage.terminal_human_gate !== "required_before_seed_admit")
  throw new Error("generated repo lost human admit gate");
assertSourceRefs(lineage.source_refs);
assertSourceRefs(source.source_refs);
if (JSON.stringify(source.source_refs) !== JSON.stringify(lineage.source_refs))
  throw new Error("generated repo source.json and lineage.json source_refs diverge");
if (source.refs_status !== lineage.refs_status)
  throw new Error("generated repo source.json and lineage.json refs_status diverge");
const shape = refsShapeStatus(lineage.source_refs);
const statusConsistent =
  shape === "sentinel"
    ? lineage.refs_status === "sentinel"
    : ["declared", "resolved", "stale"].includes(lineage.refs_status);
if (!statusConsistent) throw new Error("generated repo lineage refs_status does not match source_refs");
const plan = JSON.parse(readFileSync(join(root, "data/call-plan.json"), "utf8"));
const results = readFileSync(join(root, "data/call-results.jsonl"), "utf8")
  .trim()
  .split("\n")
  .map((line) => JSON.parse(line));
if (!Array.isArray(plan.calls) || plan.calls.length !== 20 || results.length !== 20)
  throw new Error("generated repo must contain exactly 20 call records");
const taskSha256 = new Bun.CryptoHasher("sha256").update(String(plan.task)).digest("hex");
if (plan.task_sha256 !== taskSha256) throw new Error("call plan task hash drift");
if (new Set(plan.calls.map((entry: { call_id: string }) => entry.call_id)).size !== 20)
  throw new Error("duplicate call ids");
for (const [index, call] of plan.calls.entries()) {
  for (const dependency of call.depends_on) {
    const dependencyIndex = plan.calls.findIndex((entry: { call_id: string }) => entry.call_id === dependency);
    if (dependencyIndex < 0 || dependencyIndex >= index)
      throw new Error(`invalid dependency order: ${call.call_id} -> ${dependency}`);
  }
}
for (const result of results) {
  const outputSha256 = new Bun.CryptoHasher("sha256").update(JSON.stringify(result.output)).digest("hex");
  if (result.output_sha256 !== outputSha256) throw new Error(`result output hash drift: ${String(result.call_id)}`);
}
const final = results.at(-1);
if (final?.call_id !== "F20" || final.output?.admit_edge !== "human_required")
  throw new Error("final call must surface human_required");
console.log("PASS: generated perfect-seed candidate repo");
