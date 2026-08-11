import { createHash } from "node:crypto";
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

export const PROTOCOL = "2024-11-05";
export const POLICY_SCHEMA = "bettor-arena/mcp-policy/v1";
export const POLICY_FIELDS = [
  "name",
  "module",
  "mutation",
  "network",
  "secrets",
  "max_seconds",
  "max_request_bytes",
  "max_output_bytes",
] as const;

export const SECRET_NAMES = new Set([
  "ANTHROPIC_API_KEY",
  "CLAUDE_CODE_OAUTH_TOKEN",
  "CODEX_ACCESS_TOKEN",
  "CODEX_API_KEY",
  "E2B_API_KEY",
  "FORGEJO_PASSWORD",
  "FORGEJO_TOKEN",
  "GEMINI_API_KEY",
  "GITHUB_TOKEN",
  "OPENAI_API_KEY",
]);

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export interface McpCarrier {
  kind: string;
  max_request_bytes?: number;
  description?: string;
  result_file?: string;
  input_schema: Record<string, Json>;
}

export interface LoopCommand {
  loop: string;
  mode: string;
  target: string;
  required: string[];
  optional: string[];
  mcp_exposed?: boolean;
  mcp_carrier?: McpCarrier;
  writes?: string[];
  opt_in?: Record<string, string>;
  io?: {
    input?: string | Record<string, string>;
    output?: string[];
    exit?: string;
  };
}

export interface LoopContract {
  surface_version?: string;
  modes: Record<string, string>;
  commands: LoopCommand[];
}

export interface ToolPolicy {
  name: string;
  module: string;
  mutation: "none" | "disposable-worktree";
  network: "none" | "optional";
  secrets: "none" | "broker-only";
  max_seconds: number;
  max_request_bytes: number;
  max_output_bytes: number;
}

export interface McpPolicy {
  schema: string;
  tools: ToolPolicy[];
}

export interface ModuleManifest {
  id: string;
  roots: string[];
  provides: string[];
  requires: string[];
  components: Record<string, { required: boolean; paths: string[] }>;
  external_policy: {
    exposed: boolean;
    mutation: string;
    network: string;
    secrets: string;
  };
  loops: Array<{ id: string; external_policy: string }>;
}

export interface CompositionLock {
  modules: Array<{ id: string }>;
}

export interface GeneratedTool {
  name: string;
  description: string;
  inputSchema: Record<string, Json>;
  _argv: { loop: string; mode: string; flags: string[] };
  _policy: ToolPolicy;
  _carrier?: McpCarrier;
}

export interface ModuleSurface {
  tools: GeneratedTool[];
  modules: Map<string, ModuleManifest>;
  policyDigest: string;
}

export class McpError extends Error {}

function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") {
    const source = value as Record<string, unknown>;
    return Object.fromEntries(
      Object.keys(source)
        .sort()
        .map((key) => [key, stable(source[key])]),
    );
  }
  return value;
}

export function canonical(value: unknown): string {
  return JSON.stringify(stable(value), undefined, 0);
}

export function sha256(value: Uint8Array | string): string {
  return createHash("sha256").update(value).digest("hex");
}

export function digestValue(value: unknown): string {
  return sha256(canonical(value));
}

export function readJson<T>(path: string): T {
  try {
    return JSON.parse(readFileSync(path, "utf8")) as T;
  } catch (error) {
    throw new McpError(`cannot read JSON ${path}: ${String(error)}`);
  }
}

export function assertObject(
  value: unknown,
  label: string,
): asserts value is Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new McpError(`${label} must be an object`);
  }
}

export function assertExactFields(
  value: unknown,
  fields: readonly string[],
  label: string,
): asserts value is Record<string, unknown> {
  assertObject(value, label);
  const got = Object.keys(value).sort();
  const want = [...fields].sort();
  if (JSON.stringify(got) !== JSON.stringify(want)) {
    throw new McpError(
      `${label} fields drifted: got=${got.join(",")}, want=${want.join(",")}`,
    );
  }
}

export function safeArtifactRef(value: unknown): string {
  if (typeof value !== "string" || !value || isAbsolute(value)) {
    throw new McpError(`unsafe artifact_ref: ${String(value)}`);
  }
  const normalized = normalize(value).replaceAll("\\", "/");
  if (
    normalized === "." ||
    normalized.startsWith("../") ||
    normalized.includes("/../") ||
    normalized.startsWith("/") ||
    !/^[A-Za-z0-9][A-Za-z0-9._/-]*$/.test(normalized)
  ) {
    throw new McpError(`artifact_ref escapes bundle: ${value}`);
  }
  return normalized;
}

export function safeJoin(root: string, child: string): string {
  const target = resolve(root, child);
  const rel = relative(resolve(root), target);
  if (rel === ".." || rel.startsWith(`..${sep}`) || isAbsolute(rel)) {
    throw new McpError(`path escapes root: ${child}`);
  }
  return target;
}

export function gitText(
  root: string,
  args: string[],
  allowFailure = false,
): string {
  const process = spawnSync("git", ["-C", root, ...args], {
    encoding: "utf8",
    maxBuffer: 16 * 1024 * 1024,
  });
  if (process.status !== 0 && !allowFailure) {
    throw new McpError(
      (process.stderr || process.stdout || `git ${args.join(" ")} failed`)
        .trim()
        .slice(0, 1200),
    );
  }
  return (process.stdout || "").trim();
}

export function gitBytes(root: string, args: string[]): Buffer {
  const process = spawnSync("git", ["-C", root, ...args], {
    maxBuffer: 64 * 1024 * 1024,
  });
  if (process.status !== 0) {
    throw new McpError(
      Buffer.from(process.stderr || process.stdout || "git failed")
        .toString("utf8")
        .trim()
        .slice(0, 1200),
    );
  }
  return Buffer.from(process.stdout || Buffer.alloc(0));
}

export function jsonAtRef<T>(root: string, ref: string, path: string): T {
  safeArtifactRef(path);
  const raw = gitText(root, ["show", `${ref}:${path}`]);
  try {
    return JSON.parse(raw) as T;
  } catch (error) {
    throw new McpError(`${ref}:${path} is not valid JSON: ${String(error)}`);
  }
}

export function resolveRef(
  root: string,
  ref: string,
): { commit: string; tree: string } {
  if (["HEAD", "main", "master", "trunk"].includes(ref)) {
    throw new McpError(`mutable ref is refused: ${ref}`);
  }
  if (!/^[0-9a-f]{40}$/.test(ref) && !/^v[0-9][0-9A-Za-z._-]*$/.test(ref)) {
    throw new McpError("ref must be an exact 40-hex commit or immutable v* tag");
  }
  const commit = gitText(root, ["rev-parse", `${ref}^{commit}`]);
  const tree = gitText(root, ["rev-parse", `${commit}^{tree}`]);
  if (!/^[0-9a-f]{40}$/.test(commit) || !/^[0-9a-f]{40}$/.test(tree)) {
    throw new McpError("ref did not resolve to immutable Git ids");
  }
  return { commit, tree };
}

export function toolName(command: LoopCommand): string {
  return `loopctl_${command.loop}_${command.mode}`;
}

function describe(command: LoopCommand, contract: LoopContract): string {
  const io = command.io ?? {};
  const parts = [
    `${command.mode}: ${contract.modes[command.mode] ?? ""}`.trim(),
    `Loop: ${command.loop}.`,
  ];
  if (typeof io.input === "string") parts.push(`Input: ${io.input}`);
  const outputs = io.output ?? command.writes ?? [];
  if (outputs.length) parts.push(`Writes: ${outputs.join("; ")}`);
  if (io.exit) parts.push(`Exit: ${io.exit}`);
  for (const [flag, reason] of Object.entries(command.opt_in ?? {})) {
    parts.push(`${flag} — ${reason}`);
  }
  parts.push(
    "Exit codes are the target's own and are never re-mapped: 0 ok, 2 the loop's own check failed, 64 usage or a FATAL. Do not fold 2 and 64 together.",
  );
  return parts.join(" ");
}

function commandSchema(command: LoopCommand): Record<string, Json> {
  if (command.mcp_carrier) return command.mcp_carrier.input_schema;
  const input =
    typeof command.io?.input === "object" && command.io.input
      ? command.io.input
      : {};
  const optIn = command.opt_in ?? {};
  const properties: Record<string, Json> = {};
  for (const flag of [
    ...new Set([...command.required, ...command.optional]),
  ].sort()) {
    const key = flag.slice(2).replaceAll("-", "_");
    const boolean = Object.hasOwn(optIn, flag) && !Object.hasOwn(input, flag);
    properties[key] = {
      type: boolean ? "boolean" : "string",
      description: input[flag] ?? optIn[flag] ?? flag,
    };
  }
  return {
    type: "object",
    properties,
    required: command.required.map((flag) =>
      flag.slice(2).replaceAll("-", "_"),
    ),
    additionalProperties: false,
  };
}

function validateCarrier(command: LoopCommand, name: string): void {
  const carrier = command.mcp_carrier;
  if (!carrier) return;
  if (carrier.kind !== "closed-inline-bundle@1.0.0") {
    throw new McpError(`unsupported closed carrier: ${name}`);
  }
  if (!carrier.result_file) {
    throw new McpError(`closed carrier result_file is required: ${name}`);
  }
  safeArtifactRef(carrier.result_file);
  if (
    !command.required.includes("--packet") ||
    !command.required.includes("--output")
  ) {
    throw new McpError(`closed carrier requires --packet and --output: ${name}`);
  }
}

export function validatePolicy(
  policy: McpPolicy | null,
  contract: LoopContract,
): ToolPolicy[] {
  if (policy === null) return [];
  assertExactFields(policy, ["schema", "tools"], "MCP policy");
  if (policy.schema !== POLICY_SCHEMA) {
    throw new McpError(`MCP policy schema must be ${POLICY_SCHEMA}`);
  }
  if (!Array.isArray(policy.tools)) {
    throw new McpError("MCP policy tools must be an array");
  }
  const commands = new Map(
    contract.commands.map((command) => [toolName(command), command]),
  );
  const seen = new Set<string>();
  const normalized: ToolPolicy[] = [];
  for (const [index, entry] of policy.tools.entries()) {
    assertExactFields(entry, POLICY_FIELDS, `MCP policy tool[${index}]`);
    if (typeof entry.name !== "string" || !entry.name) {
      throw new McpError(`MCP policy tool[${index}] name is required`);
    }
    if (seen.has(entry.name)) {
      throw new McpError(`duplicate MCP policy tool: ${entry.name}`);
    }
    seen.add(entry.name);
    const command = commands.get(entry.name);
    if (!command) {
      throw new McpError(
        `MCP policy references unknown CLI command: ${entry.name}`,
      );
    }
    if (command.mcp_exposed !== true) {
      throw new McpError(
        `CLI contract has not explicitly enabled MCP exposure: ${entry.name}`,
      );
    }
    validateCarrier(command, entry.name);
    if (typeof entry.module !== "string" || !entry.module) {
      throw new McpError(`MCP policy module is required: ${entry.name}`);
    }
    if (!( ["none", "disposable-worktree"] as string[]).includes(entry.mutation)) {
      throw new McpError(`unsupported mutation policy: ${entry.name}`);
    }
    if (!( ["none", "optional"] as string[]).includes(entry.network)) {
      throw new McpError(`unsupported network policy: ${entry.name}`);
    }
    if (!( ["none", "broker-only"] as string[]).includes(entry.secrets)) {
      throw new McpError(`unsupported secrets policy: ${entry.name}`);
    }
    for (const field of [
      "max_seconds",
      "max_request_bytes",
      "max_output_bytes",
    ] as const) {
      if (!Number.isInteger(entry[field]) || entry[field] <= 0) {
        throw new McpError(`${entry.name}.${field} must be positive`);
      }
    }
    normalized.push(entry);
  }
  return normalized.sort((left, right) => left.name.localeCompare(right.name));
}

export function buildTools(
  contract: LoopContract,
  policy: McpPolicy | null,
): GeneratedTool[] {
  const commands = new Map(
    contract.commands.map((command) => [toolName(command), command]),
  );
  return validatePolicy(policy, contract).map((entry) => {
    const command = commands.get(entry.name)!;
    return {
      name: entry.name,
      description: describe(command, contract),
      inputSchema: commandSchema(command),
      _argv: {
        loop: command.loop,
        mode: command.mode,
        flags: [...new Set([...command.required, ...command.optional])].sort(),
      },
      _policy: entry,
      ...(command.mcp_carrier ? { _carrier: command.mcp_carrier } : {}),
    };
  });
}

export function publicTool(tool: GeneratedTool): Record<string, unknown> {
  return {
    name: tool.name,
    description: tool.description,
    inputSchema: tool.inputSchema,
  };
}
