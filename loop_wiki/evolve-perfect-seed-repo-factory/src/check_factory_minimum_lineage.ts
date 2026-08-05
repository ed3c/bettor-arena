#!/usr/bin/env bun
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { readInputPacket } from "./contracts";
import { materializeRepo } from "./materialize";
import { verifyMinimumLineage } from "./minimum_lineage";
import { reducePacket } from "./reduce";

const root = resolve(import.meta.dir, "..");
const packetPath = join(root, "packets", "inbox", "dr-example.json");
const temporaryRoot = mkdtempSync(join(tmpdir(), "perfect-seed-minimum-lineage-"));

function sha256(value: string | Uint8Array): string {
  return new Bun.CryptoHasher("sha256").update(value).digest("hex");
}

try {
  const packetBytes = readFileSync(packetPath);
  const packet = readInputPacket(packetPath);
  const output = join(temporaryRoot, "generated");
  materializeRepo(root, output, packet, reducePacket(packet, sha256(packetBytes)));
  const result = verifyMinimumLineage(output);
  console.log(
    JSON.stringify({
      schema_version: "perfect-seed-factory-minimum-lineage-result@1.0.0",
      status: "passed",
      ...result,
    }),
  );
} catch (error) {
  console.error(`FAIL: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 2;
} finally {
  rmSync(temporaryRoot, { recursive: true, force: true });
}
