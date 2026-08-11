import { afterEach, describe, expect, test } from "bun:test";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";
import {
  McpError,
  buildTools,
  collectCtgDelivery,
  collectInlineDelivery,
  createWorkspace,
  digestValue,
  materializeInlineBundle,
  moduleClosure,
  prepareInlineCarrier,
  pruneWorktree,
  resolveRef,
  safeArtifactRef,
  sha256,
  type CompositionLock,
  type LoopContract,
  type McpPolicy,
  type ModuleManifest,
} from "./mcp_core.ts";

const temporary: string[] = [];
afterEach(() => {
  while (temporary.length) {
    rmSync(temporary.pop()!, { recursive: true, force: true });
  }
});

function fixture() {
  const contract: LoopContract = {
    modes: { run: "run", test: "test" },
    commands: [
      {
        loop: "ctg",
        mode: "run",
        target: "run.sh",
        required: ["--packet", "--output"],
        optional: ["--json"],
        mcp_exposed: true,
        mcp_carrier: {
          kind: "closed-inline-bundle@1.0.0",
          result_file: "ctg-route-result.json",
          input_schema: {
            type: "object",
            required: ["bundle"],
            properties: { bundle: { type: "object" } },
          },
        },
      },
      {
        loop: "private",
        mode: "test",
        target: "private.sh",
        required: [],
        optional: ["--json"],
      },
    ],
  };
  const policy: McpPolicy = {
    schema: "bettor-arena/mcp-policy/v1",
    tools: [
      {
        name: "loopctl_ctg_run",
        module: "ctg-module",
        mutation: "disposable-worktree",
        network: "none",
        secrets: "none",
        max_seconds: 60,
        max_request_bytes: 1024 * 1024,
        max_output_bytes: 1024 * 1024,
      },
    ],
  };
  const lock: CompositionLock = { modules: [{ id: "ctg-module" }] };
  const manifests = new Map<string, ModuleManifest>([
    [
      "ctg-module",
      {
        id: "ctg-module",
        roots: ["loop_wiki/code-truth-graph"],
        provides: ["ctg/v1"],
        requires: [],
        components: {},
        external_policy: {
          exposed: true,
          mutation: "disposable-worktree",
          network: "none",
          secrets: "none",
        },
        loops: [{ id: "ctg", external_policy: "allowlisted" }],
      },
    ],
  ]);
  return { contract, policy, lock, manifests };
}

describe("default deny policy", () => {
  test("no policy exposes no tools", () => {
    const f = fixture();
    expect(buildTools(f.contract, null)).toEqual([]);
  });

  test("explicit policy selects only explicitly enabled commands", () => {
    const f = fixture();
    expect(buildTools(f.contract, f.policy).map((tool) => tool.name)).toEqual([
      "loopctl_ctg_run",
    ]);
  });

  test("omitted mcp_exposed cannot be re-enabled by policy", () => {
    const f = fixture();
    const denied = structuredClone(f.policy);
    denied.tools[0]!.name = "loopctl_private_test";
    expect(() => buildTools(f.contract, denied)).toThrow(/not explicitly enabled/);
  });

  test("legacy command-specific carrier kinds are rejected", () => {
    const f = fixture();
    const legacy = structuredClone(f.contract);
    legacy.commands[0]!.mcp_carrier!.kind = "ctg-inline-bundle@1.0.0";
    expect(() => buildTools(legacy, f.policy)).toThrow(/unsupported closed carrier/);
  });

  test("stable digest sorts nested object keys", () => {
    expect(digestValue({ b: 1, a: { z: 2, y: 3 } })).toBe(
      digestValue({ a: { y: 3, z: 2 }, b: 1 }),
    );
  });
});

describe("closed typed carrier", () => {
  test("materializes content and checks digest", () => {
    const root = mkdtempSync(join(tmpdir(), "mcp-carrier-"));
    temporary.push(root);
    const content = Buffer.from('{"packet":true}\n');
    const result = materializeInlineBundle(
      root,
      {
        bundle: {
          packet_ref: "ctg-input.json",
          files: [
            {
              artifact_ref: "ctg-input.json",
              sha256: sha256(content),
              content_base64: content.toString("base64"),
            },
          ],
        },
      },
      1024,
    );
    expect(readFileSync(result.packet)).toEqual(content);
  });

  test("dispatches through the command's declared loop and mode", () => {
    const f = fixture();
    const tool = buildTools(f.contract, f.policy)[0]!;
    const root = mkdtempSync(join(tmpdir(), "mcp-carrier-"));
    temporary.push(root);
    const content = Buffer.from('{"packet":true}\n');
    const prepared = prepareInlineCarrier(
      tool,
      root,
      {
        bundle: {
          packet_ref: "ctg-input.json",
          files: [
            {
              artifact_ref: "ctg-input.json",
              sha256: sha256(content),
              content_base64: content.toString("base64"),
            },
          ],
        },
      },
      1024,
    );
    expect(prepared.argv.slice(0, 2)).toEqual(["ctg", "run"]);
    expect(prepared.resultFile).toBe("ctg-route-result.json");
  });

  test("rejects path escape and digest mismatch", () => {
    expect(() => safeArtifactRef("../escape")).toThrow(McpError);
    const root = mkdtempSync(join(tmpdir(), "mcp-carrier-"));
    temporary.push(root);
    expect(() =>
      materializeInlineBundle(
        root,
        {
          bundle: {
            packet_ref: "ctg-input.json",
            files: [
              {
                artifact_ref: "ctg-input.json",
                sha256: "0".repeat(64),
                content_base64: Buffer.from("x").toString("base64"),
              },
            ],
          },
        },
        1024,
      ),
    ).toThrow(/digest mismatch/);
  });

  test("returns bounded verified generic artifacts without paths", () => {
    const root = mkdtempSync(join(tmpdir(), "mcp-output-"));
    temporary.push(root);
    const content = Buffer.from("hello");
    writeFileSync(join(root, "graph.json"), content);
    writeFileSync(
      join(root, "result.json"),
      JSON.stringify({
        overall: { exit: 0 },
        artifacts: [
          {
            kind: "graph",
            artifact_ref: "graph.json",
            sha256: sha256(content),
          },
        ],
      }),
    );
    const delivery = collectInlineDelivery(root, 1024, "result.json");
    expect(delivery.artifacts[0]).not.toHaveProperty("artifact_ref");
    expect(delivery.artifacts[0]?.sha256).toBe(sha256(content));
  });

  test("retains the CTG compatibility projection", () => {
    const root = mkdtempSync(join(tmpdir(), "mcp-output-"));
    temporary.push(root);
    const content = Buffer.from("hello");
    writeFileSync(join(root, "graph.json"), content);
    writeFileSync(
      join(root, "ctg-route-result.json"),
      JSON.stringify({
        overall: { exit: 0 },
        artifacts: [
          {
            kind: "graph",
            artifact_ref: "graph.json",
            sha256: sha256(content),
          },
        ],
      }),
    );
    const delivery = collectCtgDelivery(root, 1024);
    expect(delivery.artifacts[0]).not.toHaveProperty("artifact_ref");
    expect(delivery.route_result).toHaveProperty("overall");
  });
});

describe("module closure and workspace", () => {
  test("dependency closure is transitive", () => {
    const modules = new Map<string, ModuleManifest>([
      [
        "a",
        {
          id: "a",
          roots: ["a"],
          provides: ["a/v1"],
          requires: ["b/v1"],
          components: {},
          external_policy: {
            exposed: true,
            mutation: "none",
            network: "none",
            secrets: "none",
          },
          loops: [],
        },
      ],
      [
        "b",
        {
          id: "b",
          roots: ["b"],
          provides: ["b/v1"],
          requires: [],
          components: {},
          external_policy: {
            exposed: false,
            mutation: "none",
            network: "none",
            secrets: "none",
          },
          loops: [],
        },
      ],
    ]);
    expect(moduleClosure("a", modules)).toEqual(["a", "b"]);
  });

  test("mutable refs are refused", () => {
    expect(() => resolveRef(resolve(import.meta.dir, ".."), "HEAD")).toThrow(
      /mutable/,
    );
  });

  test("disposable worktree is cleaned", () => {
    const root = resolve(import.meta.dir, "..");
    const commit = spawnSync("git", ["-C", root, "rev-parse", "HEAD"], {
      encoding: "utf8",
    }).stdout.trim();
    const workspace = createWorkspace(root, commit);
    const parent = workspace.base;
    expect(pruneWorktree(workspace.worktree, ["loopctl"]).kept).toBeGreaterThan(
      0,
    );
    workspace.cleanup();
    expect(existsSync(parent)).toBe(false);
  });
});
