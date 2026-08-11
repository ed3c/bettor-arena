import { createHash, randomUUID } from "node:crypto";
import { chmodSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { spawnSync } from "node:child_process";

export type EvidenceState = "PASS" | "FAIL" | "ABSENT" | "NOT_EXERCISED" | "NOT_IMPLEMENTED";
export const SHA40 = /^[0-9a-f]{40}$/;
export const SHA64 = /^[0-9a-f]{64}$/;
export const ID = /^[a-z0-9][a-z0-9._-]*$/;

export class EnvironmentContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EnvironmentContractError";
  }
}

export function canonical(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  const record = value as Record<string, unknown>;
  return `{${Object.keys(record)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonical(record[key])}`)
    .join(",")}}`;
}

export function sha256Bytes(value: Buffer | string): string {
  return createHash("sha256").update(value).digest("hex");
}

export function sha256Json(value: unknown): string {
  return sha256Bytes(canonical(value));
}

export function withDigest<T extends Record<string, unknown>>(value: T): T & { content_sha256: string } {
  const unsigned = { ...value } as Record<string, unknown>;
  delete unsigned.content_sha256;
  return { ...value, content_sha256: sha256Json(unsigned) } as T & { content_sha256: string };
}

export function verifyDigest(value: Record<string, unknown>, label: string): void {
  const claimed = value.content_sha256;
  const unsigned = { ...value };
  delete unsigned.content_sha256;
  if (typeof claimed !== "string" || claimed !== sha256Json(unsigned)) {
    throw new EnvironmentContractError(`${label}: content_sha256 mismatch`);
  }
}

export function readJson<T = Record<string, unknown>>(path: string): T {
  try {
    const value = JSON.parse(readFileSync(path, "utf8"));
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new EnvironmentContractError(`${path}: JSON root must be an object`);
    }
    return value as T;
  } catch (error) {
    if (error instanceof EnvironmentContractError) throw error;
    throw new EnvironmentContractError(`${path}: unreadable JSON: ${String(error)}`);
  }
}

export function writeJson(path: string, value: unknown): void {
  mkdirSync(dirname(path), { recursive: true });
  const temp = `${path}.tmp-${process.pid}-${randomUUID()}`;
  writeFileSync(temp, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o644 });
  chmodSync(temp, 0o644);
  renameSync(temp, path);
}

export function run(command: string, args: string[], options: { cwd?: string; allow?: number[]; env?: NodeJS.ProcessEnv } = {}): string {
  const processResult = spawnSync(command, args, {
    cwd: options.cwd,
    env: options.env ?? process.env,
    encoding: "utf8",
    maxBuffer: 16 * 1024 * 1024,
  });
  const code = processResult.status ?? 64;
  if (!(options.allow ?? [0]).includes(code)) {
    throw new EnvironmentContractError((processResult.stderr || processResult.stdout || `${command} failed`).trim());
  }
  return (processResult.stdout || "").trim();
}

export function runGit(root: string, args: string[], allow = [0]): string {
  return run("git", ["-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", root, ...args], { allow });
}

export function closedObject(value: unknown, fields: string[], label: string): asserts value is Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new EnvironmentContractError(`${label}: object required`);
  }
  const actual = Object.keys(value as Record<string, unknown>).sort();
  const expected = [...fields].sort();
  if (canonical(actual) !== canonical(expected)) {
    throw new EnvironmentContractError(`${label}: fields drifted`);
  }
}

export function uniqueStrings(value: unknown, label: string): string[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string") || new Set(value).size !== value.length) {
    throw new EnvironmentContractError(`${label}: unique string array required`);
  }
  return value as string[];
}
