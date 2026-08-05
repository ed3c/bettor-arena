import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { SOURCE_KINDS } from "./contracts";

const ROOT = resolve(import.meta.dir, "..");

function countFiles(directory: string): number {
  return readdirSync(directory, { withFileTypes: true }).reduce(
    (total, entry) =>
      total +
      (entry.isDirectory() && entry.name !== "node_modules"
        ? countFiles(join(directory, entry.name))
        : entry.isFile()
          ? 1
          : 0),
    0,
  );
}

export function computeStats() {
  return {
    schema_version: "perfect-seed-stats@1.0.0",
    source_kinds: SOURCE_KINDS.length,
    reasoning_functions: 20,
    reduced_ir_kinds: 9,
    template_files: countFiles(join(ROOT, "templates", "repo")),
    state_nodes: 7,
  };
}

const args = Bun.argv.slice(2);
if (import.meta.main) {
  const current = computeStats();
  if (args.includes("--check")) {
    const baselinePath = join(ROOT, "baselines", "seed-stats.json");
    if (!existsSync(baselinePath)) throw new Error(`baseline missing: ${baselinePath}`);
    const baseline = JSON.parse(readFileSync(baselinePath, "utf8"));
    if (JSON.stringify(current) !== JSON.stringify(baseline)) {
      console.error(`FAIL: seed stats drift\nexpected=${JSON.stringify(baseline)}\nactual=${JSON.stringify(current)}`);
      process.exit(1);
    }
    console.log("PASS: perfect-seed stats baseline");
  } else {
    console.log(JSON.stringify(current, null, 2));
  }
}
