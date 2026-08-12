import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import {
  EMBEDDED_PATH,
  MANAGED_PATH,
  MANAGED_SCHEMA,
  PLAN_SCHEMA,
  RECEIPT_DIR,
  RECEIPT_SCHEMA,
  ProjectError,
  atomicWrite,
  currentBytes,
  ensureGitRepository,
  fromBase64,
  gitHeadOrNull,
  gitTree,
  normalizeManagedPath,
  readJson,
  requireCommit,
  runGit,
  sha256Bytes,
  shaOrNull,
  targetPath,
  toBase64,
  validateRequirements,
  verifyDigest,
  withDigest,
  writeJson,
  type ApplyReceipt,
  type ManagedFilePlan,
  type ManagedManifest,
  type ProjectPlan,
  type ProjectRequirements,
} from "./project_types.ts";
import {
  buildConsumerLock,
  generatedFiles,
  loadModules,
  resolveComposition,
  selectedSkillRequirements,
  selectionFromRequirements,
} from "./project_resolver.ts";

export function loadManaged(target: string): ManagedManifest | null {
  const path = targetPath(target, MANAGED_PATH);
  if (!existsSync(path)) return null;
  const value = readJson<ManagedManifest>(path);
  if (value.schema !== MANAGED_SCHEMA || !Array.isArray(value.paths))
    throw new ProjectError(`${path}: invalid managed manifest`);
  verifyDigest(value as unknown as Record<string, unknown>, path);
  return value;
}

function managedMap(managed: ManagedManifest | null): Map<string, { sha256: string; mode: number }> {
  const result = new Map<string, { sha256: string; mode: number }>();
  if (!managed) return result;
  for (const item of managed.paths) {
    const path = normalizeManagedPath(item.path);
    if (result.has(path) || typeof item.sha256 !== "string" || typeof item.mode !== "number")
      throw new ProjectError(`managed manifest path entry drifted: ${path}`);
    result.set(path, { sha256: item.sha256, mode: item.mode });
  }
  return result;
}

function assertManagedState(target: string, previous: Map<string, { sha256: string; mode: number }>): void {
  for (const [path, expected] of previous) {
    const bytes = currentBytes(targetPath(target, path));
    if (!bytes || sha256Bytes(bytes) !== expected.sha256) throw new ProjectError(`managed projection drifted: ${path}`);
  }
}

export function planProject(source: string, target: string, requirementsPath: string): ProjectPlan {
  source = resolve(source);
  target = resolve(target);
  ensureGitRepository(source);
  ensureGitRepository(target);
  const requirementsBytes = readFileSync(requirementsPath);
  const requirements = validateRequirements(JSON.parse(requirementsBytes.toString("utf8")), requirementsPath);
  requireCommit(source, requirements.release.commit);
  const modules = loadModules(source);
  const composition = resolveComposition(source, selectionFromRequirements(source, requirements), modules);
  const skills = selectedSkillRequirements(requirements.id, composition, modules);
  const lock = buildConsumerLock(source, requirements, composition, skills);
  const desired = generatedFiles(requirements, lock, skills);
  const managed = loadManaged(target);
  const previous = managedMap(managed);
  assertManagedState(target, previous);
  if (managed && managed.project !== requirements.id)
    throw new ProjectError(`target is managed for another project: ${managed.project}`);

  const files: ManagedFilePlan[] = [];
  for (const path of [...new Set([...desired.keys(), ...previous.keys()])].sort()) {
    const before = currentBytes(targetPath(target, path));
    const wasManaged = previous.has(path);
    const next = desired.get(path);
    if (next && before && !wasManaged) throw new ProjectError(`unmanaged conflict: ${path}`);
    if (!next && !wasManaged) continue;
    files.push({
      path,
      action: next ? "write" : "delete",
      mode: next?.mode ?? null,
      before_sha256: shaOrNull(before),
      before_base64: toBase64(before),
      after_sha256: next ? sha256Bytes(next.content) : null,
      after_base64: next ? next.content.toString("base64") : null,
    });
  }
  const managedBytes = currentBytes(targetPath(target, MANAGED_PATH));
  return withDigest({
    schema: PLAN_SCHEMA,
    project: requirements.id,
    mode: requirements.mode,
    release: { ...requirements.release, tree: gitTree(source, requirements.release.commit) },
    requirements_sha256: sha256Bytes(requirementsBytes),
    target_head: gitHeadOrNull(target),
    previous_managed_sha256: shaOrNull(managedBytes),
    previous_managed_base64: toBase64(managedBytes),
    consumer_lock_sha256: String(lock.content_sha256),
    files,
    embedded:
      requirements.mode === "embedded-core" ? { path: EMBEDDED_PATH, commit: requirements.release.commit } : null,
  }) as ProjectPlan;
}

function verifyPlan(plan: ProjectPlan): void {
  if (plan.schema !== PLAN_SCHEMA || !Array.isArray(plan.files)) throw new ProjectError("invalid project plan schema");
  verifyDigest(plan as unknown as Record<string, unknown>, "project plan");
  for (const item of plan.files) {
    normalizeManagedPath(item.path);
    const before = fromBase64(item.before_base64);
    if (shaOrNull(before) !== item.before_sha256)
      throw new ProjectError(`project plan before payload drifted: ${item.path}`);
    if (item.action === "write") {
      const after = fromBase64(item.after_base64);
      if (!after || item.after_sha256 !== sha256Bytes(after) || item.mode === null)
        throw new ProjectError(`project plan write payload drifted: ${item.path}`);
    } else if (item.action === "delete") {
      if (item.after_base64 !== null || item.after_sha256 !== null || item.mode !== null)
        throw new ProjectError(`project plan delete payload drifted: ${item.path}`);
    } else throw new ProjectError(`unknown project plan action: ${String(item.action)}`);
  }
}

function restore(path: string, content: Buffer | null, mode: number | null): void {
  if (content === null) {
    if (existsSync(path)) unlinkSync(path);
    return;
  }
  atomicWrite(path, content, mode ?? 0o644);
}

function cloneEmbedded(source: string, target: string, commit: string): void {
  const vendor = targetPath(target, EMBEDDED_PATH);
  if (existsSync(vendor)) throw new ProjectError(`embedded path already exists: ${EMBEDDED_PATH}`);
  mkdirSync(dirname(vendor), { recursive: true });
  const clone = spawnSync("git", ["clone", "--no-hardlinks", "--no-checkout", source, vendor], { encoding: "utf8" });
  if (clone.status !== 0) throw new ProjectError((clone.stderr || "embedded clone failed").trim());
  try {
    runGit(vendor, ["checkout", "--detach", commit]);
    runGit(vendor, ["config", "core.hooksPath", "/dev/null"]);
    if (runGit(vendor, ["rev-parse", "HEAD"]) !== commit)
      throw new ProjectError("embedded clone resolved the wrong commit");
    if (runGit(vendor, ["status", "--porcelain", "--untracked-files=all"]))
      throw new ProjectError("embedded clone is dirty after checkout");
  } catch (error) {
    rmSync(vendor, { recursive: true, force: true });
    throw error;
  }
}

function embeddedState(target: string): string | null {
  const vendor = targetPath(target, EMBEDDED_PATH);
  if (!existsSync(vendor)) return null;
  if (!existsSync(join(vendor, ".git"))) throw new ProjectError(`embedded path is not a Git clone: ${EMBEDDED_PATH}`);
  if (runGit(vendor, ["status", "--porcelain", "--untracked-files=all"]))
    throw new ProjectError(`embedded clone is dirty: ${EMBEDDED_PATH}`);
  return runGit(vendor, ["rev-parse", "HEAD"]);
}

function buildManaged(plan: ProjectPlan): ManagedManifest {
  return withDigest({
    schema: MANAGED_SCHEMA,
    project: plan.project,
    mode: plan.mode,
    plan_sha256: plan.content_sha256,
    source: plan.release,
    paths: plan.files
      .filter((item) => item.action === "write")
      .map((item) => ({ path: item.path, sha256: item.after_sha256!, mode: item.mode! }))
      .sort((a, b) => a.path.localeCompare(b.path)),
    embedded: plan.embedded,
  }) as ManagedManifest;
}

export function applyProject(source: string, target: string, planPath: string, receiptPath?: string): string {
  source = resolve(source);
  target = resolve(target);
  ensureGitRepository(source);
  ensureGitRepository(target);
  const plan = readJson<ProjectPlan>(planPath);
  verifyPlan(plan);
  requireCommit(source, plan.release.commit);
  if (gitTree(source, plan.release.commit) !== plan.release.tree) throw new ProjectError("plan release tree drifted");
  if (gitHeadOrNull(target) !== plan.target_head) throw new ProjectError("target HEAD changed since plan");
  const managedPath = targetPath(target, MANAGED_PATH);
  const currentManaged = currentBytes(managedPath);
  if (shaOrNull(currentManaged) !== plan.previous_managed_sha256)
    throw new ProjectError("managed manifest changed since plan");
  for (const item of plan.files)
    if (shaOrNull(currentBytes(targetPath(target, item.path))) !== item.before_sha256)
      throw new ProjectError(`target changed since plan: ${item.path}`);
  if (plan.embedded && embeddedState(target) !== null)
    throw new ProjectError(`embedded path already exists: ${EMBEDDED_PATH}`);

  const managedBytes = Buffer.from(`${JSON.stringify(buildManaged(plan), null, 2)}\n`);
  const finalReceiptPath = receiptPath
    ? resolve(receiptPath)
    : targetPath(target, `${RECEIPT_DIR}/apply-${plan.content_sha256.slice(0, 12)}.json`);
  if (existsSync(finalReceiptPath)) throw new ProjectError(`apply receipt already exists: ${finalReceiptPath}`);
  const applied: ManagedFilePlan[] = [];
  let embeddedCreated = false;
  try {
    if (plan.embedded) {
      cloneEmbedded(source, target, plan.embedded.commit);
      embeddedCreated = true;
    }
    for (const item of plan.files) {
      const path = targetPath(target, item.path);
      if (item.action === "write") atomicWrite(path, fromBase64(item.after_base64)!, item.mode!);
      else if (existsSync(path)) unlinkSync(path);
      applied.push(item);
    }
    atomicWrite(managedPath, managedBytes, 0o644);
    const receipt = withDigest({
      schema: RECEIPT_SCHEMA,
      project: plan.project,
      mode: plan.mode,
      plan_sha256: plan.content_sha256,
      files: plan.files,
      managed_before_sha256: plan.previous_managed_sha256,
      managed_before_base64: plan.previous_managed_base64,
      managed_after_sha256: sha256Bytes(managedBytes),
      managed_after_base64: managedBytes.toString("base64"),
      embedded_created: plan.embedded,
    }) as ApplyReceipt;
    writeJson(finalReceiptPath, receipt);
    return finalReceiptPath;
  } catch (error) {
    for (const item of [...applied].reverse())
      restore(targetPath(target, item.path), fromBase64(item.before_base64), item.mode);
    restore(managedPath, currentManaged, 0o644);
    if (embeddedCreated) rmSync(targetPath(target, EMBEDDED_PATH), { recursive: true, force: true });
    throw error;
  }
}

export function verifyProject(target: string): ManagedManifest {
  target = resolve(target);
  ensureGitRepository(target);
  const managed = loadManaged(target);
  if (!managed) throw new ProjectError("project is not managed by bettor-arena");
  for (const item of managed.paths) {
    const path = targetPath(target, item.path);
    const bytes = currentBytes(path);
    if (!bytes || sha256Bytes(bytes) !== item.sha256)
      throw new ProjectError(`managed projection missing or modified: ${item.path}`);
    if ((statSync(path).mode & 0o777) !== item.mode)
      throw new ProjectError(`managed projection mode drifted: ${item.path}`);
  }
  if (managed.embedded) {
    const head = embeddedState(target);
    if (head !== managed.embedded.commit)
      throw new ProjectError(`embedded release drifted: expected ${managed.embedded.commit}, got ${head}`);
  }
  return managed;
}

export function rollbackProject(target: string, receiptPath: string): void {
  target = resolve(target);
  ensureGitRepository(target);
  const receipt = readJson<ApplyReceipt>(receiptPath);
  if (receipt.schema !== RECEIPT_SCHEMA || !Array.isArray(receipt.files))
    throw new ProjectError("invalid apply receipt");
  verifyDigest(receipt as unknown as Record<string, unknown>, "apply receipt");
  const managedPath = targetPath(target, MANAGED_PATH);
  const managedBytes = currentBytes(managedPath);
  if (!managedBytes || sha256Bytes(managedBytes) !== receipt.managed_after_sha256)
    throw new ProjectError("managed manifest changed after apply; rollback refused");
  for (const item of receipt.files)
    if (shaOrNull(currentBytes(targetPath(target, item.path))) !== item.after_sha256)
      throw new ProjectError(`rollback target changed after apply: ${item.path}`);
  if (receipt.embedded_created && embeddedState(target) !== receipt.embedded_created.commit)
    throw new ProjectError("embedded clone changed after apply; rollback refused");
  for (const item of [...receipt.files].reverse())
    restore(targetPath(target, item.path), fromBase64(item.before_base64), item.mode);
  restore(managedPath, fromBase64(receipt.managed_before_base64), 0o644);
  if (receipt.embedded_created) rmSync(targetPath(target, EMBEDDED_PATH), { recursive: true, force: true });
}

export function copyRequirements(path: string, value: ProjectRequirements): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
}
