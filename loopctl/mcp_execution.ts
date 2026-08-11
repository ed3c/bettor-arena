import { spawnSync } from "node:child_process";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { dirname, isAbsolute, join, normalize, relative, resolve, sep } from "node:path";
import { tmpdir } from "node:os";
import {
  McpError,
  SECRET_NAMES,
  assertExactFields,
  assertObject,
  buildTools,
  canonical,
  digestValue,
  gitBytes,
  gitText,
  jsonAtRef,
  safeArtifactRef,
  safeJoin,
  sha256,
  type CompositionLock,
  type GeneratedTool,
  type McpPolicy,
  type ModuleManifest,
  type ModuleSurface,
} from "./mcp_contract.ts";

export function selectedModules(lock: CompositionLock): Set<string> {
  if (!Array.isArray(lock.modules)) throw new McpError("composition lock modules are malformed");
  return new Set(lock.modules.map((item) => item.id));
}

export function loadModulesAtRef(
  root: string,
  ref: string,
  selected: Set<string>,
): Map<string, ModuleManifest> {
  const modules = new Map<string, ModuleManifest>();
  for (const id of [...selected].sort()) {
    modules.set(id, jsonAtRef<ModuleManifest>(root, ref, `.arena/modules/${id}/module.json`));
  }
  return modules;
}

export function validateExternal(
  tools: GeneratedTool[],
  lock: CompositionLock,
  modules: Map<string, ModuleManifest>,
): void {
  const selected = selectedModules(lock);
  for (const tool of tools) {
    const policy = tool._policy;
    if (!selected.has(policy.module)) {
      throw new McpError(`MCP policy module is not selected: ${policy.module}`);
    }
    const module = modules.get(policy.module);
    if (!module) throw new McpError(`MCP policy module manifest is absent: ${policy.module}`);
    if (module.external_policy?.exposed !== true) {
      throw new McpError(`module does not permit external exposure: ${policy.module}`);
    }
    const loops = module.loops.filter((loop) => loop.id === tool._argv.loop);
    if (loops.length !== 1 || loops[0]!.external_policy !== "allowlisted") {
      throw new McpError(
        `tool ${tool.name} is not an allowlisted loop of module ${policy.module}`,
      );
    }
    if (
      policy.mutation !== module.external_policy.mutation &&
      !(policy.mutation === "none" && module.external_policy.mutation === "disposable-worktree")
    ) {
      throw new McpError(`tool mutation exceeds module policy: ${tool.name}`);
    }
    if (policy.secrets !== "none") {
      throw new McpError(`broker-only secret delivery is not implemented for ${tool.name}`);
    }
  }
}

export function moduleClosure(
  moduleId: string,
  modules: Map<string, ModuleManifest>,
): string[] {
  const providers = new Map<string, string>();
  for (const [id, module] of modules) {
    for (const capability of module.provides ?? []) {
      if (providers.has(capability) && providers.get(capability) !== id) {
        throw new McpError(`duplicate capability provider: ${capability}`);
      }
      providers.set(capability, id);
    }
  }
  const selected = new Set<string>();
  const queue = [moduleId];
  while (queue.length) {
    const current = queue.shift()!;
    if (selected.has(current)) continue;
    const module = modules.get(current);
    if (!module) throw new McpError(`module absent from selected closure: ${current}`);
    selected.add(current);
    for (const capability of module.requires ?? []) {
      if (capability.startsWith("external:")) continue;
      const provider = providers.get(capability);
      if (!provider) throw new McpError(`${current} has no provider for ${capability}`);
      queue.push(provider);
    }
  }
  return [...selected].sort();
}

function portablePrefix(value: string): string {
  const normalized = normalize(value).replaceAll("\\", "/").replace(/\/$/, "");
  if (!normalized || normalized === "." || isAbsolute(value) || normalized.includes("..")) {
    throw new McpError(`module path is not portable: ${value}`);
  }
  return normalized;
}

export function closurePrefixes(
  closure: string[],
  modules: Map<string, ModuleManifest>,
): string[] {
  const prefixes = new Set<string>();
  for (const id of closure) {
    const module = modules.get(id)!;
    for (const root of module.roots ?? []) prefixes.add(portablePrefix(root));
    for (const component of Object.values(module.components ?? {})) {
      for (const path of component.paths ?? []) prefixes.add(portablePrefix(path));
    }
    prefixes.add(`.arena/modules/${id}/module.json`);
  }
  for (const fixed of [
    ".arena/mcp-policy.json",
    ".arena/locks/bettor-arena.lock.json",
    ".arena/contexts.lock.json",
    "data/module-proof/subjects.lock.json",
    "data/context-capsules/driver-parity.json",
  ]) {
    prefixes.add(fixed);
  }
  return [...prefixes].sort();
}

function matchesPrefix(path: string, prefix: string): boolean {
  return path === prefix || path.startsWith(`${prefix}/`);
}

export function pruneWorktree(
  worktree: string,
  prefixes: string[],
): { kept: number; removed: number } {
  const raw = gitBytes(worktree, ["ls-files", "-z"]);
  let kept = 0;
  let removed = 0;
  for (const path of raw.toString("utf8").split("\0")) {
    if (!path) continue;
    if (prefixes.some((prefix) => matchesPrefix(path, prefix))) {
      kept += 1;
      continue;
    }
    const target = join(worktree, path);
    if (existsSync(target)) unlinkSync(target);
    removed += 1;
  }
  return { kept, removed };
}

export function createWorkspace(root: string, commit: string): {
  base: string;
  worktree: string;
  cleanup: () => void;
} {
  const base = mkdtempSync(join(tmpdir(), "loopctl-mcp-"));
  const worktree = join(base, "repo");
  try {
    gitText(root, ["worktree", "add", "--detach", worktree, commit]);
  } catch (error) {
    rmSync(base, { recursive: true, force: true });
    throw error;
  }
  let done = false;
  return {
    base,
    worktree,
    cleanup: () => {
      if (done) return;
      done = true;
      spawnSync("git", ["-C", root, "worktree", "remove", "--force", worktree], {
        encoding: "utf8",
      });
      rmSync(base, { recursive: true, force: true });
    },
  };
}

export function toArgv(tool: GeneratedTool, argumentsValue: unknown): string[] {
  assertObject(argumentsValue, "tool arguments");
  if (tool._carrier) {
    throw new McpError("typed inline carrier accepts exactly one bundle object; local packet/output paths are forbidden");
  }
  const allowed = new Map(
    tool._argv.flags.map((flag) => [flag.slice(2).replaceAll("-", "_"), flag]),
  );
  const unknown = Object.keys(argumentsValue).filter((key) => !allowed.has(key));
  if (unknown.length) throw new McpError(`undeclared argument(s): ${unknown.sort().join(", ")}`);
  const argv = [tool._argv.loop, tool._argv.mode];
  for (const key of Object.keys(argumentsValue).sort()) {
    const value = argumentsValue[key];
    const flag = allowed.get(key)!;
    if (typeof value === "boolean") {
      if (value) argv.push(flag);
      continue;
    }
    if (typeof value !== "string") {
      throw new McpError(`argument ${key} must be a string or boolean`);
    }
    const candidate = normalize(value).replaceAll("\\", "/");
    if (isAbsolute(value) || candidate === ".." || candidate.startsWith("../") || candidate.includes("/../")) {
      throw new McpError(`server-host path is forbidden: ${key}`);
    }
    argv.push(flag, value);
  }
  if (!argv.includes("--json")) argv.push("--json");
  return argv;
}

function decodeBase64(value: unknown, label: string): Buffer {
  if (typeof value !== "string" || value.length % 4 !== 0 || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
    throw new McpError(`${label} has invalid base64`);
  }
  return Buffer.from(value, "base64");
}

export function materializeInlineBundle(
  base: string,
  argumentsValue: unknown,
  maxBytes: number,
): { packet: string; output: string } {
  assertExactFields(argumentsValue, ["bundle"], "carrier arguments");
  const bundle = argumentsValue.bundle;
  assertExactFields(bundle, ["packet_ref", "files"], "bundle");
  if (!Array.isArray(bundle.files) || bundle.files.length === 0) {
    throw new McpError("bundle.files must be non-empty");
  }
  const packetRef = safeArtifactRef(bundle.packet_ref);
  const target = join(base, "input");
  const output = join(base, "output");
  mkdirSync(target, { recursive: true });
  mkdirSync(output, { recursive: true });
  const seen = new Set<string>();
  let total = 0;
  for (const [index, raw] of bundle.files.entries()) {
    assertExactFields(raw, ["artifact_ref", "sha256", "content_base64"], `bundle.files[${index}]`);
    const artifactRef = safeArtifactRef(raw.artifact_ref);
    if (seen.has(artifactRef)) throw new McpError(`duplicate artifact_ref: ${artifactRef}`);
    seen.add(artifactRef);
    if (typeof raw.sha256 !== "string" || !/^[0-9a-f]{64}$/.test(raw.sha256)) {
      throw new McpError(`bundle.files[${index}] has invalid sha256`);
    }
    const content = decodeBase64(raw.content_base64, `bundle.files[${index}]`);
    total += content.length;
    if (total > maxBytes) throw new McpError("decoded inline request exceeds policy limit");
    if (sha256(content) !== raw.sha256) {
      throw new McpError(`inline artifact digest mismatch: ${artifactRef}`);
    }
    const destination = safeJoin(target, artifactRef);
    mkdirSync(dirname(destination), { recursive: true });
    writeFileSync(destination, content);
  }
  if (!seen.has(packetRef)) throw new McpError("packet_ref is not present in files");
  return { packet: safeJoin(target, packetRef), output };
}

export function boundedJsonPayload(
  stdout: string,
  stderr: string,
  returnCode: number,
  limit: number,
): Record<string, unknown> {
  if (Buffer.byteLength(stdout) + Buffer.byteLength(stderr) > limit) {
    throw new McpError("loopctl output exceeds policy limit");
  }
  try {
    const value = JSON.parse(stdout || "{}");
    assertObject(value, "loopctl JSON result");
    return value;
  } catch (error) {
    if (error instanceof McpError) throw error;
    return {
      error: "loopctl produced no JSON result",
      exit: returnCode,
      stdout: stdout.slice(-4000),
      stderr: stderr.slice(-4000),
    };
  }
}

export function collectCtgDelivery(
  output: string,
  maxBytes: number,
): {
  route_result: Record<string, unknown>;
  artifacts: Array<{ kind: unknown; sha256: string; content_base64: string }>;
} {
  const resultPath = join(output, "ctg-route-result.json");
  if (!existsSync(resultPath)) throw new McpError("CTG route result is absent");
  const resultBytes = readFileSync(resultPath);
  let total = resultBytes.length;
  if (total > maxBytes) throw new McpError("CTG output exceeds policy limit");
  const routeResult = JSON.parse(resultBytes.toString("utf8")) as Record<string, unknown>;
  const rawArtifacts = routeResult.artifacts;
  if (!Array.isArray(rawArtifacts)) throw new McpError("CTG route result artifacts must be an array");
  const artifacts: Array<{ kind: unknown; sha256: string; content_base64: string }> = [];
  for (const [index, raw] of rawArtifacts.entries()) {
    assertObject(raw, `CTG artifacts[${index}]`);
    const artifactRef = safeArtifactRef(raw.artifact_ref);
    if (typeof raw.sha256 !== "string" || !/^[0-9a-f]{64}$/.test(raw.sha256)) {
      throw new McpError(`CTG artifacts[${index}] has invalid sha256`);
    }
    const content = readFileSync(safeJoin(output, artifactRef));
    total += content.length;
    if (total > maxBytes) throw new McpError("CTG typed output exceeds policy limit");
    if (sha256(content) !== raw.sha256) {
      throw new McpError(`CTG result artifact digest mismatch: ${artifactRef}`);
    }
    artifacts.push({
      kind: raw.kind,
      sha256: raw.sha256,
      content_base64: content.toString("base64"),
    });
  }
  return { route_result: routeResult, artifacts };
}

export function sanitizedEnvironment(): NodeJS.ProcessEnv {
  const environment: NodeJS.ProcessEnv = { ...process.env };
  for (const name of SECRET_NAMES) delete environment[name];
  return environment;
}

export function loadSurface(root: string, commit: string): ModuleSurface {
  const contract = jsonAtRef<LoopContract>(root, commit, "loopctl/contract.json");
  const policy = jsonAtRef<McpPolicy>(root, commit, ".arena/mcp-policy.json");
  const lock = jsonAtRef<CompositionLock>(root, commit, ".arena/locks/bettor-arena.lock.json");
  const modules = loadModulesAtRef(root, commit, selectedModules(lock));
  const tools = buildTools(contract, policy);
  validateExternal(tools, lock, modules);
  return { tools, modules, policyDigest: digestValue(policy) };
}
