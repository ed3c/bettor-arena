import { afterEach, describe, expect, test } from "bun:test";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
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
    const receipt = JSON.parse(readFileSync(`${good}.resolve-receipt.json`, "utf8"));
    expect(receipt).toMatchObject({
      schema_version: "perfect-seed-resolve-receipt@1.0.0",
      packet_id: "fixture-dr",
      refs_status: "resolved",
      peer,
      ref_count: 1,
    });
    expect(receipt.packet_sha256).toBe(new Bun.CryptoHasher("sha256").update(readFileSync(good)).digest("hex"));

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
    expect(source.refs_status).toBe("declared");
    expect(lineage.refs_status).toBe("declared");
    expect(lineage.terminal_human_gate).toBe("required_before_seed_admit");
  });

  test("refs-status reports declared for shape-valid refs and sentinel for migrated placeholders", () => {
    const temp = temporaryRoot();
    const declared = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const declaredRun = run(["refs-status", "--packet", declared]);
    expect(declaredRun.exitCode, declaredRun.stderr.toString()).toBe(0);
    const declaredJson = JSON.parse(declaredRun.stdout.toString());
    expect(declaredJson).toMatchObject({
      schema_version: "perfect-seed-refs-status@1.0.0",
      packet_id: "fixture-dr",
      refs_status: "declared",
    });
    expect(declaredJson.source_refs).toEqual(VALID_SOURCE_REFS);

    const sentinel = writePacket(temp, "gcr", join(ROOT, "tests/fixtures/gcr.md"), [
      { repo: "unknown", commit: "0000000", path: "unmigrated/unknown", anchor: "pre-source-refs" },
    ]);
    const sentinelRun = run(["refs-status", "--packet", sentinel]);
    expect(sentinelRun.exitCode, sentinelRun.stderr.toString()).toBe(0);
    expect(JSON.parse(sentinelRun.stdout.toString()).refs_status).toBe("sentinel");
  });

  test("resolved status is granted only by a receipt bound to the audited packet bytes", () => {
    const temp = temporaryRoot();
    const { peer, commit } = fixturePeerRepo(temp);
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"), [
      { repo: "peer", commit, path: "docs/claim.md", anchor: "L1" },
    ]);
    expect(run(["resolve-refs", "--packet", packet, "--peer", peer]).exitCode).toBe(0);
    expect(JSON.parse(run(["refs-status", "--packet", packet]).stdout.toString()).refs_status).toBe("resolved");

    const output = join(temp, "generated");
    const built = run(["build", "--packet", packet, "--output", output]);
    expect(built.exitCode, built.stderr.toString()).toBe(0);
    const lineage = JSON.parse(readFileSync(join(output, "data/lineage.json"), "utf8"));
    expect(lineage.refs_status).toBe("resolved");

    // Tampering the packet after the audit invalidates the receipt binding —
    // and the break must read "stale", not blend into never-audited "declared".
    writeFileSync(packet, `${readFileSync(packet, "utf8").replace("N/A-none", "tampered-after-audit")}`, "utf8");
    expect(JSON.parse(run(["refs-status", "--packet", packet]).stdout.toString()).refs_status).toBe("stale");

    // The stale state survives into the built lineage the human gate reads.
    const staleOutput = join(temp, "generated-stale");
    const staleBuilt = run(["build", "--packet", packet, "--output", staleOutput]);
    expect(staleBuilt.exitCode, staleBuilt.stderr.toString()).toBe(0);
    expect(JSON.parse(readFileSync(join(staleOutput, "data/lineage.json"), "utf8")).refs_status).toBe("stale");
    const stalePlanned = Bun.spawnSync(["bun", "run", "scripts/plan.ts", "--task", "Audit stale refs at the gate"], {
      cwd: staleOutput,
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(stalePlanned.exitCode, stalePlanned.stderr.toString()).toBe(0);
    const staleVerified = Bun.spawnSync(["bun", "run", GENERATED_REPO_VERIFIER, "--repo", staleOutput], {
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(staleVerified.exitCode, staleVerified.stderr.toString()).toBe(0);
  });

  test("a receipt missing its binding fields reads stale, never declared or resolved", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    writeFileSync(
      `${packet}.resolve-receipt.json`,
      `${JSON.stringify({ schema_version: "perfect-seed-resolve-receipt@1.0.0" })}\n`,
      "utf8",
    );
    const result = run(["refs-status", "--packet", packet]);
    expect(result.exitCode, result.stderr.toString()).toBe(0);
    expect(JSON.parse(result.stdout.toString()).refs_status).toBe("stale");
  });

  test("a corrupted receipt fails the check with exit 2 and a named diagnostic", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    writeFileSync(`${packet}.resolve-receipt.json`, "{not json", "utf8");
    const result = run(["refs-status", "--packet", packet]);
    expect(result.exitCode).toBe(2);
    const stderr = result.stderr.toString();
    expect(stderr).toContain("FAIL:");
    expect(stderr).toContain("resolve-receipt.json");
    expect(stderr).not.toContain("    at "); // no raw stack trace
  });

  test("a receipt under a foreign schema fails the check with exit 2, same taxonomy as corruption", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    writeFileSync(
      `${packet}.resolve-receipt.json`,
      `${JSON.stringify({ schema_version: "perfect-seed-resolve-receipt@9.9.9", refs_status: "resolved" })}\n`,
      "utf8",
    );
    const result = run(["refs-status", "--packet", packet]);
    expect(result.exitCode).toBe(2);
    expect(result.stderr.toString()).toContain("unsupported resolve receipt schema");
  });

  test("trigger rejects a stale refs_status by name, not as unrecognized", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    writeFileSync(
      `${packet}.resolve-receipt.json`,
      `${JSON.stringify({ schema_version: "perfect-seed-resolve-receipt@1.0.0", refs_status: "resolved", packet_sha256: "0".repeat(64) })}\n`,
      "utf8",
    );
    const result = Bun.spawnSync(["sh", join(ROOT, "trigger.sh"), packet, join(temp, "out")], {
      cwd: ROOT,
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(result.exitCode).toBe(2);
    const stderr = result.stderr.toString();
    expect(stderr).toContain("refs_status=stale");
    expect(stderr).not.toContain("unrecognized");
  });

  test("migrated legacy packet builds with sentinel refs and refs_status sentinel", () => {
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
    expect(lineage.refs_status).toBe("sentinel");
  });

  test("generated repo verifier rejects a source.json whose refs_status diverges from lineage", async () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const output = join(temp, "generated");
    const built = run(["build", "--packet", packet, "--output", output]);
    expect(built.exitCode, built.stderr.toString()).toBe(0);
    const planned = Bun.spawnSync(["bun", "run", "scripts/plan.ts", "--task", "Audit source refs_status binding"], {
      cwd: output,
      stdout: "pipe",
      stderr: "pipe",
    });
    expect(planned.exitCode, planned.stderr.toString()).toBe(0);

    const sha256 = (value: string): string => new Bun.CryptoHasher("sha256").update(value).digest("hex");
    const sourcePath = join(output, "data/source.json");
    const source = JSON.parse(readFileSync(sourcePath, "utf8"));
    source.refs_status = "resolved";
    const sourceBytes = `${JSON.stringify(source, null, 2)}\n`;
    await Bun.write(sourcePath, sourceBytes);
    const manifestPath = join(output, "data/artifact-manifest.json");
    const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
    const entry = manifest.files.find((file: { path: string }) => file.path === "data/source.json");
    entry.sha256 = sha256(sourceBytes);
    entry.bytes = Buffer.byteLength(sourceBytes);
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
    expect(verified.stderr.toString()).toContain("refs_status");
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

describe("wiki-update delivery terminus (ISSUE-23)", () => {
  const ARENA = resolve(ROOT, "..", "..");

  test("a successful trigger delivery emits a typed wiki-update request with the three context lanes", () => {
    const temp = temporaryRoot();
    const packet = writePacket(temp, "dr", join(ROOT, "tests/fixtures/dr.md"));
    const requestPath = join(ARENA, "data", "wiki-update", "request-fixture-dr.json");
    rmSync(requestPath, { force: true });
    try {
      const result = Bun.spawnSync(["sh", join(ROOT, "trigger.sh"), packet, join(temp, "out")], {
        cwd: ROOT,
        stdout: "pipe",
        stderr: "pipe",
      });
      expect(result.exitCode, result.stderr.toString()).toBe(0);
      // Negative control the slice exists for: delivery succeeded but the
      // request artifact is absent — that must be caught, not assumed away.
      expect(existsSync(requestPath)).toBe(true);
      const request = JSON.parse(readFileSync(requestPath, "utf8"));
      expect(request.schema_version).toBe("bettor-arena-wiki-update-request@1.0.0");
      expect(request.packet_id).toBe("fixture-dr");
      expect(request.git_head).toMatch(/^[0-9a-f]{40}$/);
      expect(request.request_id).toBe(`fixture-dr@${request.git_head}`);
      expect(request.route_result.build_exit).toBe(0);
      expect(request.route_result.validator_exit).toBe(0);
      expect(request.route_result.path).toBe(
        "loop_wiki/evolve-perfect-seed-repo-factory/packets/outbox/route-result.fixture-dr.json",
      );
      // fixed lane: pointers only, never copied prompt content.
      expect(request.fixed_prompt_context).toEqual([
        "kb-ingest/openwiki/update.system.md",
        "kb-ingest/openwiki/user.update.md",
        "kb-ingest/port/host-runtime.md",
      ]);
      // iteration lane: deterministic delta, with absence as a named state.
      const delta = request.iteration_auto_context;
      expect(["computed", "no-last-update", "unresolvable-last-head"]).toContain(delta.delta_status);
      expect(Array.isArray(delta.changed_files)).toBe(true);
      if (delta.delta_status === "computed") expect(delta.last_update_git_head).toMatch(/^[0-9a-f]{40}$/);
      // emergent lane: a pointer to the openwiki-native backlog, nothing inline.
      expect(request.emergent_prompt_context).toBe("openwiki/quickstart.md#backlog");
    } finally {
      rmSync(requestPath, { force: true });
    }
  }, 180000);

  test("standards modules carry zero emergent content — emergent lands only in the openwiki backlog", () => {
    const EMERGENT = /emergent_observation|wiki[-_]update|##\s*Backlog/i;
    // Positive control: prove the matcher can go red before trusting its green.
    expect(EMERGENT.test("## Backlog\n- drift observed during generation")).toBe(true);

    const markdownFilesUnder = (dir: string): string[] =>
      readdirSync(dir).flatMap((name) => {
        const path = join(dir, name);
        if (statSync(path).isDirectory()) return markdownFilesUnder(path);
        return name.endsWith(".md") ? [path] : [];
      });
    const files = [
      ...markdownFilesUnder(join(ROOT, "modules")),
      ...markdownFilesUnder(join(ROOT, "templates", "repo")),
    ];
    expect(files.length).toBeGreaterThan(0);
    for (const file of files) {
      expect(EMERGENT.test(readFileSync(file, "utf8")), `emergent content leaked into ${file}`).toBe(false);
    }
  });
});
