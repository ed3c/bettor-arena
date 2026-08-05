import { existsSync, readFileSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { readInputPacket } from "./contracts";
import { materializeRepo } from "./materialize";
import { reducePacket } from "./reduce";

const ROOT = resolve(import.meta.dir, "..");

function sha256(value: string | Uint8Array): string {
  return new Bun.CryptoHasher("sha256").update(value).digest("hex");
}

function option(args: string[], name: string): string {
  const index = args.indexOf(name);
  const value = index >= 0 ? args[index + 1] : undefined;
  if (!value) throw new Error(`missing ${name}`);
  return value;
}

function validateOutputPath(outputPath: string): void {
  if (!isAbsolute(outputPath)) throw new Error("output path must be absolute");
  if (/[\0\r\n"\\]/.test(outputPath)) throw new Error("output path contains unsafe characters");
  if (existsSync(outputPath)) throw new Error(`output already exists: ${outputPath}`);
}

function main(args: string[]): void {
  const command = args[0];
  if (command === "validate") {
    const packetPath = option(args, "--packet");
    readInputPacket(packetPath);
    console.log("PASS: perfect-seed input packet");
    return;
  }
  if (command === "validate-output") {
    validateOutputPath(option(args, "--output"));
    console.log("PASS: perfect-seed output path");
    return;
  }
  if (command !== "build")
    throw new Error("usage: cli.ts validate|validate-output|build --packet <absolute-path> [--output <absolute-path>]");
  const packetPath = option(args, "--packet");
  const outputPath = option(args, "--output");
  validateOutputPath(outputPath);
  const packet = readInputPacket(packetPath);
  const packetBytes = readFileSync(packetPath);
  const ir = reducePacket(packet, sha256(packetBytes));
  const receipt = materializeRepo(ROOT, outputPath, packet, ir);
  console.log(JSON.stringify({ status: "candidate-human-admit-required", ...receipt }));
}

try {
  main(Bun.argv.slice(2));
} catch (error) {
  console.error(`FAIL: ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
}
