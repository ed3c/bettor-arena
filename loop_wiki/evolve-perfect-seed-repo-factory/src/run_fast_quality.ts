#!/usr/bin/env bun
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, join, resolve } from "node:path";

type StageStatus = "passed" | "failed" | "not_run";

type StageResult = {
  id: "minimum-lineage" | "format" | "lint" | "typecheck";
  command: string[];
  status: StageStatus;
  exit_code: number | null;
  elapsed_ms: number | null;
  stdout_tail: string;
  stderr_tail: string;
};

const ROOT = resolve(import.meta.dir, "..");
const GATE_INPUTS = [
  "package.json",
  "bun.lock",
  "eslint.config.mjs",
  "prettier.config.mjs",
  "tsconfig.json",
  "templates/template-metadata.json",
] as const;
const STAGES: Array<{ id: StageResult["id"]; command: string[] }> = [
  { id: "minimum-lineage", command: ["bun", "run", "src/check_factory_minimum_lineage.ts"] },
  { id: "format", command: ["./node_modules/.bin/prettier", ".", "--check"] },
  { id: "lint", command: ["./node_modules/.bin/eslint", "."] },
  { id: "typecheck", command: ["./node_modules/.bin/tsc", "--project", "tsconfig.json", "--noEmit"] },
];

function sha256(value: string | Uint8Array): string {
  return new Bun.CryptoHasher("sha256").update(value).digest("hex");
}

function outputPath(args: string[]): string {
  if (args.length === 0) {
    return join(ROOT, "_engine-run", `fast-quality.${Date.now()}.${process.pid}.receipt.json`);
  }
  const index = args.indexOf("--output");
  const value = index >= 0 ? args[index + 1] : undefined;
  if (!value || !isAbsolute(value)) throw new Error("usage: run_fast_quality.ts [--output <absolute-path>]");
  return value;
}

function tail(value: Uint8Array): string {
  return Buffer.from(value).toString("utf8").slice(-4000);
}

function runStage(id: StageResult["id"], command: string[]): StageResult {
  const started = performance.now();
  const result = Bun.spawnSync(command, { cwd: ROOT, stdout: "pipe", stderr: "pipe" });
  return {
    id,
    command,
    status: result.exitCode === 0 ? "passed" : "failed",
    exit_code: result.exitCode,
    elapsed_ms: Math.max(0, Math.round(performance.now() - started)),
    stdout_tail: tail(result.stdout),
    stderr_tail: tail(result.stderr),
  };
}

function notRun(id: StageResult["id"], command: string[]): StageResult {
  return { id, command, status: "not_run", exit_code: null, elapsed_ms: null, stdout_tail: "", stderr_tail: "" };
}

try {
  const output = outputPath(Bun.argv.slice(2));
  const started = performance.now();
  const stages: StageResult[] = [];
  let blocked = false;
  for (const stage of STAGES) {
    const result: StageResult = blocked ? notRun(stage.id, stage.command) : runStage(stage.id, stage.command);
    stages.push(result);
    blocked ||= result.status === "failed";
  }
  const receipt = {
    schema_version: "perfect-seed-fast-quality-receipt@1.0.0",
    status: blocked ? "failed" : "passed",
    claim_boundary: "preflight-only-not-code-quality-axis",
    network_called: false,
    elapsed_ms: Math.max(0, Math.round(performance.now() - started)),
    measured_at: new Date().toISOString(),
    gate_inputs: GATE_INPUTS.map((path) => ({ path, sha256: sha256(readFileSync(join(ROOT, path))) })),
    stages,
  };
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, `${JSON.stringify(receipt, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
  console.log(JSON.stringify({ status: receipt.status, receipt: output }));
  if (blocked) process.exitCode = 2;
} catch (error) {
  console.error(`FAIL: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 64;
}
