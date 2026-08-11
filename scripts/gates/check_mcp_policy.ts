#!/usr/bin/env bun
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  McpError,
  buildTools,
  closurePrefixes,
  createWorkspace,
  gitText,
  loadSurface,
  moduleClosure,
  pruneWorktree,
  publicTool,
  resolveRef,
  toArgv,
  type LoopContract,
} from "../../loopctl/mcp_core.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "../..");

function check(): number {
  const commit = gitText(ROOT, ["rev-parse", "HEAD"]);
  const surface = loadSurface(ROOT, commit);
  if (!surface.tools.length || surface.tools.length >= 20) {
    throw new McpError(`explicit policy generated an invalid tool count: ${surface.tools.length}`);
  }
  const forbidden = new Set([
    "loopctl_macro_run",
    "loopctl_mcp_serve",
    "loopctl_container_build",
    "loopctl_openwiki_run",
    "loopctl_notebooklm_run",
    "loopctl_equivalence_run",
  ]);
  const leaked = surface.tools.filter((tool) => forbidden.has(tool.name));
  if (leaked.length) {
    throw new McpError(`dangerous tools exposed: ${leaked.map((tool) => tool.name)}`);
  }
  if (
    surface.tools.some((tool) =>
      Object.keys(publicTool(tool)).some((key) => key.startsWith("_")),
    )
  ) {
    throw new McpError("public tool projection leaked internal fields");
  }
  const runtime = readFileSync(resolve(ROOT, "loopctl/mcp_runtime.ts"), "utf8");
  if (/symlink(?:Sync|To)|node_modules.*owner/i.test(runtime)) {
    throw new McpError("Bun runtime contains owner dependency borrowing");
  }
  console.log(`PASS default-deny Bun MCP policy (${surface.tools.length} tools)`);
  return 0;
}

function selftest(): number {
  let red = 0;
  const expect = (name: string, condition: boolean): void => {
    if (condition) return;
    console.error(`SELFTEST case failed — ${name}`);
    red = 1;
  };

  const contract: LoopContract = {
    modes: { run: "run" },
    commands: [
      {
        loop: "demo",
        mode: "run",
        target: "x",
        required: [],
        optional: ["--json"],
      },
    ],
  };
  expect("no-policy-is-empty", buildTools(contract, null).length === 0);

  let mutableRefRejected = false;
  try {
    resolveRef(ROOT, "HEAD");
  } catch {
    mutableRefRejected = true;
  }
  expect("mutable-head-is-rejected", mutableRefRejected);

  const commit = gitText(ROOT, ["rev-parse", "HEAD"]);
  const surface = loadSurface(ROOT, commit);
  const nonCarrier = surface.tools.find((tool) => !tool._carrier);
  expect("policy-has-a-non-carrier-control", Boolean(nonCarrier));
  if (nonCarrier) {
    let hostPathRejected = false;
    try {
      toArgv(nonCarrier, { force_receipt: "/tmp/escape" });
    } catch {
      hostPathRejected = true;
    }
    expect("server-host-path-is-rejected", hostPathRejected);
  }

  const tool = surface.tools[0];
  expect("policy-has-an-exposed-tool", Boolean(tool));
  if (tool) {
    const workspace = createWorkspace(ROOT, commit);
    const parent = workspace.base;
    try {
      const closure = moduleClosure(tool._policy.module, surface.modules);
      const result = pruneWorktree(
        workspace.worktree,
        closurePrefixes(closure, surface.modules),
      );
      expect("pruning-keeps-and-removes-files", result.kept > 0 && result.removed > 0);
      if (tool._policy.module !== "notebooklm") {
        expect(
          "unselected-module-bytes-are-absent",
          !existsSync(resolve(workspace.worktree, "notebooklm/workflow.py")),
        );
      }
    } finally {
      workspace.cleanup();
    }
    expect("workspace-is-cleaned", !existsSync(parent));
  }

  console.log(`SELFTEST ${red ? "RED" : "GREEN"}`);
  return red;
}

function main(argv: string[]): number {
  try {
    if (argv[0] === "--selftest") return selftest();
    if (argv.length) {
      throw new McpError("no arguments are accepted except --selftest");
    }
    return check();
  } catch (error) {
    console.error(
      `MCP policy RED: ${String(error instanceof Error ? error.message : error)}`,
    );
    return error instanceof McpError ? 2 : 64;
  }
}

const invoked =
  process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) process.exit(main(process.argv.slice(2)));
