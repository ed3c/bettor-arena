#!/usr/bin/env bun
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildTools,
  publicTool,
  readJson,
  type LoopContract,
  type McpPolicy,
} from "./mcp_core.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");

function parseArgs(argv: string[]): { contract: string; policy: string | null } {
  if (!argv.length) {
    return {
      contract: resolve(HERE, "contract.json"),
      policy: resolve(ROOT, ".arena/mcp-policy.json"),
    };
  }
  const contract = resolve(argv[0]!);
  let policy: string | null = resolve(ROOT, ".arena/mcp-policy.json");
  const rest = argv.slice(1);
  while (rest.length) {
    const flag = rest.shift();
    if (flag === "--policy") {
      const value = rest.shift();
      if (!value) throw new Error("--policy requires a path");
      policy = resolve(value);
    } else if (flag === "--no-policy") {
      policy = null;
    } else {
      throw new Error(`unknown argument: ${flag}`);
    }
  }
  return { contract, policy };
}

export function generate(
  contractPath: string,
  policyPath: string | null,
): object {
  const contract = readJson<LoopContract>(contractPath);
  const policy = policyPath ? readJson<McpPolicy>(policyPath) : null;
  return { tools: buildTools(contract, policy).map(publicTool) };
}

function selftest(): number {
  const contract: LoopContract = {
    modes: { run: "run", prove: "prove" },
    commands: [
      {
        loop: "micro",
        mode: "run",
        target: "x",
        required: ["--packet"],
        optional: ["--json"],
        mcp_exposed: true,
      },
      {
        loop: "ctg",
        mode: "build-local",
        target: "y",
        required: [],
        optional: ["--json"],
        mcp_exposed: false,
      },
    ],
  };
  if (buildTools(contract, null).length !== 0) {
    console.error("SELFTEST case failed — no policy did not mean no tools");
    return 1;
  }
  const policy: McpPolicy = {
    schema: "bettor-arena/mcp-policy/v1",
    tools: [
      {
        name: "loopctl_micro_run",
        module: "micro",
        mutation: "disposable-worktree",
        network: "none",
        secrets: "none",
        max_seconds: 30,
        max_request_bytes: 1024,
        max_output_bytes: 2048,
      },
    ],
  };
  const tools = buildTools(contract, policy);
  if (tools.length !== 1 || tools[0]?.name !== "loopctl_micro_run") {
    console.error(
      "SELFTEST case failed — explicit policy did not select exactly one tool",
    );
    return 1;
  }
  console.log("SELFTEST GREEN");
  return 0;
}

export function main(argv: string[]): number {
  if (argv[0] === "--selftest") return selftest();
  try {
    const args = parseArgs(argv);
    console.log(JSON.stringify(generate(args.contract, args.policy), null, 2));
    return 0;
  } catch (error) {
    console.error(
      `MCP policy RED: ${String(error instanceof Error ? error.message : error)}`,
    );
    return 2;
  }
}

const invoked =
  process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) process.exit(main(process.argv.slice(2)));
