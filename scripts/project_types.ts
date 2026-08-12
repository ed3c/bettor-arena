import { spawnSync } from "node:child_process";
import {
  chmodSync,
  existsSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  realpathSync,
  renameSync,
  writeFileSync,
} from "node:fs";
import { createHash, randomUUID } from "node:crypto";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";

export const REQUIREMENTS_SCHEMA = "bettor-arena/project-requirements/v1";
export const PLAN_SCHEMA = "bettor-arena/project-plan/v1";
export const LOCK_SCHEMA = "bettor-arena/consumer-lock/v1";
export const MANAGED_SCHEMA = "bettor-arena/project-managed/v1";
export const RECEIPT_SCHEMA = "bettor-arena/project-apply-receipt/v1";
export const MANAGED_PATH = ".arena/managed.json";
export const RECEIPT_DIR = ".arena/receipts";
export const EMBEDDED_PATH = ".arena/vendor/bettor";
export const SHA40 = /^[0-9a-f]{40}$/;
export const ID = /^[a-z0-9][a-z0-9._-]*$/;

export interface ModuleSelection {
  id: string;
  components: string[];
}
export interface ProjectRequirements {
  schema: typeof REQUIREMENTS_SCHEMA;
  id: string;
  mode: "remote-consumer" | "embedded-core";
  release: { repository: string; commit: string };
  preset: string | null;
  modules: ModuleSelection[];
}
export interface ModuleManifest {
  schema: "bettor-arena/module/v1";
  id: string;
  interface_version: string;
  summary: string;
  roots: string[];
  components: Record<string, { required: boolean; paths: string[] }>;
  provides: string[];
  requires: string[];
  conflicts: string[];
  skills: { required: string[]; optional: string[]; repo_owned: string[] };
  external_policy: { exposed: boolean; mutation: string; network: string; secrets: string };
}
export interface ResolvedComposition {
  modules: Array<{
    id: string;
    interface_version: string;
    manifest_sha256: string;
    components: string[];
    provides: string[];
    roots: string[];
  }>;
  capabilities: Record<string, string>;
}
export interface ManagedFilePlan {
  path: string;
  action: "write" | "delete";
  mode: number | null;
  before_sha256: string | null;
  before_base64: string | null;
  after_sha256: string | null;
  after_base64: string | null;
}
export interface ProjectPlan {
  schema: typeof PLAN_SCHEMA;
  project: string;
  mode: ProjectRequirements["mode"];
  release: ProjectRequirements["release"] & { tree: string };
  requirements_sha256: string;
  target_head: string | null;
  previous_managed_sha256: string | null;
  previous_managed_base64: string | null;
  consumer_lock_sha256: string;
  files: ManagedFilePlan[];
  embedded: { path: typeof EMBEDDED_PATH; commit: string } | null;
  content_sha256: string;
}
export interface ManagedManifest {
  schema: typeof MANAGED_SCHEMA;
  project: string;
  mode: ProjectRequirements["mode"];
  plan_sha256: string;
  source: { repository: string; commit: string; tree: string };
  paths: Array<{ path: string; sha256: string; mode: number }>;
  embedded: { path: typeof EMBEDDED_PATH; commit: string } | null;
  content_sha256: string;
}
export interface ApplyReceipt {
  schema: typeof RECEIPT_SCHEMA;
  project: string;
  mode: ProjectRequirements["mode"];
  plan_sha256: string;
  files: ManagedFilePlan[];
  managed_before_sha256: string | null;
  managed_before_base64: string | null;
  managed_after_sha256: string;
  managed_after_base64: string;
  embedded_created: { path: typeof EMBEDDED_PATH; commit: string } | null;
  content_sha256: string;
}

export class ProjectError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ProjectError";
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
  if (typeof claimed !== "string" || claimed !== sha256Json(unsigned))
    throw new ProjectError(`${label}: content_sha256 mismatch`);
}
export function readJson<T = Record<string, unknown>>(path: string): T {
  try {
    const parsed = JSON.parse(readFileSync(path, "utf8"));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed))
      throw new ProjectError(`${path}: JSON root must be an object`);
    return parsed as T;
  } catch (error) {
    if (error instanceof ProjectError) throw error;
    throw new ProjectError(`${path}: unreadable JSON: ${String(error)}`);
  }
}
export function atomicWrite(path: string, content: Buffer, mode: number): void {
  mkdirSync(dirname(path), { recursive: true });
  const temp = `${path}.tmp-${process.pid}-${randomUUID()}`;
  writeFileSync(temp, content, { mode });
  chmodSync(temp, mode);
  renameSync(temp, path);
}
export function writeJson(path: string, value: unknown): void {
  atomicWrite(path, Buffer.from(`${JSON.stringify(value, null, 2)}\n`), 0o644);
}
export function runGit(root: string, args: string[], allow = new Set([0])): string {
  const result = spawnSync(
    "git",
    ["-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", root, ...args],
    {
      encoding: "utf8",
      maxBuffer: 8 * 1024 * 1024,
    },
  );
  const code = result.status ?? 64;
  if (!allow.has(code))
    throw new ProjectError((result.stderr || result.stdout || `git ${args.join(" ")} failed`).trim());
  return (result.stdout || "").trim();
}
export function ensureGitRepository(root: string): void {
  const actual = runGit(root, ["rev-parse", "--show-toplevel"]);
  if (realpathSync(actual) !== realpathSync(root)) {
    throw new ProjectError(`target must be the Git repository root: ${root}`);
  }
}
export function gitHeadOrNull(root: string): string | null {
  const result = spawnSync(
    "git",
    ["-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-C", root, "rev-parse", "HEAD"],
    { encoding: "utf8" },
  );
  return result.status === 0 ? result.stdout.trim() : null;
}
export function gitTree(root: string, commit: string): string {
  return runGit(root, ["rev-parse", `${commit}^{tree}`]);
}
export function requireCommit(root: string, commit: string): void {
  if (!SHA40.test(commit)) throw new ProjectError(`release.commit must be exactly 40 lowercase hex: ${commit}`);
  runGit(root, ["cat-file", "-e", `${commit}^{commit}`]);
}
export function normalizeManagedPath(value: string): string {
  if (!value || isAbsolute(value)) throw new ProjectError(`managed path must be target-relative: ${value}`);
  const normalized = value.replaceAll("\\", "/").replace(/^\.\//, "").replace(/\/$/, "");
  if (!normalized || normalized === "." || normalized.split("/").some((part) => !part || part === "..")) {
    throw new ProjectError(`managed path escapes project root: ${value}`);
  }
  return normalized;
}
export function targetPath(target: string, managedPath: string): string {
  const absolute = resolve(target, normalizeManagedPath(managedPath));
  const rel = relative(resolve(target), absolute);
  if (rel.startsWith(`..${sep}`) || rel === ".." || isAbsolute(rel))
    throw new ProjectError(`managed path escapes target: ${managedPath}`);
  return absolute;
}
export function currentBytes(path: string): Buffer | null {
  if (!existsSync(path)) return null;
  const info = lstatSync(path);
  if (info.isSymbolicLink()) throw new ProjectError(`managed projection may not be a symlink: ${path}`);
  if (!info.isFile()) throw new ProjectError(`managed projection is not a regular file: ${path}`);
  return readFileSync(path);
}
export function shaOrNull(value: Buffer | null): string | null {
  return value ? sha256Bytes(value) : null;
}
export function toBase64(value: Buffer | null): string | null {
  return value ? value.toString("base64") : null;
}
export function fromBase64(value: string | null): Buffer | null {
  return value === null ? null : Buffer.from(value, "base64");
}
export function assertClosedObject(
  value: unknown,
  fields: string[],
  label: string,
): asserts value is Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new ProjectError(`${label}: object required`);
  if (canonical(Object.keys(value as Record<string, unknown>).sort()) !== canonical([...fields].sort()))
    throw new ProjectError(`${label}: fields drifted`);
}
export function stringArray(value: unknown, label: string): string[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string") || new Set(value).size !== value.length) {
    throw new ProjectError(`${label}: unique string array required`);
  }
  return value as string[];
}
export function validateRequirements(value: unknown, label = "project requirements"): ProjectRequirements {
  assertClosedObject(value, ["schema", "id", "mode", "release", "preset", "modules"], label);
  if (value.schema !== REQUIREMENTS_SCHEMA) throw new ProjectError(`${label}: schema must be ${REQUIREMENTS_SCHEMA}`);
  if (typeof value.id !== "string" || !ID.test(value.id)) throw new ProjectError(`${label}: invalid project id`);
  if (value.mode !== "remote-consumer" && value.mode !== "embedded-core")
    throw new ProjectError(`${label}: unsupported mode`);
  assertClosedObject(value.release, ["repository", "commit"], `${label}.release`);
  if (typeof value.release.repository !== "string" || !value.release.repository.trim())
    throw new ProjectError(`${label}: release.repository is required`);
  const repository = value.release.repository;
  if (
    isAbsolute(repository) ||
    repository.startsWith("~/") ||
    repository.startsWith("file://") ||
    repository.includes("/Use" + "rs/")
  ) {
    throw new ProjectError(`${label}: release.repository must be a portable Git remote identity`);
  }
  if (typeof value.release.commit !== "string" || !SHA40.test(value.release.commit))
    throw new ProjectError(`${label}: release.commit must be exactly 40 lowercase hex`);
  if (value.preset !== null && (typeof value.preset !== "string" || !ID.test(value.preset)))
    throw new ProjectError(`${label}: invalid preset`);
  if (!Array.isArray(value.modules)) throw new ProjectError(`${label}: modules must be an array`);
  const seen = new Set<string>();
  const modules = value.modules.map((entry, index) => {
    assertClosedObject(entry, ["id", "components"], `${label}.modules[${index}]`);
    if (typeof entry.id !== "string" || !ID.test(entry.id) || seen.has(entry.id))
      throw new ProjectError(`${label}: invalid or duplicate module ${String(entry.id)}`);
    seen.add(entry.id);
    return { id: entry.id, components: stringArray(entry.components, `${label}:${entry.id}.components`) };
  });
  return {
    schema: REQUIREMENTS_SCHEMA,
    id: value.id,
    mode: value.mode,
    release: { repository, commit: value.release.commit },
    preset: value.preset,
    modules,
  };
}
