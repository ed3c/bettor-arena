import {
  McpError,
  buildTools,
  digestValue,
  gitText,
  type CompositionLock,
  type LoopContract,
  type McpPolicy,
  type ModuleManifest,
  type ModuleSurface,
} from "./mcp_contract.ts";
import {
  selectedModules,
  validateExternal,
} from "./mcp_execution.ts";

function internalJsonAtRef<T>(root: string, ref: string, path: string): T {
  if (!/^[A-Za-z0-9._/-]+$/.test(path) || path.includes("..") || path.startsWith("/")) {
    throw new McpError(`unsafe internal repository path: ${path}`);
  }
  const raw = gitText(root, ["show", `${ref}:${path}`]);
  try {
    return JSON.parse(raw) as T;
  } catch (error) {
    throw new McpError(`${ref}:${path} is not valid JSON: ${String(error)}`);
  }
}

export function loadSurface(root: string, commit: string): ModuleSurface {
  const contract = internalJsonAtRef<LoopContract>(root, commit, "loopctl/contract.json");
  const policy = internalJsonAtRef<McpPolicy>(root, commit, ".arena/mcp-policy.json");
  const lock = internalJsonAtRef<CompositionLock>(
    root,
    commit,
    ".arena/locks/bettor-arena.lock.json",
  );
  const modules = new Map<string, ModuleManifest>();
  for (const id of [...selectedModules(lock)].sort()) {
    modules.set(
      id,
      internalJsonAtRef<ModuleManifest>(root, commit, `.arena/modules/${id}/module.json`),
    );
  }
  const tools = buildTools(contract, policy);
  validateExternal(tools, lock, modules);
  return { tools, modules, policyDigest: digestValue(policy) };
}
