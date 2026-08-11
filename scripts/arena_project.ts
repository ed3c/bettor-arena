#!/usr/bin/env bun
import { spawnSync } from "node:child_process";
import {
  existsSync,
  lstatSync,
  mkdtempSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  EMBEDDED_PATH,
  MANAGED_PATH,
  ProjectError,
  gitHeadOrNull,
  readJson,
  runGit,
  sha256Bytes,
  withDigest,
  writeJson,
  type ManagedManifest,
  type ProjectPlan,
  type ProjectRequirements,
} from "./project_types.ts";
import {
  applyProject,
  copyRequirements,
  planProject,
  rollbackProject,
  verifyProject,
} from "./project_transaction.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const DEFAULT_SOURCE = resolve(HERE, "..");

interface Options {
  source: string;
  command?: "plan" | "apply" | "verify" | "rollback";
  requirements?: string;
  target?: string;
  output?: string;
  plan?: string;
  receipt?: string;
  selftest: boolean;
  json: boolean;
}

function parseArgs(argv: string[]): Options {
  const options: Options = { source: DEFAULT_SOURCE, selftest: false, json: false };
  const rest = [...argv];
  while (rest.length) {
    const token = rest.shift()!;
    if (["plan", "apply", "verify", "rollback"].includes(token)) {
      if (options.command) throw new ProjectError("only one project command may be selected");
      options.command = token as Options["command"];
      continue;
    }
    if (token === "--selftest") { options.selftest = true; continue }
    if (token === "--json") { options.json = true; continue }
    const key = token.startsWith("--") ? token.slice(2).replaceAll("-", "_") : "";
    if (!["source", "requirements", "target", "output", "plan", "receipt"].includes(key)) throw new ProjectError(`unknown argument: ${token}`);
    const value = rest.shift();
    if (!value) throw new ProjectError(`${token} requires a value`);
    (options as unknown as Record<string, string>)[key] = value;
  }
  if (options.selftest) {
    if (options.command) throw new ProjectError("--selftest cannot be combined with a command");
    return options;
  }
  if (!options.command) throw new ProjectError("command required: plan | apply | verify | rollback");
  if (!options.target) throw new ProjectError(`${options.command}: --target is required`);
  if (options.command === "plan" && (!options.requirements || !options.output)) throw new ProjectError("plan: --requirements and --output are required");
  if (options.command === "apply" && !options.plan) throw new ProjectError("apply: --plan is required");
  if (options.command === "rollback" && !options.receipt) throw new ProjectError("rollback: --receipt is required");
  return options;
}

function output(value: unknown): void { console.log(JSON.stringify(value, null, 2)) }

function initTarget(path: string): void {
  mkdirSync(path, { recursive: true });
  const init = spawnSync("git", ["init", "-q", path], { encoding: "utf8" });
  if (init.status !== 0) throw new ProjectError(init.stderr || "git init failed");
  runGit(path, ["config", "user.email", "selftest@example.invalid"]);
  runGit(path, ["config", "user.name", "bettor selftest"]);
}

function expectError(name: string, operation: () => unknown, contains?: string): void {
  try { operation() } catch (error) {
    const message = String(error instanceof Error ? error.message : error);
    if (contains && !message.includes(contains)) throw new ProjectError(`selftest ${name}: wrong error: ${message}`);
    return;
  }
  throw new ProjectError(`selftest ${name}: operation unexpectedly passed`);
}

function requirements(id: string, mode: ProjectRequirements["mode"], commit: string): ProjectRequirements {
  return {
    schema: "bettor-arena/project-requirements/v1",
    id,
    mode,
    release: { repository: "https://github.com/ed3c/bettor-arena", commit },
    preset: mode === "remote-consumer" ? "consumer-core" : "embedded-core",
    modules: [],
  };
}

export function selftest(source: string): number {
  source = resolve(source);
  const commit = gitHeadOrNull(source);
  if (!commit) throw new ProjectError("selftest source has no commit");
  if (runGit(source, ["status", "--porcelain", "--untracked-files=all"])) throw new ProjectError("selftest requires a clean source checkout");
  const base = mkdtempSync(join(tmpdir(), "bettor-project-selftest-"));
  try {
    const remoteTarget = join(base, "remote");
    initTarget(remoteTarget);
    const remoteReqPath = join(base, "remote-requirements.json");
    copyRequirements(remoteReqPath, requirements("remote-fixture", "remote-consumer", commit));
    const remotePlan = planProject(source, remoteTarget, remoteReqPath);
    if (remotePlan.files.length < 8 || remotePlan.embedded !== null) throw new ProjectError("selftest remote plan has incomplete projections");
    if (existsSync(join(remoteTarget, "AGENTS.md"))) throw new ProjectError("selftest plan mutated the target");
    const remotePlanPath = join(base, "remote-plan.json");
    writeJson(remotePlanPath, remotePlan);

    const stale = { ...remotePlan, project: "tampered" } as ProjectPlan;
    const stalePath = join(base, "stale-plan.json");
    writeJson(stalePath, stale);
    expectError("stale-plan", () => applyProject(source, remoteTarget, stalePath), "content_sha256 mismatch");

    const receiptPath = applyProject(source, remoteTarget, remotePlanPath, join(base, "remote-receipt-1.json"));
    verifyProject(remoteTarget);
    const launcher = readFileSync(join(remoteTarget, ".arena/bin/bettor-mcp"), "utf8");
    if (!launcher.includes("mcp_runtime.ts") || !launcher.includes("exec bun") || launcher.includes("mcp_server.py")) {
      throw new ProjectError("selftest remote launcher is not Bun + TypeScript primary");
    }
    const agentPath = join(remoteTarget, "AGENTS.md");
    const afterAgent = readFileSync(agentPath);
    writeFileSync(agentPath, `${afterAgent.toString("utf8")}\ndrift\n`);
    expectError("verify-drift", () => verifyProject(remoteTarget), "modified");
    expectError("rollback-drift", () => rollbackProject(remoteTarget, receiptPath), "changed after apply");
    writeFileSync(agentPath, afterAgent);
    rollbackProject(remoteTarget, receiptPath);
    if (existsSync(agentPath) || existsSync(join(remoteTarget, MANAGED_PATH))) throw new ProjectError("selftest rollback left managed projections");

    writeFileSync(agentPath, "unmanaged\n");
    expectError("unmanaged-conflict", () => planProject(source, remoteTarget, remoteReqPath), "unmanaged conflict");
    rmSync(agentPath);

    const orphanPlan = planProject(source, remoteTarget, remoteReqPath);
    const orphanPlanPath = join(base, "orphan-plan.json");
    writeJson(orphanPlanPath, orphanPlan);
    const orphanReceipt = applyProject(source, remoteTarget, orphanPlanPath, join(base, "remote-receipt-2.json"));
    const managedPath = join(remoteTarget, MANAGED_PATH);
    const originalManagedBytes = readFileSync(managedPath);
    const managed = readJson<ManagedManifest>(managedPath);
    const orphanRelative = ".arena/orphan.txt";
    writeFileSync(join(remoteTarget, orphanRelative), "owned orphan\n");
    const alteredUnsigned = {
      ...managed,
      paths: [...managed.paths, { path: orphanRelative, sha256: sha256Bytes(readFileSync(join(remoteTarget, orphanRelative))), mode: 0o644 }],
    } as Record<string, unknown>;
    delete alteredUnsigned.content_sha256;
    writeJson(managedPath, withDigest(alteredUnsigned));
    const cleanupPlan = planProject(source, remoteTarget, remoteReqPath);
    if (!cleanupPlan.files.some((item) => item.path === orphanRelative && item.action === "delete")) throw new ProjectError("selftest orphan projection was not named for deletion");
    writeFileSync(managedPath, originalManagedBytes);
    rmSync(join(remoteTarget, orphanRelative));
    rollbackProject(remoteTarget, orphanReceipt);

    const embeddedTarget = join(base, "embedded");
    initTarget(embeddedTarget);
    const embeddedReqPath = join(base, "embedded-requirements.json");
    copyRequirements(embeddedReqPath, requirements("embedded-fixture", "embedded-core", commit));
    const embeddedPlan = planProject(source, embeddedTarget, embeddedReqPath);
    const embeddedPlanPath = join(base, "embedded-plan.json");
    writeJson(embeddedPlanPath, embeddedPlan);
    const embeddedReceipt = applyProject(source, embeddedTarget, embeddedPlanPath, join(base, "embedded-receipt.json"));
    verifyProject(embeddedTarget);
    const vendor = join(embeddedTarget, EMBEDDED_PATH);
    if (lstatSync(vendor).isSymbolicLink() || runGit(vendor, ["rev-parse", "HEAD"]) !== commit) throw new ProjectError("selftest embedded release is not an independent exact clone");
    rollbackProject(embeddedTarget, embeddedReceipt);
    if (existsSync(vendor)) throw new ProjectError("selftest embedded rollback left the clone");

    console.log("SELFTEST GREEN: Bun + TypeScript project bootstrapper");
    return 0;
  } finally { rmSync(base, { recursive: true, force: true }) }
}

export async function main(argv = process.argv.slice(2)): Promise<number> {
  let options: Options;
  try { options = parseArgs(argv) }
  catch (error) {
    console.error(`project-bootstrap FATAL: ${String(error instanceof Error ? error.message : error)}`);
    return 64;
  }
  try {
    if (options.selftest) return selftest(options.source);
    const target = resolve(options.target!);
    if (options.command === "plan") {
      const plan = planProject(resolve(options.source), target, resolve(options.requirements!));
      writeJson(resolve(options.output!), plan);
      output({ status: "PLANNED", plan_sha256: plan.content_sha256, files: plan.files.map(({ path, action }) => ({ path, action })) });
    } else if (options.command === "apply") {
      const receipt = applyProject(resolve(options.source), target, resolve(options.plan!), options.receipt ? resolve(options.receipt) : undefined);
      output({ status: "APPLIED", receipt });
    } else if (options.command === "verify") {
      const managed = verifyProject(target);
      output({ status: "PASS", project: managed.project, mode: managed.mode, plan_sha256: managed.plan_sha256 });
    } else if (options.command === "rollback") {
      rollbackProject(target, resolve(options.receipt!));
      output({ status: "ROLLED_BACK", receipt: resolve(options.receipt!) });
    }
    return 0;
  } catch (error) {
    if (error instanceof ProjectError) { console.error(`PROJECT-BOOTSTRAP-RED ${error.message}`); return 2 }
    console.error(`project-bootstrap FATAL: ${String(error)}`);
    return 64;
  }
}

const invoked = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) process.exit(await main());
