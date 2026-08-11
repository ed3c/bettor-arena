#!/usr/bin/env bun
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { EnvironmentContractError } from "../environment_types.ts";
import { loadContract as loadOrigins, selftest as originSelftest } from "../arena_origins.ts";
import { loadContract as loadBrowser, selftest as browserSelftest } from "../arena_browser.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = resolve(HERE, "../..");

function parse(argv: string[]): { root: string; selftest: boolean } {
  let root = DEFAULT_ROOT;
  let selftest = false;
  const rest = [...argv];
  while (rest.length) {
    const token = rest.shift()!;
    if (token === "--selftest") selftest = true;
    else if (token === "--root") {
      const value = rest.shift(); if (!value) throw new EnvironmentContractError("--root requires a path");
      root = resolve(value);
    } else throw new EnvironmentContractError(`unknown argument: ${token}`);
  }
  return { root, selftest };
}

function staticCheck(root: string): void {
  const required = [
    "scripts/environment_types.ts",
    "scripts/arena_origins.ts",
    "scripts/arena_origin_checkout_probe.ts",
    "scripts/arena_browser.ts",
    ".arena/origins/release.json",
    ".arena/browser/contract.json",
    ".arena/modules/environment-contracts/module.json",
  ];
  for (const path of required) if (!existsSync(join(root, path))) throw new EnvironmentContractError(`missing ${path}`);
  const origins = loadOrigins(root);
  const browser = loadBrowser(root);
  if (origins.origins.length !== 2 || browser.routes.length < 10) throw new EnvironmentContractError("environment contract closure is incomplete");
  const text = `${readFileSync(join(root, ".arena/origins/release.json"), "utf8")}\n${readFileSync(join(root, ".arena/browser/contract.json"), "utf8")}`;
  const forbidden = ["cookie=", "authorization:", "private_key", "client_secret", "/Users/", "~/"];
  for (const marker of forbidden) if (text.toLowerCase().includes(marker.toLowerCase())) throw new EnvironmentContractError(`versioned environment contract contains forbidden host/session material: ${marker}`);
  const manifest = JSON.parse(readFileSync(join(root, ".arena/modules/environment-contracts/module.json"), "utf8"));
  const proof = JSON.stringify(manifest.proof ?? {});
  const components = JSON.stringify(manifest.components ?? {});
  if (!proof.includes("bun") || !proof.includes("check_environment_contracts.ts") || !components.includes("arena_origin_checkout_probe.ts")) {
    throw new EnvironmentContractError("environment module proof is not a complete Bun + TypeScript closure");
  }
}

function main(argv: string[]): number {
  try {
    const options = parse(argv);
    staticCheck(options.root);
    if (options.selftest) {
      originSelftest();
      browserSelftest(options.root);
    }
    console.log("PASS GitHub/Forgejo origin and Browser Contract v2 gates");
    return 0;
  } catch (error) {
    console.error(`ENVIRONMENT-CONTRACT-RED ${String(error instanceof Error ? error.message : error)}`);
    return error instanceof EnvironmentContractError ? 2 : 64;
  }
}

process.exit(main(process.argv.slice(2)));
