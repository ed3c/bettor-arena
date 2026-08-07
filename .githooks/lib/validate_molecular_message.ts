#!/usr/bin/env bun
/**
 * validate_molecular_message — commit-msg gate for molecular commit messages.
 *
 * Charter (legislated responsibilities; the gate may do this and nothing else):
 *   READS ONLY: the commit message file named in argv, and this repo's
 *     `git diff --cached --name-only` (or an explicit --changed-paths-file).
 *   FORBIDDEN: imports from outside this file except `node:` builtins;
 *     repo-specific data paths inside the contract; reading sibling
 *     checkouts; any network access.
 *
 * Rebuilt from ts-skill-bettor loop_wiki/evolve-unknown-discovery-plan-truth/
 * adapters/typescript/runtime/scripts/validate_molecular_commit_message.ts
 * (source read-only). Kept core: subject shape, molecular trailer-block
 * structure, staged-consistency (protected surface requires molecular).
 *
 * Stripped UDPT-specific rules (each violated the charter above):
 *   S1 commit-verification-envelope trailer set (Verification-State,
 *      Code-Quality-*, Production-Use-*, Promotion-Eligible,
 *      Evidence-Manifest, Observed-Checks, Async-Run-Refs, Not-Measured,
 *      Measurement-As-Of) — required importing runtime/verification from
 *      outside the gate directory.
 *   S2 canonical Plan-Package/Small-Loop/Final-Repo absolute-path equality —
 *      repo-specific data paths in the contract.
 *   S3 "at least five absolute dataflow paths under repo root" —
 *      home-directory path coupling.
 *   S4 mandatory GCR source-conversation reference (absolute path into a
 *      sibling antigravity checkout).
 *   S5 mandatory ROUTES.md#plan-package-materialization and
 *      modules/exchange-formats.md literal references — repo-specific paths.
 *   S6 UDPT protected path list — retargeted to this repo's own control
 *      surface (.githooks/, scripts/gates/).
 *
 * Exit codes: 0 pass · 2 fail · 64 usage.
 */
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const REQUIRED_FIELDS = [
  "Intent-Slice:",
  "Route:",
  "Plan-Package:",
  "Small-Loop:",
  "Final-Repo:",
  "Exchange-Format:",
  "Exchange-Packet:",
  "Fixed-Prompt-Context:",
  "Iteration-Auto-Context:",
  "Emergent-Prompt-Context:",
  "Dataflow:",
] as const;

// S6: this repo's own gate/hook surface — changes here must be traceable.
const PROTECTED_PREFIXES = [".githooks/", "scripts/gates/"] as const;

// ADR 0001 amendment (2026-08-07, human ruling): Intent-Slice belongs to the
// small loop and nothing else. Touching a gate is not by itself a role — the
// large loop maintains this control surface too, and it has no slice to name.
// Demanding one there forces a fabricated issue number, which is worse than an
// untraceable commit: it points the lineage chain at the wrong intent.
const SMALL_LOOP_PREFIXES = ["loop_wiki/"] as const;

// Arena slice vocabulary (ADR 0001): Intent-Slice anchors the Forgejo issue
// tracker (ISSUE-<n>), the SSOT of this plan's intent chain. The source repo's
// prefixes (GCR-SLICE-/TS-SLICE-/...) were deliberately not imported — that
// would re-embed the source repo's topology this rebuild just stripped.
function isMolecularMessage(text: string): boolean {
  return /Intent-Slice:\s+ISSUE-\d+/.test(text);
}

export function validateText(text: string, requireMolecular = false): string[] {
  if (!isMolecularMessage(text)) {
    return requireMolecular
      ? ["protected gate surface requires a molecular commit message with a supported Intent-Slice"]
      : [];
  }

  const failures: string[] = [];
  const lines = text.split(/\r?\n/);
  if (!lines[0]?.trim()) failures.push("subject line must be non-empty");
  if (lines.length > 1 && lines[1]?.trim() !== "") {
    failures.push("subject must be separated from the molecular block by a blank line");
  }
  for (const field of REQUIRED_FIELDS) {
    if (!text.includes(field)) failures.push(`missing field: ${field}`);
  }
  const fixedIndex = text.indexOf("Fixed-Prompt-Context:");
  const iterationIndex = text.indexOf("Iteration-Auto-Context:");
  if (fixedIndex >= 0 && iterationIndex >= 0 && fixedIndex > iterationIndex) {
    failures.push("Fixed-Prompt-Context must appear before Iteration-Auto-Context");
  }
  return failures;
}

function stagedPaths(): string[] {
  const result = spawnSync("git", ["diff", "--cached", "--name-only"], { encoding: "utf8" });
  return result.status === 0 ? result.stdout.split(/\r?\n/).filter(Boolean) : [];
}

function hasPrefix(paths: string[], prefixes: readonly string[]): boolean {
  return paths.some((path) => prefixes.some((prefix) => path.startsWith(prefix)));
}

/** A gate change made by the small loop: the only role that has a slice to name. */
export function requiresMolecular(paths: string[]): boolean {
  return hasPrefix(paths, PROTECTED_PREFIXES) && hasPrefix(paths, SMALL_LOOP_PREFIXES);
}

function validateFile(path: string, requireMolecular: boolean): number {
  let text: string;
  try {
    text = readFileSync(path, "utf8");
  } catch {
    console.error(`FAIL: commit message file does not exist: ${path}`);
    return 2;
  }
  const failures = validateText(text, requireMolecular);
  if (failures.length > 0) {
    console.error("FAIL: molecular commit message contract failed");
    for (const failure of failures) console.error(failure);
    return 2;
  }
  console.log("PASS: molecular commit message contract");
  return 0;
}

function selftest(): number {
  const fail = (message: string): number => {
    console.error(`FAIL: ${message}`);
    return 2;
  };
  const ordinary = "Fix typo\n\nNo molecular lineage in this commit.\n";
  const good = `Add a gate

Intent-Slice: ISSUE-3
Route: docs/routes.md#gate
Plan-Package: docs/plan-package.yaml
Small-Loop: loop_wiki/some-loop/
Final-Repo: repo/
Exchange-Format: docs/exchange-format.md
Exchange-Packet: docs/packet.yaml
Fixed-Prompt-Context: docs/prompt.md
Iteration-Auto-Context: docs/iteration.md
Emergent-Prompt-Context: docs/emergent.md
Dataflow:
docs/plan-package.yaml
  -> repo/
`;
  if (validateText(ordinary).length > 0) return fail("ordinary message should pass without molecular fields");
  if (validateText(ordinary, true).length === 0) return fail("protected surface must reject an ordinary message");
  if (validateText(good).length > 0) return fail("good molecular message did not validate");
  if (validateText(good, true).length > 0) return fail("good molecular message must satisfy protected surface");
  const hollow = "Add a gate\n\nIntent-Slice: ISSUE-10\nRoute: docs/routes.md\n";
  if (validateText(hollow).length === 0) return fail("hollow molecular message unexpectedly validated");
  const swapped = good
    .replace("Fixed-Prompt-Context: docs/prompt.md", "MOVED")
    .replace(
      "Iteration-Auto-Context: docs/iteration.md",
      "Iteration-Auto-Context: docs/iteration.md\nFixed-Prompt-Context: docs/prompt.md",
    )
    .replace("MOVED\n", "");
  if (!validateText(swapped).some((f) => f.includes("must appear before"))) {
    return fail("swapped context ordering unexpectedly validated");
  }
  const noBlank = good.replace("Add a gate\n\n", "Add a gate\n");
  if (!validateText(noBlank).some((f) => f.includes("blank line"))) {
    return fail("missing subject separator unexpectedly validated");
  }
  if (validateText("Intent-Slice: TS-SLICE-01\n", true).length === 0) {
    return fail("source-repo vocabulary (deliberately unsupported) unexpectedly satisfied protected surface");
  }
  // role filter (ADR 0001 amendment): the slice, not the file, decides
  if (!requiresMolecular(["scripts/gates/x.py", "loop_wiki/some-loop/run.sh"])) {
    return fail("small loop touching a gate must require a slice");
  }
  if (requiresMolecular(["scripts/gates/x.py", "ARCHITECTURE.md"])) {
    return fail("large loop maintaining the gate surface has no slice to name");
  }
  if (requiresMolecular(["loop_wiki/some-loop/run.sh"])) {
    return fail("small loop that leaves the control surface alone is not a gate change");
  }
  if (requiresMolecular(["README.md"])) {
    return fail("ordinary edit must not require a slice");
  }
  console.log("PASS: selftest");
  return 0;
}

function main(argv: string[]): number {
  if (argv.length === 1 && argv[0] === "--selftest") return selftest();
  const args = [...argv];
  let changedPathsFile = "";
  const flag = args.indexOf("--changed-paths-file");
  if (flag >= 0) {
    changedPathsFile = args[flag + 1] ?? "";
    args.splice(flag, 2);
  }
  const messageFile = args[0];
  if (args.length !== 1 || !messageFile || (flag >= 0 && !changedPathsFile)) {
    console.error(
      `usage: validate_molecular_message.ts (--selftest | [--changed-paths-file <f>] <commit-msg-file>); got: ${argv.join(" ")}`,
    );
    return 64;
  }
  const paths = changedPathsFile
    ? readFileSync(changedPathsFile, "utf8").split(/\r?\n/).filter(Boolean)
    : stagedPaths();
  return validateFile(messageFile, requiresMolecular(paths));
}

process.exitCode = main(process.argv.slice(2));
