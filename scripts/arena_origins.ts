#!/usr/bin/env bun
import { existsSync, mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import {
  EnvironmentContractError,
  ID,
  SHA40,
  closedObject,
  readJson,
  run,
  runGit,
  sha256Json,
  uniqueStrings,
  verifyDigest,
  withDigest,
  writeJson,
  type EvidenceState,
} from "./environment_types.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = resolve(HERE, "..");
const CONTRACT_SCHEMA = "bettor-arena/origin-contract/v1";
const RECEIPT_SCHEMA = "bettor-arena/origin-receipt/v1";
const EQUIVALENCE_SCHEMA = "bettor-arena/origin-equivalence/v1";
const STATUS_SCHEMA = "bettor-arena/origin-status/v1";
const MODES = ["exact-commit", "same-tree", "same-release-manifest"] as const;
type EquivalenceMode = (typeof MODES)[number];

type OriginRole = "authoring" | "distribution";
interface Origin {
  id: string;
  role: OriginRole;
  scopes: string[];
  repository: string;
  live_probe: "ci" | "host-only";
}
interface OriginContract {
  schema: typeof CONTRACT_SCHEMA;
  logical_source: string;
  release_manifest: string;
  accepted_equivalence: EquivalenceMode[];
  origins: Origin[];
}
interface OriginReceipt {
  schema: typeof RECEIPT_SCHEMA;
  logical_source: string;
  origin: Pick<Origin, "id" | "role" | "repository" | "scopes">;
  status: Exclude<EvidenceState, "NOT_IMPLEMENTED">;
  subject: null | {
    commit: string;
    tree: string;
    release_manifest: string;
    release_manifest_sha256: string;
  };
  note: string;
  content_sha256: string;
}
interface EquivalenceReceipt {
  schema: typeof EQUIVALENCE_SCHEMA;
  logical_source: string;
  status: "PASS" | "FAIL" | "NOT_EXERCISED";
  mode: EquivalenceMode | null;
  origins: string[];
  subject: Record<string, string> | null;
  note: string;
  content_sha256: string;
}

function portableRelative(path: string, label: string): string {
  if (!path || isAbsolute(path)) throw new EnvironmentContractError(`${label}: repo-relative path required`);
  const normalized = path.replaceAll("\\", "/").replace(/^\.\//, "");
  const parts = normalized.split("/");
  if (!normalized || parts.some((part) => !part || part === ".."))
    throw new EnvironmentContractError(`${label}: path escape`);
  return normalized;
}

export function validateContract(value: unknown, options: { allowLocalRepositories?: boolean } = {}): OriginContract {
  closedObject(
    value,
    ["schema", "logical_source", "release_manifest", "accepted_equivalence", "origins"],
    "origin contract",
  );
  if (value.schema !== CONTRACT_SCHEMA)
    throw new EnvironmentContractError(`origin contract: schema must be ${CONTRACT_SCHEMA}`);
  if (typeof value.logical_source !== "string" || !value.logical_source.trim())
    throw new EnvironmentContractError("origin contract: logical_source required");
  const releaseManifest = portableRelative(String(value.release_manifest), "origin contract.release_manifest");
  const accepted = uniqueStrings(
    value.accepted_equivalence,
    "origin contract.accepted_equivalence",
  ) as EquivalenceMode[];
  if (!accepted.length || accepted.some((mode) => !MODES.includes(mode)))
    throw new EnvironmentContractError("origin contract: unsupported equivalence mode");
  if (!Array.isArray(value.origins) || value.origins.length !== 2)
    throw new EnvironmentContractError("origin contract: exactly two origins required for MVP");
  const ids = new Set<string>();
  const roles = new Set<string>();
  const origins = value.origins.map((item, index) => {
    closedObject(item, ["id", "role", "scopes", "repository", "live_probe"], `origin[${index}]`);
    if (typeof item.id !== "string" || !ID.test(item.id) || ids.has(item.id))
      throw new EnvironmentContractError(`origin[${index}]: invalid or duplicate id`);
    ids.add(item.id);
    if (item.role !== "authoring" && item.role !== "distribution")
      throw new EnvironmentContractError(`origin ${item.id}: invalid role`);
    if (roles.has(item.role)) throw new EnvironmentContractError(`origin contract: duplicate role ${item.role}`);
    roles.add(item.role);
    const scopes = uniqueStrings(item.scopes, `origin ${item.id}.scopes`);
    if (!scopes.includes("promotion") || scopes.some((scope) => !["local", "cloud", "promotion"].includes(scope))) {
      throw new EnvironmentContractError(`origin ${item.id}: scopes must include promotion and use known values`);
    }
    if (typeof item.repository !== "string" || !item.repository.trim())
      throw new EnvironmentContractError(`origin ${item.id}: repository required`);
    const repository = item.repository;
    const isLocalPath = isAbsolute(repository) || repository.startsWith("file://");
    if (isLocalPath && !options.allowLocalRepositories)
      throw new EnvironmentContractError(`origin ${item.id}: local path is not a versioned repository identity`);
    if (!isLocalPath) {
      let url: URL;
      try {
        url = new URL(repository);
      } catch {
        throw new EnvironmentContractError(`origin ${item.id}: repository must be a URL`);
      }
      if (url.username || url.password)
        throw new EnvironmentContractError(`origin ${item.id}: credentials are forbidden in repository URL`);
      if (url.hostname === "localhost" && item.role !== "authoring")
        throw new EnvironmentContractError("localhost may only be the local authoring origin");
    }
    if (item.role === "distribution") {
      if (!scopes.includes("cloud") || item.live_probe !== "ci")
        throw new EnvironmentContractError("distribution origin must be cloud-scoped and CI-probed");
    } else if (!scopes.includes("local") || item.live_probe !== "host-only") {
      throw new EnvironmentContractError("authoring origin must be local-scoped and host-only");
    }
    return { id: item.id, role: item.role, scopes, repository, live_probe: item.live_probe } as Origin;
  });
  if (!roles.has("authoring") || !roles.has("distribution"))
    throw new EnvironmentContractError("origin contract requires authoring and distribution roles");
  return {
    schema: CONTRACT_SCHEMA,
    logical_source: value.logical_source,
    release_manifest: releaseManifest,
    accepted_equivalence: accepted,
    origins,
  };
}

export function loadContract(root: string, allowLocalRepositories = false): OriginContract {
  return validateContract(readJson(join(root, ".arena/origins/release.json")), { allowLocalRepositories });
}

function manifestDigest(text: string, label: string): string {
  try {
    return sha256Json(JSON.parse(text));
  } catch {
    throw new EnvironmentContractError(`${label}: release manifest is not JSON`);
  }
}

function fetchSubject(repository: string, commit: string, manifestPath: string): OriginReceipt["subject"] {
  if (!SHA40.test(commit))
    throw new EnvironmentContractError("origin probe requires an exact 40-hex commit, never main/HEAD");
  const temp = mkdtempSync(join(tmpdir(), "bettor-origin-probe-"));
  try {
    run("git", ["init", "-q", temp]);
    runGit(temp, ["fetch", "--no-tags", "--depth=1", repository, commit]);
    const actual = runGit(temp, ["rev-parse", "FETCH_HEAD"]);
    if (actual !== commit) throw new EnvironmentContractError(`origin returned ${actual}, expected ${commit}`);
    const tree = runGit(temp, ["rev-parse", "FETCH_HEAD^{tree}"]);
    const manifest = runGit(temp, ["show", `FETCH_HEAD:${manifestPath}`]);
    return {
      commit,
      tree,
      release_manifest: manifestPath,
      release_manifest_sha256: manifestDigest(manifest, repository),
    };
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
}

export function probeOrigin(contract: OriginContract, originId: string, commit: string): OriginReceipt {
  const origin = contract.origins.find((candidate) => candidate.id === originId);
  if (!origin) throw new EnvironmentContractError(`unknown origin: ${originId}`);
  try {
    const subject = fetchSubject(origin.repository, commit, contract.release_manifest);
    return withDigest({
      schema: RECEIPT_SCHEMA,
      logical_source: contract.logical_source,
      origin: { id: origin.id, role: origin.role, repository: origin.repository, scopes: origin.scopes },
      status: "PASS",
      subject,
      note: "Exact commit, tree, and release-manifest bytes were fetched from this origin.",
    }) as OriginReceipt;
  } catch (error) {
    return withDigest({
      schema: RECEIPT_SCHEMA,
      logical_source: contract.logical_source,
      origin: { id: origin.id, role: origin.role, repository: origin.repository, scopes: origin.scopes },
      status: SHA40.test(commit) ? "FAIL" : "ABSENT",
      subject: null,
      note: String(error instanceof Error ? error.message : error),
    }) as OriginReceipt;
  }
}

function validateReceipt(receipt: OriginReceipt, label: string): void {
  if (receipt.schema !== RECEIPT_SCHEMA) throw new EnvironmentContractError(`${label}: wrong schema`);
  verifyDigest(receipt as unknown as Record<string, unknown>, label);
  if (receipt.status === "PASS") {
    if (!receipt.subject || !SHA40.test(receipt.subject.commit) || !SHA40.test(receipt.subject.tree))
      throw new EnvironmentContractError(`${label}: PASS lacks exact Git subject`);
  } else if (receipt.subject !== null)
    throw new EnvironmentContractError(`${label}: non-PASS receipt carries a fake subject`);
}

export function compareOrigins(contract: OriginContract, receipts: OriginReceipt[]): EquivalenceReceipt {
  if (receipts.length !== 2) throw new EnvironmentContractError("equivalence requires exactly two origin receipts");
  receipts.forEach((receipt, index) => validateReceipt(receipt, `origin receipt ${index}`));
  if (receipts.some((receipt) => receipt.status !== "PASS")) {
    return withDigest({
      schema: EQUIVALENCE_SCHEMA,
      logical_source: contract.logical_source,
      status: "NOT_EXERCISED",
      mode: null,
      origins: receipts.map((receipt) => receipt.origin.id).sort(),
      subject: null,
      note: "Two PASS receipts are required; one origin cannot prove the other.",
    }) as EquivalenceReceipt;
  }
  if (
    new Set(receipts.map((receipt) => receipt.origin.id)).size !== 2 ||
    new Set(receipts.map((receipt) => receipt.origin.role)).size !== 2
  ) {
    throw new EnvironmentContractError("equivalence receipts must represent distinct origins and roles");
  }
  if (receipts.some((receipt) => receipt.logical_source !== contract.logical_source))
    throw new EnvironmentContractError("equivalence logical source mismatch");
  const left = receipts[0]?.subject;
  const right = receipts[1]?.subject;
  if (!left || !right) throw new EnvironmentContractError("equivalence PASS receipts lost their immutable subjects");
  let mode: EquivalenceMode | null = null;
  let subject: Record<string, string> | null = null;
  if (left.commit === right.commit) {
    mode = "exact-commit";
    subject = { commit: left.commit };
  } else if (left.tree === right.tree) {
    mode = "same-tree";
    subject = { tree: left.tree };
  } else if (left.release_manifest_sha256 === right.release_manifest_sha256) {
    mode = "same-release-manifest";
    subject = { release_manifest_sha256: left.release_manifest_sha256 };
  }
  const accepted = mode !== null && contract.accepted_equivalence.includes(mode);
  return withDigest({
    schema: EQUIVALENCE_SCHEMA,
    logical_source: contract.logical_source,
    status: accepted ? "PASS" : "FAIL",
    mode,
    origins: receipts.map((receipt) => receipt.origin.id).sort(),
    subject,
    note: accepted ? `Origins agree by ${mode}.` : "Origins do not share an accepted immutable release subject.",
  }) as EquivalenceReceipt;
}

export function status(root: string): Record<string, unknown> & { content_sha256: string } {
  const contract = loadContract(root);
  const manifestPath = join(root, contract.release_manifest);
  if (!existsSync(manifestPath))
    throw new EnvironmentContractError(`release manifest absent: ${contract.release_manifest}`);
  const manifest = readJson(manifestPath);
  return withDigest({
    schema: STATUS_SCHEMA,
    logical_source: contract.logical_source,
    release_manifest: contract.release_manifest,
    release_manifest_sha256: sha256Json(manifest),
    offline_contract: "PASS",
    origins: contract.origins.map((origin) => ({
      id: origin.id,
      role: origin.role,
      scopes: origin.scopes,
      repository: origin.repository,
      live_state: "NOT_EXERCISED",
      note:
        origin.live_probe === "ci"
          ? "Requires an exact-head distribution probe."
          : "Requires a trusted local Forgejo host probe.",
    })),
    equivalence: { status: "NOT_EXERCISED", mode: null, note: "Two PASS origin receipts are required." },
  });
}

function initRepo(path: string): void {
  mkdirSync(path, { recursive: true });
  run("git", ["init", "-q", path]);
  runGit(path, ["config", "user.name", "origin selftest"]);
  runGit(path, ["config", "user.email", "origin@example.invalid"]);
}

function commitAll(path: string, message: string, allowEmpty = false): string {
  runGit(path, ["add", "-A"]);
  runGit(path, ["commit", "-q", ...(allowEmpty ? ["--allow-empty"] : []), "-m", message]);
  return runGit(path, ["rev-parse", "HEAD"]);
}

function expectError(name: string, operation: () => unknown): void {
  try {
    operation();
  } catch {
    return;
  }
  throw new EnvironmentContractError(`selftest ${name}: operation unexpectedly passed`);
}

export function selftest(): number {
  const base = mkdtempSync(join(tmpdir(), "bettor-origin-selftest-"));
  try {
    const work = join(base, "work");
    initRepo(work);
    const manifestPath = ".arena/locks/bettor-arena.lock.json";
    mkdirSync(dirname(join(work, manifestPath)), { recursive: true });
    writeFileSync(join(work, manifestPath), '{"release":1}\n');
    writeFileSync(join(work, "README.md"), "fixture\n");
    const commit1 = commitAll(work, "initial");
    const originA = join(base, "a.git");
    const originB = join(base, "b.git");
    run("git", ["clone", "-q", "--bare", work, originA]);
    run("git", ["clone", "-q", "--bare", work, originB]);
    const fixture = validateContract(
      {
        schema: CONTRACT_SCHEMA,
        logical_source: "fixture/repo",
        release_manifest: manifestPath,
        accepted_equivalence: [...MODES],
        origins: [
          {
            id: "fixture-authoring",
            role: "authoring",
            scopes: ["local", "promotion"],
            repository: originA,
            live_probe: "host-only",
          },
          {
            id: "fixture-distribution",
            role: "distribution",
            scopes: ["cloud", "promotion"],
            repository: originB,
            live_probe: "ci",
          },
        ],
      },
      { allowLocalRepositories: true },
    );
    const a1 = probeOrigin(fixture, "fixture-authoring", commit1);
    const b1 = probeOrigin(fixture, "fixture-distribution", commit1);
    if (compareOrigins(fixture, [a1, b1]).mode !== "exact-commit")
      throw new EnvironmentContractError("selftest exact-commit failed");

    const commit2 = commitAll(work, "same tree", true);
    runGit(work, ["push", "-q", "--force", originB, `HEAD:refs/heads/main`]);
    const b2 = probeOrigin(fixture, "fixture-distribution", commit2);
    if (compareOrigins(fixture, [a1, b2]).mode !== "same-tree")
      throw new EnvironmentContractError("selftest same-tree failed");

    writeFileSync(join(work, "README.md"), "tree differs, release unchanged\n");
    const commit3 = commitAll(work, "same release manifest");
    runGit(work, ["push", "-q", "--force", originB, `HEAD:refs/heads/main`]);
    const b3 = probeOrigin(fixture, "fixture-distribution", commit3);
    if (compareOrigins(fixture, [a1, b3]).mode !== "same-release-manifest")
      throw new EnvironmentContractError("selftest same-release-manifest failed");

    writeFileSync(join(work, manifestPath), '{"release":2}\n');
    const commit4 = commitAll(work, "release differs");
    runGit(work, ["push", "-q", "--force", originB, `HEAD:refs/heads/main`]);
    const mismatch = compareOrigins(fixture, [a1, probeOrigin(fixture, "fixture-distribution", commit4)]);
    if (mismatch.status !== "FAIL") throw new EnvironmentContractError("selftest origin disagreement was accepted");
    if (probeOrigin(fixture, "fixture-authoring", "main").status !== "ABSENT")
      throw new EnvironmentContractError("selftest mutable ref was accepted");

    const duplicateRoles = JSON.parse(JSON.stringify(fixture));
    duplicateRoles.origins[1].role = "authoring";
    duplicateRoles.origins[1].scopes = ["local", "promotion"];
    duplicateRoles.origins[1].live_probe = "host-only";
    expectError("duplicate-role", () => validateContract(duplicateRoles, { allowLocalRepositories: true }));
    console.log("SELFTEST GREEN: GitHub/Forgejo logical origin contract");
    return 0;
  } finally {
    rmSync(base, { recursive: true, force: true });
  }
}

interface Options {
  root: string;
  command: "check" | "status" | "probe" | "equivalence" | null;
  selftest: boolean;
  output?: string;
  origin?: string;
  commit?: string;
  left?: string;
  right?: string;
}

function parse(argv: string[]): Options {
  const options: Options = { root: DEFAULT_ROOT, command: null, selftest: false };
  const rest = [...argv];
  while (rest.length) {
    const token = rest.shift()!;
    if (["check", "status", "probe", "equivalence"].includes(token)) {
      options.command = token as Options["command"];
      continue;
    }
    if (token === "--selftest") {
      options.selftest = true;
      continue;
    }
    const key = token.startsWith("--") ? token.slice(2) : "";
    if (!["root", "output", "origin", "commit", "left", "right"].includes(key))
      throw new EnvironmentContractError(`unknown argument: ${token}`);
    const value = rest.shift();
    if (!value) throw new EnvironmentContractError(`${token} requires a value`);
    (options as unknown as Record<string, string>)[key] = value;
  }
  options.root = resolve(options.root);
  if (!options.selftest && !options.command) options.command = "check";
  return options;
}

export async function main(argv = process.argv.slice(2)): Promise<number> {
  try {
    const options = parse(argv);
    if (options.selftest) return selftest();
    const contract = loadContract(options.root);
    if (options.command === "check") {
      console.log(`PASS logical origin contract (${contract.origins.length} origins)`);
    } else if (options.command === "status") {
      if (!options.output) throw new EnvironmentContractError("status requires --output");
      writeJson(resolve(options.output), status(options.root));
    } else if (options.command === "probe") {
      if (!options.output || !options.origin || !options.commit)
        throw new EnvironmentContractError("probe requires --origin, --commit, and --output");
      const receipt = probeOrigin(contract, options.origin, options.commit);
      writeJson(resolve(options.output), receipt);
      if (receipt.status !== "PASS") {
        console.error(`ORIGIN-RED ${receipt.note}`);
        return 2;
      }
    } else if (options.command === "equivalence") {
      if (!options.output || !options.left || !options.right)
        throw new EnvironmentContractError("equivalence requires --left, --right, and --output");
      const receipt = compareOrigins(contract, [
        readJson<OriginReceipt>(resolve(options.left)),
        readJson<OriginReceipt>(resolve(options.right)),
      ]);
      writeJson(resolve(options.output), receipt);
      if (receipt.status === "FAIL") return 2;
    }
    return 0;
  } catch (error) {
    console.error(`ORIGIN-CONTRACT-RED ${String(error instanceof Error ? error.message : error)}`);
    return error instanceof EnvironmentContractError ? 2 : 64;
  }
}

if (resolve(process.argv[1] ?? "") === fileURLToPath(import.meta.url)) process.exit(await main());
