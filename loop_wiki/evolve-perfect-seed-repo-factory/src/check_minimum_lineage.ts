#!/usr/bin/env bun
import { isAbsolute } from "node:path";
import { verifyMinimumLineage } from "./minimum_lineage";

function repoPath(args: string[]): string {
  const index = args.indexOf("--repo");
  const value = index >= 0 ? args[index + 1] : undefined;
  if (!value || !isAbsolute(value)) {
    throw new Error("usage: check_minimum_lineage.ts --repo <absolute-path>");
  }
  return value;
}

try {
  const result = verifyMinimumLineage(repoPath(Bun.argv.slice(2)));
  console.log(
    JSON.stringify({ schema_version: "perfect-seed-minimum-lineage-result@1.0.0", status: "passed", ...result }),
  );
} catch (error) {
  console.error(`FAIL: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 2;
}
