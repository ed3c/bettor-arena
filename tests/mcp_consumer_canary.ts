#!/usr/bin/env bun
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, readdirSync, rmSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { tmpdir } from "node:os";

interface RpcResponse {
  result?: {
    content?: Array<{ type?: string; text?: string }>;
    isError?: boolean;
    tools?: Array<{ name?: string }>;
  };
  error?: { code?: number; message?: string };
}

function sha256(value: Uint8Array | string): string {
  return createHash("sha256").update(value).digest("hex");
}

function git(root: string, args: string[]): string {
  const proc = spawnSync("git", ["-C", root, ...args], { encoding: "utf8" });
  if (proc.status !== 0) throw new Error(`git ${args.join(" ")} failed: ${proc.stderr || proc.stdout}`);
  return proc.stdout.trim();
}

function walk(root: string, at = root): string[] {
  const out: string[] = [];
  for (const name of readdirSync(at).sort()) {
    const path = join(at, name);
    if (statSync(path).isDirectory()) out.push(...walk(root, path));
    else out.push(path);
  }
  return out;
}

function invoke(root: string, ref: string, request: object): RpcResponse {
  const proc = spawnSync("python3", ["loopctl/mcp_server.py", "--ref", ref], {
    cwd: root,
    input: JSON.stringify(request) + "\n",
    encoding: "utf8",
    maxBuffer: 32 * 1024 * 1024,
    env: { ...process.env, LOOPCTL_REF: "" },
  });
  if (proc.status !== 0) {
    throw new Error(
      `MCP server exited ${proc.status}\n--- stdout ---\n${proc.stdout}\n--- stderr ---\n${proc.stderr}`,
    );
  }
  const lines = proc.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const line = lines.at(-1);
  if (!line) throw new Error(`MCP server returned no response\n--- stderr ---\n${proc.stderr}`);
  try {
    return JSON.parse(line) as RpcResponse;
  } catch (error) {
    throw new Error(`MCP server returned invalid JSON: ${String(error)}\n${line}\n--- stderr ---\n${proc.stderr}`);
  }
}

function requirePayload(response: RpcResponse): Record<string, any> {
  if (response.error) throw new Error(`MCP RPC error ${response.error.code}: ${response.error.message}`);
  const text = response.result?.content?.[0]?.text;
  if (!text) throw new Error(`MCP response has no text payload: ${JSON.stringify(response)}`);
  const payload = JSON.parse(text) as Record<string, any>;
  if (response.result?.isError || payload.exit !== 0) {
    throw new Error(`MCP tool returned red: ${JSON.stringify(payload, null, 2)}`);
  }
  return payload;
}

function main(): number {
  const root = resolve(import.meta.dir, "..");
  const ref = process.env.CTG_MCP_REF || git(root, ["rev-parse", "HEAD"]);
  const temp = mkdtempSync(join(tmpdir(), "bettor-mcp-canary-"));
  try {
    const bundle = join(temp, "bundle");
    const fixture = spawnSync("python3", ["-m", "code_truth_graph.fixture", "--out", bundle], {
      cwd: root,
      encoding: "utf8",
      env: { ...process.env, PYTHONPATH: join(root, "loop_wiki/code-truth-graph/src") },
    });
    if (fixture.status !== 0) {
      throw new Error(`CTG fixture failed ${fixture.status}: ${fixture.stderr || fixture.stdout}`);
    }

    const files = walk(bundle).map((path) => {
      const content = readFileSync(path);
      return {
        artifact_ref: relative(bundle, path).replaceAll("\\", "/"),
        sha256: sha256(content),
        content_base64: content.toString("base64"),
      };
    });
    const request = {
      jsonrpc: "2.0",
      id: 41,
      method: "tools/call",
      params: {
        name: "loopctl_ctg_run",
        arguments: { bundle: { packet_ref: "ctg-input.json", files } },
      },
    };

    const before = git(root, ["worktree", "list", "--porcelain"]);
    const payload = requirePayload(invoke(root, ref, request));
    const route = payload.ctg_delivery?.route_result;
    if (route?.overall?.exit !== 0) throw new Error(`CTG route result is red: ${JSON.stringify(route)}`);
    const artifacts = payload.ctg_delivery?.artifacts;
    if (!Array.isArray(artifacts) || artifacts.length === 0) {
      throw new Error(`MCP delivered no typed artifacts: ${JSON.stringify(payload)}`);
    }
    for (const artifact of artifacts) {
      const content = Buffer.from(artifact.content_base64, "base64");
      if (sha256(content) !== artifact.sha256) {
        throw new Error(`delivered artifact digest mismatch: ${artifact.kind}`);
      }
    }
    if (JSON.stringify(payload).includes("loopctl-mcp-")) {
      throw new Error("ephemeral server path leaked into the response");
    }
    const after = git(root, ["worktree", "list", "--porcelain"]);
    if (before !== after) throw new Error("MCP call left a disposable worktree behind");

    const badCarrier = invoke(root, ref, {
      jsonrpc: "2.0",
      id: 42,
      method: "tools/call",
      params: { name: "loopctl_ctg_run", arguments: { packet: "/tmp/forbidden.json" } },
    });
    const badText = badCarrier.result?.content?.[0]?.text || badCarrier.error?.message || "";
    if (!badCarrier.result?.isError || !/bundle|forbidden|undeclared/i.test(badText)) {
      throw new Error(`server-host path carrier was not refused: ${JSON.stringify(badCarrier)}`);
    }

    const tampered = structuredClone(request);
    tampered.id = 43;
    tampered.params.arguments.bundle.files[0].sha256 = "0".repeat(64);
    const badDigest = invoke(root, ref, tampered);
    const badDigestText = badDigest.result?.content?.[0]?.text || badDigest.error?.message || "";
    if (!badDigest.result?.isError || !/digest mismatch/i.test(badDigestText)) {
      throw new Error(`tampered input digest was not refused: ${JSON.stringify(badDigest)}`);
    }

    const tools = invoke(root, ref, { jsonrpc: "2.0", id: 44, method: "tools/list" });
    const names = tools.result?.tools?.map((tool) => tool.name).filter(Boolean) ?? [];
    if (!names.includes("loopctl_ctg_run")) throw new Error(`CTG run is absent from tools/list: ${names.join(",")}`);
    const forbidden = [
      "loopctl_macro_run",
      "loopctl_mcp_serve",
      "loopctl_container_build",
      "loopctl_openwiki_run",
      "loopctl_notebooklm_run",
      "loopctl_equivalence_run",
    ];
    const leaked = names.filter((name) => forbidden.includes(name!));
    if (leaked.length) throw new Error(`default-deny surface leaked tools: ${leaked.join(",")}`);

    console.log(`MCP EXTERNAL CONSUMER CANARY GREEN ref=${ref} artifacts=${artifacts.length}`);
    return 0;
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
}

try {
  process.exit(main());
} catch (error) {
  console.error(`MCP EXTERNAL CONSUMER CANARY RED: ${String(error instanceof Error ? error.message : error)}`);
  process.exit(2);
}
