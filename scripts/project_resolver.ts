import { existsSync, readdirSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import {
  ID,
  LOCK_SCHEMA,
  ProjectError,
  assertClosedObject,
  gitTree,
  readJson,
  requireCommit,
  sha256Json,
  stringArray,
  withDigest,
  type ModuleManifest,
  type ModuleSelection,
  type ProjectRequirements,
  type ResolvedComposition,
} from "./project_types.ts";

function validateModule(value: unknown, path: string): ModuleManifest {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new ProjectError(`${path}: module object required`);
  const module = value as Partial<ModuleManifest>;
  if (module.schema !== "bettor-arena/module/v1" || typeof module.id !== "string" || !ID.test(module.id)) {
    throw new ProjectError(`${path}: invalid module identity`);
  }
  if (!module.components || typeof module.components !== "object" || Array.isArray(module.components))
    throw new ProjectError(`${path}: components object required`);
  for (const [name, component] of Object.entries(module.components)) {
    if (!ID.test(name) || !component || typeof component.required !== "boolean")
      throw new ProjectError(`${path}: invalid component ${name}`);
    stringArray(component.paths, `${path}:${name}.paths`);
  }
  stringArray(module.roots, `${path}:roots`);
  stringArray(module.provides, `${path}:provides`);
  stringArray(module.requires, `${path}:requires`);
  stringArray(module.conflicts, `${path}:conflicts`);
  if (!module.skills || !module.external_policy || typeof module.interface_version !== "string")
    throw new ProjectError(`${path}: incomplete module contract`);
  stringArray(module.skills.required, `${path}:skills.required`);
  stringArray(module.skills.optional, `${path}:skills.optional`);
  stringArray(module.skills.repo_owned, `${path}:skills.repo_owned`);
  return module as ModuleManifest;
}

export function loadModules(source: string): Map<string, { manifest: ModuleManifest; path: string }> {
  const root = join(source, ".arena/modules");
  const modules = new Map<string, { manifest: ModuleManifest; path: string }>();
  for (const name of readdirSync(root).sort()) {
    const path = join(root, name, "module.json");
    if (!existsSync(path)) continue;
    const manifest = validateModule(readJson(path), path);
    if (manifest.id !== name || modules.has(manifest.id))
      throw new ProjectError(`${path}: module directory/id mismatch`);
    modules.set(manifest.id, { manifest, path });
  }
  if (!modules.size) throw new ProjectError("module catalog is empty");
  return modules;
}

function mergeSelections(base: ModuleSelection[], extra: ModuleSelection[]): ModuleSelection[] {
  const merged = new Map<string, Set<string>>();
  for (const entry of [...base, ...extra]) {
    const components = merged.get(entry.id) ?? new Set<string>();
    entry.components.forEach((component) => components.add(component));
    merged.set(entry.id, components);
  }
  return [...merged.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([id, components]) => ({ id, components: [...components].sort() }));
}

export function selectionFromRequirements(source: string, requirements: ProjectRequirements): ModuleSelection[] {
  let preset: ModuleSelection[] = [];
  if (requirements.preset) {
    const path = join(source, `.arena/presets/${requirements.preset}.json`);
    const value = readJson<Record<string, unknown>>(path);
    if (value.schema !== "bettor-arena/preset/v1" || value.id !== requirements.preset || !Array.isArray(value.modules))
      throw new ProjectError(`${path}: invalid preset`);
    preset = value.modules.map((entry, index) => {
      assertClosedObject(entry, ["id", "components"], `${path}.modules[${index}]`);
      if (typeof entry.id !== "string" || !ID.test(entry.id)) throw new ProjectError(`${path}: invalid module id`);
      return { id: entry.id, components: stringArray(entry.components, `${path}:${entry.id}.components`) };
    });
  }
  const selection = mergeSelections(preset, requirements.modules);
  if (!selection.length) throw new ProjectError("project selects no modules");
  return selection;
}

export function resolveComposition(
  source: string,
  selection: ModuleSelection[],
  modules = loadModules(source),
): ResolvedComposition {
  const providers = new Map<string, string>();
  for (const [id, { manifest }] of modules) {
    for (const capability of manifest.provides) {
      if (providers.has(capability))
        throw new ProjectError(`capability has multiple providers: ${capability}: ${providers.get(capability)}, ${id}`);
      providers.set(capability, id);
    }
  }
  const requested = new Map<string, Set<string>>();
  const queue: string[] = [];
  for (const entry of selection) {
    if (!modules.has(entry.id)) throw new ProjectError(`unknown selected module: ${entry.id}`);
    requested.set(entry.id, new Set(entry.components));
    queue.push(entry.id);
  }
  const selected = new Set<string>();
  while (queue.length) {
    const id = queue.shift()!;
    if (selected.has(id)) continue;
    selected.add(id);
    for (const capability of modules.get(id)!.manifest.requires) {
      if (capability.startsWith("external:")) continue;
      const provider = providers.get(capability);
      if (!provider) throw new ProjectError(`${id} requires unprovided capability: ${capability}`);
      if (!selected.has(provider)) queue.push(provider);
    }
  }
  for (const id of [...selected].sort()) {
    const manifest = modules.get(id)!.manifest;
    const conflicts = manifest.conflicts.filter((candidate) => selected.has(candidate));
    if (conflicts.length) throw new ProjectError(`${id} conflicts with: ${conflicts.sort().join(", ")}`);
    const components =
      requested.get(id) ??
      new Set(
        Object.entries(manifest.components)
          .filter(([, value]) => value.required)
          .map(([name]) => name),
      );
    const unknown = [...components].filter((name) => !(name in manifest.components));
    if (unknown.length) throw new ProjectError(`${id} requests unknown components: ${unknown.sort().join(", ")}`);
    const omitted = Object.entries(manifest.components)
      .filter(([, value]) => value.required)
      .map(([name]) => name)
      .filter((name) => !components.has(name));
    if (omitted.length) throw new ProjectError(`${id} omits required components: ${omitted.sort().join(", ")}`);
    requested.set(id, components);
  }
  const capabilities: Record<string, string> = {};
  const resolved = [...selected].sort().map((id) => {
    const { manifest, path } = modules.get(id)!;
    manifest.provides.forEach((capability) => (capabilities[capability] = id));
    return {
      id,
      interface_version: manifest.interface_version,
      manifest_sha256: sha256Json(readJson(path)),
      components: [...requested.get(id)!].sort(),
      provides: [...manifest.provides].sort(),
      roots: [...manifest.roots].sort(),
    };
  });
  return { modules: resolved, capabilities: Object.fromEntries(Object.entries(capabilities).sort()) };
}

export function selectedSkillRequirements(
  project: string,
  composition: ResolvedComposition,
  modules: Map<string, { manifest: ModuleManifest; path: string }>,
): Record<string, unknown> {
  const shared = new Set<string>();
  const repoOwned = new Set<string>();
  for (const item of composition.modules) {
    const module = modules.get(item.id)!.manifest;
    module.skills.required.forEach((skill) => shared.add(skill));
    module.skills.repo_owned.forEach((skill) => repoOwned.add(skill));
  }
  return {
    schema: "shared-skills/consumer-requirements/v1",
    binding: project,
    shared: [...shared].sort(),
    repo_owned: [...repoOwned].sort(),
    surfaces: { claude: ".claude/skills", codex: ".agents/skills" },
  };
}

export function buildConsumerLock(
  source: string,
  requirements: ProjectRequirements,
  composition: ResolvedComposition,
  skills: Record<string, unknown>,
): Record<string, unknown> & { content_sha256: string } {
  requireCommit(source, requirements.release.commit);
  const policy = readJson(join(source, ".arena/mcp-policy.json"));
  return withDigest({
    schema: LOCK_SCHEMA,
    project: requirements.id,
    mode: requirements.mode,
    source: { ...requirements.release, tree: gitTree(source, requirements.release.commit) },
    modules: composition.modules,
    capabilities: composition.capabilities,
    skills,
    mcp_policy_sha256: sha256Json(policy),
    runtime: "bun-typescript",
  });
}

function launcher(mode: ProjectRequirements["mode"], commit: string): string {
  const rootExpression =
    mode === "remote-consumer"
      ? "${BETTOR_ARENA_ROOT:?set BETTOR_ARENA_ROOT to a clean bettor-arena checkout}"
      : "$repo_root/.arena/vendor/bettor";
  return `#!/bin/sh
set -eu
repo_root="$(git rev-parse --show-toplevel)" || exit 64
arena_root="${rootExpression}"
command -v bun >/dev/null 2>&1 || { echo "bun absent" >&2; exit 64; }
[ -f "$arena_root/loopctl/mcp_runtime.ts" ] || { echo "bettor Bun MCP runtime missing: $arena_root" >&2; exit 64; }
actual="$(git -c core.hooksPath=/dev/null -c core.fsmonitor=false -C "$arena_root" rev-parse HEAD)" || exit 64
[ "$actual" = "${commit}" ] || { echo "bettor release drift: expected ${commit}, got $actual" >&2; exit 2; }
[ -z "$(git -c core.hooksPath=/dev/null -c core.fsmonitor=false -C "$arena_root" status --porcelain --untracked-files=all)" ] || { echo "bettor release checkout is dirty" >&2; exit 2; }
exec bun "$arena_root/loopctl/mcp_runtime.ts" --ref "${commit}"
`;
}

export function generatedFiles(
  requirements: ProjectRequirements,
  lock: Record<string, unknown>,
  skills: Record<string, unknown>,
): Map<string, { content: Buffer; mode: number }> {
  const commit = requirements.release.commit;
  const header = `# ${requirements.id} — bettor-arena consumer entry

This project consumes immutable bettor-arena release \`${commit}\` in \`${requirements.mode}\` mode.
Read \`.arena/consumer.lock.json\` before using a selected module. Use the generated MCP adapter; do not call bettor private entrypoints or copy Skills by hand. PASS, FAIL, ABSENT, NOT_IMPLEMENTED, and NOT_EXERCISED remain distinct.
`;
  const bootstrap = `#!/bin/sh
set -eu
root="$(git rev-parse --show-toplevel)" || exit 64
command -v git >/dev/null 2>&1 || { echo "git absent" >&2; exit 64; }
command -v bun >/dev/null 2>&1 || { echo "bun absent" >&2; exit 64; }
[ -f "$root/.arena/consumer.lock.json" ] || { echo "consumer lock absent" >&2; exit 64; }
[ -x "$root/.arena/bin/bettor-mcp" ] || { echo "bettor MCP launcher absent" >&2; exit 64; }
${requirements.mode === "remote-consumer" ? ': "${BETTOR_ARENA_ROOT:?set BETTOR_ARENA_ROOT to the pinned bettor-arena checkout}"' : '[ -d "$root/.arena/vendor/bettor/.git" ] || { echo "embedded bettor clone absent" >&2; exit 64; }'}
echo "bootstrap OK: ${requirements.id} -> bettor ${commit.slice(0, 12)} (bun-typescript)"
`;
  const mcp = {
    mcpServers: {
      "bettor-arena": {
        type: "stdio",
        command: "sh",
        args: [
          "-c",
          'repo_root="$(git rev-parse --show-toplevel)" || exit 64; exec "$repo_root/.arena/bin/bettor-mcp"',
        ],
        env: {},
      },
    },
  };
  const codex = `# Portable bettor-arena MCP projection. Host trust, network, sockets, and permissions are human-owned.
[mcp_servers.bettor-arena]
command = "sh"
args = ["-c", 'repo_root="$(git rev-parse --show-toplevel)" || exit 64; exec "$repo_root/.arena/bin/bettor-mcp"']
enabled = true
required = false
startup_timeout_sec = 30
tool_timeout_sec = 300
`;
  const values = new Map<string, { content: Buffer; mode: number }>([
    [
      "AGENTS.md",
      {
        content: Buffer.from(`${header}\nCodex host permissions, trust, and network remain human-owned.\n`),
        mode: 0o644,
      },
    ],
    [
      "CLAUDE.md",
      {
        content: Buffer.from(`${header}\nClaude project MCP activation and permissions remain human-owned.\n`),
        mode: 0o644,
      },
    ],
    ["bootstrap.sh", { content: Buffer.from(bootstrap), mode: 0o755 }],
    [".arena/bin/bettor-mcp", { content: Buffer.from(launcher(requirements.mode, commit)), mode: 0o755 }],
    [
      ".arena/consumer.requirements.json",
      { content: Buffer.from(`${JSON.stringify(requirements, null, 2)}\n`), mode: 0o644 },
    ],
    [".arena/consumer.lock.json", { content: Buffer.from(`${JSON.stringify(lock, null, 2)}\n`), mode: 0o644 }],
    [
      ".agents/shared-skills.requirements.json",
      { content: Buffer.from(`${JSON.stringify(skills, null, 2)}\n`), mode: 0o644 },
    ],
    [".mcp.json", { content: Buffer.from(`${JSON.stringify(mcp, null, 2)}\n`), mode: 0o644 }],
    [".codex/config.toml", { content: Buffer.from(codex), mode: 0o644 }],
  ]);
  const forbidden = [
    "ANTHROPIC" + "_API_KEY=",
    "OPENAI" + "_API_KEY=",
    "E2B" + "_API_KEY=",
    "CODEX" + "_API_KEY=",
    "/Use" + "rs/",
    "~/",
  ];
  for (const [path, value] of values) {
    const text = value.content.toString("utf8");
    for (const marker of forbidden)
      if (text.includes(marker))
        throw new ProjectError(`generated projection contains forbidden material ${marker}: ${path}`);
    if (isAbsolute(path)) throw new ProjectError(`generated path is absolute: ${path}`);
  }
  return values;
}
