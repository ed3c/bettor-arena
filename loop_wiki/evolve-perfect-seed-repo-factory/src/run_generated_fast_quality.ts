#!/usr/bin/env bun
import { existsSync, symlinkSync, unlinkSync } from "node:fs";
import { isAbsolute, join, resolve } from "node:path";

const ROOT = resolve(import.meta.dir, "..");

function repoPath(args: string[]): string {
  const index = args.indexOf("--repo");
  const value = index >= 0 ? args[index + 1] : undefined;
  if (!value || !isAbsolute(value)) throw new Error("usage: run_generated_fast_quality.ts --repo <absolute-path>");
  return value;
}

let localModules: string | undefined;
let createdLocalModules = false;
try {
  const repo = repoPath(Bun.argv.slice(2));
  const factoryModules = join(ROOT, "node_modules");
  localModules = join(repo, "node_modules");
  if (!existsSync(factoryModules)) throw new Error("factory node_modules missing; run bun install --frozen-lockfile");
  if (existsSync(localModules)) throw new Error("generated repo node_modules must be absent before local fast gate");
  symlinkSync(factoryModules, localModules, "dir");
  createdLocalModules = true;
  const result = Bun.spawnSync(["bun", "run", "quality:fast"], { cwd: repo, stdout: "pipe", stderr: "pipe" });
  process.stdout.write(result.stdout);
  process.stderr.write(result.stderr);
  if (result.exitCode !== 0) process.exitCode = 2;
} catch (error) {
  console.error(`FAIL: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 64;
} finally {
  if (createdLocalModules && localModules && existsSync(localModules)) unlinkSync(localModules);
}
