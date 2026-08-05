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

function writePacket(root: string, sourceKind: string, sourcePath: string): string {
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
      },
      null,
      2,
    ) + "\n",
    "utf8",
  );
  return packet;
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
