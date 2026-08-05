import { afterEach, describe, expect, test } from "bun:test";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const ROOT = resolve(import.meta.dir, "..");
const CLI = join(ROOT, "src", "cli.ts");
const MINIMUM_LINEAGE_CLI = join(ROOT, "src", "check_minimum_lineage.ts");
const FAST_QUALITY_CLI = join(ROOT, "src", "run_fast_quality.ts");
const GENERATED_FAST_QUALITY_CLI = join(ROOT, "src", "run_generated_fast_quality.ts");
const GENERATED_REPO_VERIFIER = join(ROOT, "src", "verify_generated_repo.ts");
const temporaryRoots: string[] = [];

afterEach(() => {
  for (const path of temporaryRoots.splice(0)) rmSync(path, { recursive: true, force: true });
});

function temporaryRoot(): string {
  const path = mkdtempSync(join(tmpdir(), "perfect-seed-factory-test-"));
  temporaryRoots.push(path);
  return path;
}

function run(args: string[], cwd = ROOT) {
  return Bun.spawnSync(["bun", "run", CLI, ...args], { cwd, stdout: "pipe", stderr: "pipe" });
}

const VALID_SOURCE_REFS = [
  {
    repo: "ts-skill-bettor",
    commit: "f3776cbf1b4c75c78e017e1381a8517cd1865abf",
    path: "AGENTS.md",
    anchor: "L20:重複組件禁字面推論等價",
  },
];

function writePacket(
  root: string,
  sourceKind: string,
  sourcePath: string,
  sourceRefs: unknown = VALID_SOURCE_REFS,
): string {
  const packet = join(root, `${sourceKind}.json`);
  writeFileSync(
    packet,
    JSON.stringify(
      {
        schema_version: "perfect-seed-input@1.0.0",
        packet_id: `fixture-${sourceKind}`,
        packet_state: "admitted",
        source_kind: sourceKind,
        source_path: sourcePath,
        task: "Design the smallest traceable repository and choose the next implementation action.",
        fixed_prompt_context: ["PROMPT.md", "modules/semantic-truth-context.md"],
        emergent_prompt_context: "N/A-none",
        human_gate: "required_before_seed_admit",
        ...(sourceRefs === null ? {} : { source_refs: sourceRefs }),
      },
      null,
      2,
    ) + "\n",
    "utf8",
  );
  return packet;
}

function fixturePeerRepo(root: string): { peer: string; commit: string } {
  const peer = join(root, "peer");
  mkdirSync(join(peer, "docs"), { recursive: true });
  writeFileSync(join(peer, "docs", "claim.md"), "claim body\n", "utf8");
  const git = (...gitArgs: string[]): string => {
    const result = Bun.spawnSync(["git", "-C", peer, ...gitArgs], { stdout: "pipe", stderr: "pipe" });
    if (result.exitCode !== 0) throw new Error(result.stderr.toString());
    return result.stdout.toString().trim();
  };
  git("init", "-q");
  git("add", "docs/claim.md");
  git("-c", "user.name=fixture", "-c", "user.email=fixture@test", "commit", "-qm", "fixture");
  return { peer, commit: git("rev-parse", "HEAD") };
}

describe("seed-factory build public seam", () => {
  for (const [kind, relativeSource] of [
    ["dr", "tests/fixtures/dr.md"],
    ["gcr", "tests/fixtures/gcr.md"],
    ["grill-me", "tests/fixtures/grill.md"],
    ["repo", "tests/fixtures/repo"],
  ] as const) {
    test(`materializes a runnable repo from ${kind}`, async () => {
      const temp = temporaryRoot();
      const packet = writePacket(temp, kind, join(ROOT, relativeSource));
      const output = join(temp, "generated");

      const built = run(["build", "--packet", packet, "--output", output]);
      expect(built.exitCode, built.stderr.toString()).toBe(0);
      expect(readFileSync(join(output, ".agents/skills/seed-repo-operator/SKILL.md"), "utf8")).toContain(
        "seed-repo-operator",
      );
      expect(readFileSync(join(output, "data/source.json"), "utf8")).toContain(`"source_kind": "${kind}"`);

      const planned = Bun.spawnSync(["bun", "run", "scripts/plan.ts", "--task", "Choose a safe implementation slice"], {
        cwd: output,
        stdout: "pipe",
        stderr: "pipe",
      });
      expect(planned.exitCode, planned.stderr.toString()).toBe(0);
      const callPlan = JSON.parse(readFileSync(join(output, "data/call-plan.json"), "utf8"));
      const results = readFileSync(join(output, "data/call-results.jsonl"), "utf8")
        .trim()
        .split("\n")
        .map((line) => JSON.parse(line));
      expect(callPlan.calls).toHaveLength(20);
      expect(results).toHaveLength(20);
      expect(new Set(results.map((entry: { call_id: string }) => entry.call_id)).size).toBe(20);
      for (const call of callPlan.calls) {
        const position = callPlan.calls.findIndex((entry: { call_id: string }) => entry.call_id === call.call_id);
        for (const dependency of call.depends_on) {
          expect(callPlan.calls.findIndex((entry: { call_id: string }) => entry.call_id === dependency)).toBeLessThan(
            position,
          );
        }
      }

      const generatedTests = Bun.spawnSync(["bun", "test"], { cwd: output, stdout: "pipe", stderr: "pipe" });
      expect(generatedTests.exitCode, generatedTests.stderr.toString()).toBe(0);
    });
  }

  test("rejects an unknown source kind", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "web", join(ROOT, "tests/fixtures/dr.md"));
    const result = run(["build", "--packet", packet, "--output", join(temp, "generated")]);
    expect(result.exitCode).not.toBe(0);
    expect(result.stderr.toString()).toContain("unsupported source_kind");
  });

  test("does not overwrite an existing output", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const output = join(temp, "generated");
    expect(run(["build", "--packet", packet, "--output", output]).exitCode).toBe(0);
    const second = run(["build", "--packet", packet, "--output", output]);
    expect(second.exitCode).not.toBe(0);
    expect(second.stderr.toString()).toContain("output already exists");
  });

  test("rejects an unsafe output path before materialization", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const result = run(["build", "--packet", packet, "--output", `${temp}/unsafe"output`]);
    expect(result.exitCode).not.toBe(0);
    expect(result.stderr.toString()).toContain("output path contains unsafe characters");
  });

  test("rejects an artifact manifest path that escapes the generated repo", async () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const output = join(temp, "generated");
    const built = run(["build", "--packet", packet, "--output", output]);
    expect(built.exitCode, built.stderr.toString()).toBe(0);
    const planned = Bun.spawnSync(["bun", "run", "scripts/plan.ts", "--task", "Audit manifest path confinement"], {
      cwd: output,
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(planned.exitCode, planned.stderr.toString()).toBe(0);
    const manifestPath = join(output, "data/artifact-manifest.json");
    const receiptPath = join(output, "data/build-receipt.json");
    const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
    manifest.files[0].path = "../escape";
    const manifestBytes = `${JSON.stringify(manifest, null, 2)}\n`;
    await Bun.write(manifestPath, manifestBytes);
    const receipt = JSON.parse(readFileSync(receiptPath, "utf8"));
    receipt.artifact_manifest_sha256 = new Bun.CryptoHasher("sha256").update(manifestBytes).digest("hex");
    await Bun.write(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`);
    const verified = Bun.spawnSync(["bun", "run", GENERATED_REPO_VERIFIER, "--repo", output], {
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(verified.exitCode).not.toBe(0);
    expect(verified.stderr.toString()).toContain("manifest path escapes repo");
  });

  test("minimum-lineage gate accepts a fresh repo and rejects one-byte template drift", async () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const output = join(temp, "generated");
    const built = run(["build", "--packet", packet, "--output", output]);
    expect(built.exitCode, built.stderr.toString()).toBe(0);

    const fresh = Bun.spawnSync(["bun", "run", MINIMUM_LINEAGE_CLI, "--repo", output], {
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(fresh.exitCode, fresh.stderr.toString()).toBe(0);

    const agentsPath = join(output, "AGENTS.md");
    const agentsBytes = readFileSync(agentsPath, "utf8");
    await Bun.write(agentsPath, `${agentsBytes.startsWith("#") ? "!" : "#"}${agentsBytes.slice(1)}`);
    const drifted = Bun.spawnSync(["bun", "run", MINIMUM_LINEAGE_CLI, "--repo", output], {
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(drifted.exitCode).not.toBe(0);
    expect(drifted.stderr.toString()).toContain("minimum-lineage hash drift: AGENTS.md");
  });

  test("generated repo exposes a local fail-fast quality gate", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const output = join(temp, "generated");
    const built = run(["build", "--packet", packet, "--output", output]);
    expect(built.exitCode, built.stderr.toString()).toBe(0);
    symlinkSync(join(ROOT, "node_modules"), join(output, "node_modules"), "dir");

    const checked = Bun.spawnSync(["bun", "run", "quality:fast"], {
      cwd: output,
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(checked.exitCode, `${checked.stdout.toString()}\n${checked.stderr.toString()}`).toBe(0);
    expect(checked.stdout.toString()).toContain("perfect-seed-minimum-lineage-result@1.0.0");
  });

  test("generated quality gate detects format, lint, and type defects at their physical stages", async () => {
    const defects = [
      {
        id: "format",
        source: "export const badlyFormatted={value:1}\n",
        expected: "Code style issues found",
        forbiddenLaterCommand: "$ eslint .",
      },
      {
        id: "lint",
        source: "export const explicitAny: any = 1;\n",
        expected: "@typescript-eslint/no-explicit-any",
        forbiddenLaterCommand: "$ tsc --project tsconfig.json --noEmit",
      },
      {
        id: "type",
        source: 'export const wrongType: number = "not-a-number";\n',
        expected: "Type 'string' is not assignable to type 'number'",
        forbiddenLaterCommand: "N/A-final-stage",
      },
    ] as const;

    for (const defect of defects) {
      const temp = temporaryRoot();
      const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
      const output = join(temp, "generated");
      const built = run(["build", "--packet", packet, "--output", output]);
      expect(built.exitCode, built.stderr.toString()).toBe(0);
      symlinkSync(join(ROOT, "node_modules"), join(output, "node_modules"), "dir");
      await Bun.write(join(output, "src", `hollow-${defect.id}.ts`), defect.source);

      const checked = Bun.spawnSync(["bun", "run", "quality:fast"], {
        cwd: output,
        stdout: "pipe",
        stderr: "pipe",
      });
      const transcript = `${checked.stdout.toString()}\n${checked.stderr.toString()}`;
      expect(checked.exitCode).not.toBe(0);
      expect(transcript).toContain("perfect-seed-minimum-lineage-result@1.0.0");
      expect(transcript).toContain(defect.expected);
      if (defect.forbiddenLaterCommand !== "N/A-final-stage") {
        expect(transcript).not.toContain(defect.forbiddenLaterCommand);
      }
    }
  });

  test("factory fast gate writes a preflight-only receipt in fail-fast order", () => {
    const temp = temporaryRoot();
    const receiptPath = join(temp, "fast-quality.receipt.json");
    const checked = Bun.spawnSync(["bun", "run", FAST_QUALITY_CLI, "--output", receiptPath], {
      cwd: ROOT,
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(checked.exitCode, `${checked.stdout.toString()}\n${checked.stderr.toString()}`).toBe(0);
    const receipt = JSON.parse(readFileSync(receiptPath, "utf8"));
    expect(receipt).toMatchObject({
      schema_version: "perfect-seed-fast-quality-receipt@1.0.0",
      status: "passed",
      claim_boundary: "preflight-only-not-code-quality-axis",
    });
    expect(receipt.stages.map((stage: { id: string }) => stage.id)).toEqual([
      "minimum-lineage",
      "format",
      "lint",
      "typecheck",
    ]);
    expect(
      receipt.stages.every(
        (stage: { status: string; exit_code: number }) => stage.status === "passed" && stage.exit_code === 0,
      ),
    ).toBe(true);
  });

  test("rejects a packet without source_refs", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"), null);
    const result = run(["validate", "--packet", packet]);
    expect(result.exitCode).toBe(1);
    expect(result.stderr.toString()).toContain("source_refs");
  });

  test("rejects malformed source_refs shapes", () => {
    const temp = temporaryRoot();
    const badShapes: unknown[] = [
      [],
      [{ repo: "r", commit: "not-hex", path: "a/b.md", anchor: "L1" }],
      [{ repo: "r", commit: "abcdef0", path: "/absolute/path.md", anchor: "L1" }],
      [{ repo: "r", commit: "abcdef0", path: "a/../escape.md", anchor: "L1" }],
      [{ repo: "r", commit: "abcdef0", path: "a/b.md" }],
      [{ repo: "", commit: "abcdef0", path: "a/b.md", anchor: "L1" }],
    ];
    for (const refs of badShapes) {
      const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"), refs);
      const result = run(["validate", "--packet", packet]);
      expect(result.exitCode, JSON.stringify(refs)).toBe(1);
      expect(result.stderr.toString()).toContain("source_refs");
    }
  });

  test("resolve-refs without --peer reports NOT_RUN with exit 2", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const result = run(["resolve-refs", "--packet", packet]);
    expect(result.exitCode).toBe(2);
    expect(result.stdout.toString()).toContain("NOT_RUN");
    expect(result.stdout.toString()).not.toContain("PASS");
  });

  test("resolve-refs audits commit existence and tracked path against an explicit peer", () => {
    const temp = temporaryRoot();
    const { peer, commit } = fixturePeerRepo(temp);

    const good = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"), [
      { repo: "peer", commit, path: "docs/claim.md", anchor: "L1" },
    ]);
    const passed = run(["resolve-refs", "--packet", good, "--peer", peer]);
    expect(passed.exitCode, passed.stderr.toString()).toBe(0);
    expect(passed.stdout.toString()).toContain("PASS");

    const untracked = writePacket(temp, "gcr", join(ROOT, "tests/fixtures/gcr.md"), [
      { repo: "peer", commit, path: "docs/missing.md", anchor: "L1" },
    ]);
    const failedPath = run(["resolve-refs", "--packet", untracked, "--peer", peer]);
    expect(failedPath.exitCode).toBe(1);
    expect(failedPath.stderr.toString()).toContain("not tracked");

    const badCommit = writePacket(temp, "grill-me", join(ROOT, "tests/fixtures/grill.md"), [
      { repo: "peer", commit: "deadbeef00", path: "docs/claim.md", anchor: "L1" },
    ]);
    const failedCommit = run(["resolve-refs", "--packet", badCommit, "--peer", peer]);
    expect(failedCommit.exitCode).toBe(1);
    expect(failedCommit.stderr.toString()).toContain("commit");
  });

  test("build carries source_refs through the reduced IR into the lineage manifest", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const output = join(temp, "generated");
    const built = run(["build", "--packet", packet, "--output", output]);
    expect(built.exitCode, built.stderr.toString()).toBe(0);
    const source = JSON.parse(readFileSync(join(output, "data/source.json"), "utf8"));
    const lineage = JSON.parse(readFileSync(join(output, "data/lineage.json"), "utf8"));
    expect(source.source_refs).toEqual(VALID_SOURCE_REFS);
    expect(lineage.source_refs).toEqual(VALID_SOURCE_REFS);
    expect(lineage.refs_grounded).toBe(true);
    expect(lineage.terminal_human_gate).toBe("required_before_seed_admit");
  });

  test("migrated legacy packet builds with sentinel refs and refs_grounded false", () => {
    const temp = temporaryRoot();
    const migrated = join(temp, "migrated.json");
    const migratedRun = Bun.spawnSync(
      [
        "bun",
        "run",
        join(ROOT, "src", "migrate_packet.ts"),
        "--input",
        join(ROOT, "packets", "inbox", "legacy-dr-example.json"),
        "--output",
        migrated,
      ],
      { stdout: "pipe", stderr: "pipe" },
    );
    expect(migratedRun.exitCode, migratedRun.stderr.toString()).toBe(0);
    const value = JSON.parse(readFileSync(migrated, "utf8"));
    expect(value.source_refs).toEqual([
      { repo: "unknown", commit: "0000000", path: "unmigrated/unknown", anchor: "pre-source-refs" },
    ]);
    const output = join(temp, "generated");
    const built = run(["build", "--packet", migrated, "--output", output]);
    expect(built.exitCode, built.stderr.toString()).toBe(0);
    const lineage = JSON.parse(readFileSync(join(output, "data/lineage.json"), "utf8"));
    expect(lineage.refs_grounded).toBe(false);
  });

  test("generated repo verifier rejects a lineage stripped of source_refs", async () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const output = join(temp, "generated");
    const built = run(["build", "--packet", packet, "--output", output]);
    expect(built.exitCode, built.stderr.toString()).toBe(0);
    const planned = Bun.spawnSync(["bun", "run", "scripts/plan.ts", "--task", "Audit lineage source_refs binding"], {
      cwd: output,
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(planned.exitCode, planned.stderr.toString()).toBe(0);

    const sha256 = (value: string): string => new Bun.CryptoHasher("sha256").update(value).digest("hex");
    const lineagePath = join(output, "data/lineage.json");
    const lineage = JSON.parse(readFileSync(lineagePath, "utf8"));
    delete lineage.source_refs;
    const lineageBytes = `${JSON.stringify(lineage, null, 2)}\n`;
    await Bun.write(lineagePath, lineageBytes);
    const manifestPath = join(output, "data/artifact-manifest.json");
    const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
    const entry = manifest.files.find((file: { path: string }) => file.path === "data/lineage.json");
    entry.sha256 = sha256(lineageBytes);
    entry.bytes = Buffer.byteLength(lineageBytes);
    const manifestBytes = `${JSON.stringify(manifest, null, 2)}\n`;
    await Bun.write(manifestPath, manifestBytes);
    const receiptPath = join(output, "data/build-receipt.json");
    const receipt = JSON.parse(readFileSync(receiptPath, "utf8"));
    receipt.artifact_manifest_sha256 = sha256(manifestBytes);
    await Bun.write(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`);

    const verified = Bun.spawnSync(["bun", "run", GENERATED_REPO_VERIFIER, "--repo", output], {
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(verified.exitCode).not.toBe(0);
    expect(verified.stderr.toString()).toContain("source_refs");
  });

  test("generated fast gate never removes a pre-existing local dependency symlink", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const output = join(temp, "generated");
    const built = run(["build", "--packet", packet, "--output", output]);
    expect(built.exitCode, built.stderr.toString()).toBe(0);
    const existingModules = join(temp, "existing-node-modules");
    mkdirSync(existingModules);
    writeFileSync(join(existingModules, "sentinel"), "owned-by-caller\n", "utf8");
    const localModules = join(output, "node_modules");
    symlinkSync(existingModules, localModules, "dir");

    const checked = Bun.spawnSync(["bun", "run", GENERATED_FAST_QUALITY_CLI, "--repo", output], {
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(checked.exitCode).not.toBe(0);
    expect(checked.stderr.toString()).toContain("generated repo node_modules must be absent");
    expect(existsSync(localModules)).toBe(true);
    expect(readFileSync(join(localModules, "sentinel"), "utf8")).toBe("owned-by-caller\n");
  });
});
