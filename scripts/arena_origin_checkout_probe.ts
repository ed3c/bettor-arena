#!/usr/bin/env bun
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  EnvironmentContractError,
  SHA40,
  readJson,
  runGit,
  sha256Json,
  withDigest,
  writeJson,
} from "./environment_types.ts";
import { loadContract } from "./arena_origins.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = resolve(HERE, "..");
const RECEIPT_SCHEMA = "bettor-arena/origin-receipt/v1";

function normalizedRepository(value: string): string {
  return value
    .trim()
    .replace(/\.git$/, "")
    .replace(/\/$/, "");
}

interface Options {
  root: string;
  origin: string;
  commit: string;
  output: string;
}

function parse(argv: string[]): Options {
  const options: Partial<Options> = { root: DEFAULT_ROOT };
  const rest = [...argv];
  while (rest.length) {
    const token = rest.shift()!;
    if (!["--root", "--origin", "--commit", "--output"].includes(token)) {
      throw new EnvironmentContractError(`unknown argument: ${token}`);
    }
    const value = rest.shift();
    if (!value) throw new EnvironmentContractError(`${token} requires a value`);
    (options as Record<string, string>)[token.slice(2)] = value;
  }
  if (!options.origin || !options.commit || !options.output) {
    throw new EnvironmentContractError("--origin, --commit, and --output are required");
  }
  return {
    root: resolve(options.root!),
    origin: options.origin,
    commit: options.commit,
    output: resolve(options.output),
  };
}

function main(argv = process.argv.slice(2)): number {
  try {
    const options = parse(argv);
    if (!SHA40.test(options.commit)) {
      throw new EnvironmentContractError("checkout probe requires an exact 40-hex commit, never main/HEAD");
    }
    const contract = loadContract(options.root);
    const origin = contract.origins.find((candidate) => candidate.id === options.origin);
    if (!origin) throw new EnvironmentContractError(`unknown origin: ${options.origin}`);
    if (origin.role !== "distribution" || origin.live_probe !== "ci") {
      throw new EnvironmentContractError("authenticated checkout probes are only valid for the CI distribution origin");
    }
    const remote = runGit(options.root, ["remote", "get-url", "origin"]);
    if (normalizedRepository(remote) !== normalizedRepository(origin.repository)) {
      throw new EnvironmentContractError(
        `checkout remote ${remote} differs from configured origin ${origin.repository}`,
      );
    }
    const actual = runGit(options.root, ["rev-parse", "HEAD"]);
    if (actual !== options.commit) {
      throw new EnvironmentContractError(`checkout HEAD ${actual} differs from requested commit ${options.commit}`);
    }
    const tree = runGit(options.root, ["rev-parse", "HEAD^{tree}"]);
    const manifest = readJson(join(options.root, contract.release_manifest));
    const receipt = withDigest({
      schema: RECEIPT_SCHEMA,
      logical_source: contract.logical_source,
      origin: {
        id: origin.id,
        role: origin.role,
        repository: origin.repository,
        scopes: origin.scopes,
      },
      status: "PASS",
      subject: {
        commit: actual,
        tree,
        release_manifest: contract.release_manifest,
        release_manifest_sha256: sha256Json(manifest),
      },
      note: "Authenticated actions/checkout acquired the exact commit from the configured GitHub distribution origin; the immutable subject was read from that checkout.",
    });
    writeJson(options.output, receipt);
    console.log(`PASS authenticated GitHub checkout origin ${origin.id} commit=${actual}`);
    return 0;
  } catch (error) {
    console.error(`ORIGIN-CHECKOUT-RED ${String(error instanceof Error ? error.message : error)}`);
    return error instanceof EnvironmentContractError ? 2 : 64;
  }
}

process.exit(main());
