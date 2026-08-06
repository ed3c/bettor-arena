import { appendFileSync } from "node:fs";
import { isAbsolute } from "node:path";
import { computeStats } from "./stats";

const args = Bun.argv.slice(2);
const outputIndex = args.indexOf("--output");
const output = outputIndex >= 0 ? args[outputIndex + 1] : undefined;
if (!output) throw new Error("usage: record_trend.ts --output <absolute-jsonl-path>");
if (!isAbsolute(output)) throw new Error("trend output must be absolute");
// Ask git from where this factory actually sits, not from an assumed grandparent. The old
// `../../..` encoded "the loop is always two levels under a repo root", which is false the
// moment the factory is extracted anywhere else -- it would then record an unrelated repo's
// HEAD, or a stale one, instead of failing honestly. Outside any repository git exits
// nonzero and the N/A branch below records that as an explicit absence.
const head = Bun.spawnSync(["git", "rev-parse", "HEAD"], {
  cwd: import.meta.dir,
  stdout: "pipe",
  stderr: "pipe",
});
const commit = head.exitCode === 0 ? head.stdout.toString().trim() : "N/A-no-git-head";
appendFileSync(
  output,
  `${JSON.stringify({ schema_version: "perfect-seed-trend@1.0.0", commit, stats: computeStats() })}\n`,
  "utf8",
);
console.log("PASS: perfect-seed trend recorded");
