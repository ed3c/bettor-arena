#!/usr/bin/env bun
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = resolve(HERE, "../..");

function parse(argv: string[]): { root: string; selftest: boolean } {
  let root = DEFAULT_ROOT;
  let selftest = false;
  const rest = [...argv];
  while (rest.length) {
    const flag = rest.shift();
    if (flag === "--selftest") selftest = true;
    else if (flag === "--root") {
      const value = rest.shift();
      if (!value) throw new Error("--root requires a path");
      root = resolve(value);
    } else throw new Error(`unknown argument: ${flag}`);
  }
  return { root, selftest };
}

function staticCheck(root: string): void {
  const required = [
    "scripts/project_types.ts",
    "scripts/project_resolver.ts",
    "scripts/project_transaction.ts",
    "scripts/arena_project.ts",
    "scripts/arena_project.py",
    ".arena/modules/project-bootstrapper/module.json",
    ".arena/presets/consumer-core.json",
    ".arena/presets/embedded-core.json",
  ];
  for (const path of required) if (!existsSync(join(root, path))) throw new Error(`missing ${path}`);
  const manifest = JSON.parse(readFileSync(join(root, ".arena/modules/project-bootstrapper/module.json"), "utf8"));
  const commandText = JSON.stringify(manifest.proof ?? {});
  if (!commandText.includes("bun") || !commandText.includes("scripts/arena_project.ts")) throw new Error("project-bootstrapper proof is not Bun + TypeScript primary");
  const preset = JSON.parse(readFileSync(join(root, ".arena/presets/consumer-core.json"), "utf8"));
  if (preset.status !== "IMPLEMENTED") throw new Error("consumer-core is not IMPLEMENTED");
  const shim = readFileSync(join(root, "scripts/arena_project.py"), "utf8");
  if (!shim.includes("os.execv") || shim.includes("def plan")) throw new Error("Python entry is not a thin compatibility shim");
}

function main(argv: string[]): number {
  let options: { root: string; selftest: boolean };
  try { options = parse(argv); staticCheck(options.root) }
  catch (error) { console.error(`PROJECT-BOOTSTRAP-GATE-RED ${String(error)}`); return 2 }
  if (options.selftest) {
    const result = spawnSync(process.execPath, [join(options.root, "scripts/arena_project.ts"), "--source", options.root, "--selftest"], {
      cwd: options.root,
      encoding: "utf8",
      stdio: "inherit",
    });
    if (result.status !== 0) return result.status ?? 64;
  }
  console.log("PASS Bun + TypeScript project bootstrap contract");
  return 0;
}

process.exit(main(process.argv.slice(2)));
