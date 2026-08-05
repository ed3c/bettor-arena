#!/usr/bin/env bun
import { existsSync, readFileSync, statSync } from "node:fs";
import { isAbsolute, join, resolve, sep } from "node:path";

const REQUIRED_MANIFEST_PATHS = [
  "AGENTS.md",
  ".agents/skills/seed-repo-operator/SKILL.md",
  "data/source.json",
  "data/evidence.jsonl",
  "data/claims.jsonl",
  "data/unknowns.json",
  "data/decisions.jsonl",
  "data/lineage.json",
  "scripts/check_minimum_lineage.ts",
  "scripts/plan.ts",
] as const;

type ManifestEntry = { path: string; sha256: string; bytes: number };

function sha256(value: string | Uint8Array): string {
  return new Bun.CryptoHasher("sha256").update(value).digest("hex");
}

function readJson(path: string): Record<string, unknown> {
  const value = JSON.parse(readFileSync(path, "utf8"));
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`minimum-lineage JSON object required: ${path}`);
  }
  return value as Record<string, unknown>;
}

function safeManifestPath(root: string, path: unknown): string {
  if (typeof path !== "string" || isAbsolute(path) || path.split(/[\\/]/).includes("..")) {
    throw new Error(`minimum-lineage manifest path escapes repo: ${String(path)}`);
  }
  const absolute = resolve(root, path);
  if (!absolute.startsWith(`${resolve(root)}${sep}`)) {
    throw new Error(`minimum-lineage manifest path escapes repo: ${path}`);
  }
  return absolute;
}

function manifestEntries(value: Record<string, unknown>): ManifestEntry[] {
  if (value.schema_version !== "perfect-seed-artifact-manifest@1.0.0" || !Array.isArray(value.files)) {
    throw new Error("minimum-lineage artifact manifest schema mismatch");
  }
  return value.files as ManifestEntry[];
}

export type MinimumLineageResult = {
  packet_id: string;
  template_version: string;
  manifest_sha256: string;
  manifest_entry_count: number;
};

export function verifyMinimumLineage(rootPath: string): MinimumLineageResult {
  const root = resolve(rootPath);
  const manifestPath = join(root, "data", "artifact-manifest.json");
  const receiptPath = join(root, "data", "build-receipt.json");
  for (const path of [manifestPath, receiptPath]) {
    if (!existsSync(path)) throw new Error(`minimum-lineage file missing: ${path}`);
  }

  const manifestBytes = readFileSync(manifestPath);
  const manifest = readJson(manifestPath);
  const receipt = readJson(receiptPath);
  const source = readJson(join(root, "data", "source.json"));
  const lineage = readJson(join(root, "data", "lineage.json"));
  const entries = manifestEntries(manifest);
  const entryPaths = entries.map((entry) => entry.path);

  if (new Set(entryPaths).size !== entryPaths.length) {
    throw new Error("minimum-lineage artifact manifest contains duplicate paths");
  }
  for (const required of REQUIRED_MANIFEST_PATHS) {
    if (!entryPaths.includes(required)) throw new Error(`minimum-lineage manifest missing: ${required}`);
  }

  const manifestSha256 = sha256(manifestBytes);
  if (
    receipt.schema_version !== "perfect-seed-build-receipt@1.0.0" ||
    receipt.artifact_manifest_sha256 !== manifestSha256 ||
    receipt.manifest_entry_count !== entries.length
  ) {
    throw new Error("minimum-lineage build receipt does not bind artifact manifest");
  }
  if (
    source.schema_version !== "perfect-seed-source@1.0.0" ||
    lineage.schema_version !== "perfect-seed-lineage@1.0.0" ||
    source.packet_id !== lineage.packet_id ||
    source.packet_id !== receipt.packet_id ||
    source.packet_sha256 !== lineage.packet_sha256 ||
    source.task_sha256 !== lineage.task_sha256
  ) {
    throw new Error("minimum-lineage source, lineage, and receipt identity mismatch");
  }

  for (const entry of entries) {
    if (
      typeof entry.sha256 !== "string" ||
      !/^[a-f0-9]{64}$/.test(entry.sha256) ||
      !Number.isInteger(entry.bytes) ||
      entry.bytes < 0
    ) {
      throw new Error(`minimum-lineage manifest entry invalid: ${String(entry.path)}`);
    }
    const path = safeManifestPath(root, entry.path);
    if (!existsSync(path) || !statSync(path).isFile() || statSync(path).size !== entry.bytes) {
      throw new Error(`minimum-lineage file missing or size drift: ${entry.path}`);
    }
    if (sha256(readFileSync(path)) !== entry.sha256) {
      throw new Error(`minimum-lineage hash drift: ${entry.path}`);
    }
  }

  return {
    packet_id: String(source.packet_id),
    template_version: String(manifest.template_version),
    manifest_sha256: manifestSha256,
    manifest_entry_count: entries.length,
  };
}

function cliRoot(args: string[]): string {
  if (args.length === 0) return process.cwd();
  const index = args.indexOf("--repo");
  const value = index >= 0 ? args[index + 1] : undefined;
  if (!value || !isAbsolute(value)) throw new Error("usage: check_minimum_lineage.ts [--repo <absolute-path>]");
  return value;
}

if (import.meta.main) {
  try {
    const result = verifyMinimumLineage(cliRoot(Bun.argv.slice(2)));
    console.log(
      JSON.stringify({ schema_version: "perfect-seed-minimum-lineage-result@1.0.0", status: "passed", ...result }),
    );
  } catch (error) {
    console.error(`FAIL: ${error instanceof Error ? error.message : String(error)}`);
    process.exitCode = 2;
  }
}
