import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import type { SeedInputPacket } from "./contracts";
import type { ReducedIR } from "./reduce";

const TEMPLATE_VERSION = "perfect-seed-repo@1.1.0";

function sha256(value: string | Uint8Array): string {
  return new Bun.CryptoHasher("sha256").update(value).digest("hex");
}

function writeJson(path: string, value: unknown): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function writeJsonl(path: string, values: unknown[]): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${values.map((value) => JSON.stringify(value)).join("\n")}\n`, "utf8");
}

function listFiles(root: string, directory = root): string[] {
  const files: string[] = [];
  for (const entry of readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const absolute = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...listFiles(root, absolute));
    else if (entry.isFile()) files.push(relative(root, absolute));
  }
  return files;
}

export function materializeRepo(
  factoryRoot: string,
  outputPath: string,
  packet: SeedInputPacket,
  ir: ReducedIR,
): Record<string, unknown> {
  const output = resolve(outputPath);
  if (existsSync(output)) throw new Error(`output already exists: ${output}`);
  mkdirSync(output, { recursive: false });
  const templateRoot = join(factoryRoot, "templates", "repo");
  const templateNodeModules = join(templateRoot, "node_modules");
  cpSync(templateRoot, output, {
    recursive: true,
    errorOnExist: true,
    filter: (source) => source !== templateNodeModules && !source.startsWith(`${templateNodeModules}${sep}`),
  });
  writeJson(join(output, "data", "source.json"), ir.source);
  writeJsonl(join(output, "data", "evidence.jsonl"), ir.evidence);
  writeJsonl(join(output, "data", "claims.jsonl"), ir.claims);
  writeJson(join(output, "data", "unknowns.json"), ir.unknowns);
  writeJsonl(join(output, "data", "decisions.jsonl"), ir.decisions);
  writeJson(join(output, "data", "lineage.json"), {
    schema_version: "perfect-seed-lineage@1.0.0",
    template_version: TEMPLATE_VERSION,
    packet_id: packet.packet_id,
    packet_sha256: ir.source.packet_sha256,
    source_kind: packet.source_kind,
    task_sha256: ir.source.task_sha256,
    fixed_prompt_context: packet.fixed_prompt_context,
    emergent_prompt_context: packet.emergent_prompt_context,
    terminal_human_gate: packet.human_gate,
  });
  const manifestEntries = listFiles(output)
    .filter((path) => path !== "data/artifact-manifest.json" && path !== "data/build-receipt.json")
    .map((path) => ({
      path,
      sha256: sha256(readFileSync(join(output, path))),
      bytes: statSync(join(output, path)).size,
    }));
  const manifest = {
    schema_version: "perfect-seed-artifact-manifest@1.0.0",
    template_version: TEMPLATE_VERSION,
    files: manifestEntries,
  };
  writeJson(join(output, "data", "artifact-manifest.json"), manifest);
  const artifactManifestSha256 = sha256(`${JSON.stringify(manifest, null, 2)}\n`);
  writeJson(join(output, "data", "build-receipt.json"), {
    schema_version: "perfect-seed-build-receipt@1.0.0",
    packet_id: packet.packet_id,
    artifact_manifest_sha256: artifactManifestSha256,
    manifest_entry_count: manifestEntries.length,
    terminal_state: "candidate-human-admit-required",
  });
  return { output, file_count: manifestEntries.length + 2, artifact_manifest_sha256: artifactManifestSha256 };
}
