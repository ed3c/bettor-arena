import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { ReceiptCheckError, readInputPacket, refsStatusForPacket, resolveReceiptPath } from "./contracts";
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

function refsStatusJson(packetPath: string): string {
  const packet = readInputPacket(packetPath);
  const status = refsStatusForPacket(packetPath, packet, sha256(readFileSync(packetPath)));
  return JSON.stringify({
    schema_version: "perfect-seed-refs-status@1.0.0",
    packet_id: packet.packet_id,
    refs_status: status,
    source_refs: packet.source_refs,
  });
}

function resolveRefs(args: string[]): void {
  const packetPath = option(args, "--packet");
  const packet = readInputPacket(packetPath);
  const peerIndex = args.indexOf("--peer");
  const peer = peerIndex >= 0 ? args[peerIndex + 1] : undefined;
  if (!peer) {
    // Explicit audit only: standing validate/build/verify gates never read sibling checkouts.
    console.log("NOT_RUN: resolve-refs requires --peer <absolute-path>; refs were not audited");
    process.exitCode = 2;
    return;
  }
  if (!isAbsolute(peer)) throw new Error("--peer must be an absolute path");
  if (!existsSync(peer)) throw new Error(`peer repo not found: ${peer}`);
  for (const ref of packet.source_refs) {
    const commitCheck = Bun.spawnSync(["git", "-C", peer, "cat-file", "-e", `${ref.commit}^{commit}`], {
      stdout: "pipe",
      stderr: "pipe",
    });
    if (commitCheck.exitCode !== 0) throw new Error(`source_refs commit not found in peer: ${ref.commit}`);
    const tracked = Bun.spawnSync(["git", "-C", peer, "ls-tree", "-r", "--name-only", ref.commit, "--", ref.path], {
      stdout: "pipe",
      stderr: "pipe",
    });
    if (tracked.exitCode !== 0 || !tracked.stdout.toString().split("\n").includes(ref.path))
      throw new Error(`source_refs path not tracked at ${ref.commit}: ${ref.path}`);
  }
  const receiptPath = resolveReceiptPath(packetPath);
  writeFileSync(
    receiptPath,
    `${JSON.stringify(
      {
        schema_version: "perfect-seed-resolve-receipt@1.0.0",
        packet_id: packet.packet_id,
        packet_sha256: sha256(readFileSync(packetPath)),
        peer,
        ref_count: packet.source_refs.length,
        refs_status: "resolved",
      },
      null,
      2,
    )}\n`,
    "utf8",
  );
  console.log(`PASS: resolved ${packet.source_refs.length} source_refs against ${peer}; receipt=${receiptPath}`);
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
  if (command === "resolve-refs") {
    resolveRefs(args);
    return;
  }
  if (command === "refs-status") {
    console.log(refsStatusJson(option(args, "--packet")));
    return;
  }
  if (command !== "build")
    throw new Error(
      "usage: cli.ts validate|validate-output|resolve-refs|refs-status|build --packet <absolute-path> [--output <absolute-path>] [--peer <absolute-path>]",
    );
  const packetPath = option(args, "--packet");
  const outputPath = option(args, "--output");
  validateOutputPath(outputPath);
  const packet = readInputPacket(packetPath);
  const packetSha256 = sha256(readFileSync(packetPath));
  const ir = reducePacket(packet, packetSha256, refsStatusForPacket(packetPath, packet, packetSha256));
  const receipt = materializeRepo(ROOT, outputPath, packet, ir);
  console.log(JSON.stringify({ status: "candidate-human-admit-required", ...receipt }));
}

try {
  main(Bun.argv.slice(2));
} catch (error) {
  console.error(`FAIL: ${error instanceof Error ? error.message : String(error)}`);
  // Exit 2 = a check ran and failed on unreadable evidence; 1 = precondition/usage.
  process.exitCode = error instanceof ReceiptCheckError ? 2 : 1;
}
