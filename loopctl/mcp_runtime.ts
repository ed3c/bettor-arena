#!/usr/bin/env bun
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { createServer } from "node:http";
import { createInterface } from "node:readline";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  McpError,
  PROTOCOL,
  attachInlineDelivery,
  boundedJsonPayload,
  canonical,
  closurePrefixes,
  createWorkspace,
  loadSurface,
  moduleClosure,
  prepareInlineCarrier,
  pruneWorktree,
  publicTool,
  resolveRef,
  sanitizedEnvironment,
  toArgv,
  type GeneratedTool,
  type ModuleManifest,
  type PreparedInlineCarrier,
} from "./mcp_core.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");

interface RpcRequest {
  jsonrpc?: string;
  id?: string | number | null;
  method?: string;
  params?: { name?: string; arguments?: unknown };
}

interface ParsedArgs {
  ref: string;
  httpPort?: number;
}

function rpcError(id: RpcRequest["id"], code: number, message: string): object {
  return { jsonrpc: "2.0", id: id ?? null, error: { code, message } };
}

export function parseArgs(argv: string[], environment: Record<string, string | undefined> = process.env): ParsedArgs {
  let ref = environment.LOOPCTL_REF ?? "";
  let httpPort: number | undefined;
  const rest = [...argv];
  while (rest.length) {
    const flag = rest.shift();
    if (flag === "--ref") {
      const value = rest.shift();
      if (!value) {
        throw new McpError("--ref requires an immutable commit or v* tag");
      }
      ref = value;
    } else if (flag === "--http") {
      const value = rest.shift();
      if (!value || !/^\d+$/.test(value)) {
        throw new McpError("--http requires a numeric port");
      }
      httpPort = Number(value);
      if (httpPort < 1 || httpPort > 65535) {
        throw new McpError("--http port is outside 1..65535");
      }
    } else if (flag === "--json") {
      // loopctl declares --json on its own surface; server output is always structured.
    } else {
      throw new McpError(`unknown argument: ${flag}`);
    }
  }
  if (!ref) {
    throw new McpError("an immutable --ref or LOOPCTL_REF is required");
  }
  return httpPort === undefined ? { ref } : { ref, httpPort };
}

export function executeTool(
  root: string,
  commit: string,
  tree: string,
  tool: GeneratedTool,
  modules: Map<string, ModuleManifest>,
  policyDigest: string,
  argumentsValue: unknown,
): Record<string, unknown> {
  const policy = tool._policy;
  const closure = moduleClosure(policy.module, modules);
  const prefixes = closurePrefixes(closure, modules);
  const workspace = createWorkspace(root, commit);
  let payload: Record<string, unknown> | undefined;
  try {
    const pruned = pruneWorktree(workspace.worktree, prefixes);
    const loopctl = join(workspace.worktree, "loopctl/loopctl.sh");
    if (!pruned.kept || !existsSync(loopctl)) {
      throw new McpError("selected module closure omitted loopctl");
    }

    let argv: string[];
    let preparedCarrier: PreparedInlineCarrier | undefined;
    if (tool._carrier) {
      preparedCarrier = prepareInlineCarrier(tool, workspace.base, argumentsValue, policy.max_request_bytes);
      argv = preparedCarrier.argv;
    } else {
      if (Buffer.byteLength(canonical(argumentsValue ?? {})) > policy.max_request_bytes) {
        throw new McpError("request exceeds policy limit");
      }
      argv = toArgv(tool, argumentsValue ?? {});
    }

    const process = spawnSync("sh", ["loopctl/loopctl.sh", ...argv], {
      cwd: workspace.worktree,
      env: sanitizedEnvironment(),
      encoding: "utf8",
      timeout: policy.max_seconds * 1000,
      maxBuffer: policy.max_output_bytes + 64 * 1024,
    });
    if (process.error) {
      if ((process.error as NodeJS.ErrnoException).code === "ETIMEDOUT") {
        throw new McpError(`tool timed out after ${policy.max_seconds} seconds`);
      }
      throw new McpError(`tool process failed: ${process.error.message}`);
    }
    payload = boundedJsonPayload(
      process.stdout || "",
      process.stderr || "",
      process.status ?? 64,
      policy.max_output_bytes,
    );
    if (typeof payload.exit !== "number") {
      payload.exit = process.status ?? 64;
    }
    delete payload.stdout;
    delete payload.stderr;
    if (preparedCarrier) {
      attachInlineDelivery(payload, tool, preparedCarrier, policy.max_output_bytes);
    }
    payload.mcp_subject = {
      module: policy.module,
      module_closure: closure,
      commit,
      tree,
      policy_sha256: policyDigest,
      kept_tracked_files: pruned.kept,
      removed_tracked_files: pruned.removed,
      owner_dependency_borrowing: false,
      runtime: "bun-typescript",
    };
  } finally {
    workspace.cleanup();
  }
  if (!payload) throw new McpError("tool produced no payload");
  (payload.mcp_subject as Record<string, unknown>).cleanup = "PASS";
  return payload;
}

export function handle(
  request: RpcRequest,
  root: string,
  commit: string,
  tree: string,
  tools: GeneratedTool[],
  modules: Map<string, ModuleManifest>,
  policyDigest: string,
): object | undefined {
  if (request.method === "initialize") {
    return {
      jsonrpc: "2.0",
      id: request.id ?? null,
      result: {
        protocolVersion: PROTOCOL,
        capabilities: { tools: {} },
        serverInfo: { name: "loopctl", version: commit },
      },
    };
  }
  if (request.method === "tools/list") {
    return {
      jsonrpc: "2.0",
      id: request.id ?? null,
      result: { tools: tools.map(publicTool) },
    };
  }
  if (request.method === "tools/call") {
    const tool = tools.find((candidate) => candidate.name === request.params?.name);
    if (!tool) {
      return rpcError(request.id, -32602, `unknown or externally denied tool ${JSON.stringify(request.params?.name)}`);
    }
    try {
      const payload = executeTool(root, commit, tree, tool, modules, policyDigest, request.params?.arguments ?? {});
      return {
        jsonrpc: "2.0",
        id: request.id ?? null,
        result: {
          content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
          isError: payload.exit !== 0,
        },
      };
    } catch (error) {
      const payload = {
        error: String(error instanceof Error ? error.message : error),
        exit: 64,
      };
      return {
        jsonrpc: "2.0",
        id: request.id ?? null,
        result: {
          content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
          isError: true,
        },
      };
    }
  }
  if (request.method?.startsWith("notifications/")) return undefined;
  return rpcError(request.id, -32601, `unsupported method: ${request.method}`);
}

async function serveStdio(
  root: string,
  commit: string,
  tree: string,
  tools: GeneratedTool[],
  modules: Map<string, ModuleManifest>,
  policyDigest: string,
): Promise<number> {
  const lines = createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of lines) {
    if (!line.trim()) continue;
    if (Buffer.byteLength(line) > 1024 * 1024) {
      console.log(JSON.stringify(rpcError(null, -32602, "request exceeds 1 MiB")));
      continue;
    }
    try {
      const request = JSON.parse(line) as RpcRequest;
      const response = handle(request, root, commit, tree, tools, modules, policyDigest);
      if (response) console.log(JSON.stringify(response));
    } catch (error) {
      console.log(JSON.stringify(rpcError(null, -32700, `parse error: ${String(error)}`)));
    }
  }
  return 0;
}

async function serveHttp(
  root: string,
  commit: string,
  tree: string,
  tools: GeneratedTool[],
  modules: Map<string, ModuleManifest>,
  policyDigest: string,
  port: number,
): Promise<number> {
  const server = createServer(async (request, response) => {
    if (request.method !== "POST" || request.url?.replace(/\/$/, "") !== "/mcp") {
      response.writeHead(404).end();
      return;
    }
    const chunks: Buffer[] = [];
    let total = 0;
    for await (const chunk of request) {
      const buffer = Buffer.from(chunk);
      total += buffer.length;
      if (total > 1024 * 1024) {
        response.writeHead(413, { "content-type": "application/json" });
        response.end(JSON.stringify(rpcError(null, -32602, "request exceeds 1 MiB")));
        return;
      }
      chunks.push(buffer);
    }
    try {
      const rpc = JSON.parse(Buffer.concat(chunks).toString("utf8")) as RpcRequest;
      const value = handle(rpc, root, commit, tree, tools, modules, policyDigest);
      if (!value) {
        response.writeHead(202).end();
        return;
      }
      const body = JSON.stringify(value);
      response.writeHead(200, {
        "content-type": "application/json",
        "content-length": Buffer.byteLength(body),
      });
      response.end(body);
    } catch (error) {
      const body = JSON.stringify(rpcError(null, -32700, `parse error: ${String(error)}`));
      response.writeHead(200, { "content-type": "application/json" });
      response.end(body);
    }
  });
  await new Promise<void>((accept, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", accept);
  });
  console.error(`mcp: serving ref=${commit} on http://127.0.0.1:${port}/mcp`);
  await new Promise<void>((accept) => {
    process.once("SIGINT", () => server.close(() => accept()));
    process.once("SIGTERM", () => server.close(() => accept()));
  });
  return 0;
}

function selftest(): number {
  let red = 0;
  const expectError = (name: string, operation: () => unknown): void => {
    try {
      operation();
      console.error(`SELFTEST case failed — ${name}`);
      red = 1;
    } catch {
      // expected
    }
  };
  expectError("missing-ref", () => parseArgs([], {}));
  expectError("mutable-head", () => resolveRef(ROOT, "HEAD"));
  const init = handle(
    { jsonrpc: "2.0", id: 1, method: "initialize" },
    ROOT,
    "a".repeat(40),
    "b".repeat(40),
    [],
    new Map(),
    "c".repeat(64),
  ) as { result?: { protocolVersion?: string } };
  if (init.result?.protocolVersion !== PROTOCOL) red = 1;
  const unknown = handle(
    {
      jsonrpc: "2.0",
      id: 2,
      method: "tools/call",
      params: { name: "nope" },
    },
    ROOT,
    "a".repeat(40),
    "b".repeat(40),
    [],
    new Map(),
    "c".repeat(64),
  ) as { error?: { message?: string } };
  if (!unknown.error?.message?.includes("externally denied")) red = 1;
  console.log(`SELFTEST ${red ? "RED" : "GREEN"}`);
  return red;
}

export async function main(argv: string[]): Promise<number> {
  if (argv[0] === "--selftest") return selftest();
  let parsed: ParsedArgs;
  try {
    parsed = parseArgs(argv);
  } catch (error) {
    console.error(`mcp-server FATAL: ${String(error instanceof Error ? error.message : error)}`);
    return 64;
  }
  try {
    const ids = resolveRef(ROOT, parsed.ref);
    const surface = loadSurface(ROOT, ids.commit);
    return parsed.httpPort
      ? serveHttp(ROOT, ids.commit, ids.tree, surface.tools, surface.modules, surface.policyDigest, parsed.httpPort)
      : serveStdio(ROOT, ids.commit, ids.tree, surface.tools, surface.modules, surface.policyDigest);
  } catch (error) {
    console.error(`mcp-server FATAL: ${String(error instanceof Error ? error.message : error)}`);
    return 64;
  }
}

const invoked = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) process.exit(await main(process.argv.slice(2)));
