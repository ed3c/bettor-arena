import { readdirSync, readFileSync, statSync } from "node:fs";
import { relative, resolve } from "node:path";
import { refsGrounded, type SeedInputPacket } from "./contracts";

const MAX_SOURCE_BYTES = 512 * 1024;
const MAX_REPO_FILES = 200;
const MAX_REPO_FILE_BYTES = 128 * 1024;
const IGNORED_DIRECTORIES = new Set([".git", "node_modules", "dist", "coverage", "__pycache__"]);

export interface EvidenceRecord {
  evidence_id: string;
  source_ref: string;
  sha256: string;
  excerpt: string;
}

export interface ReducedIR {
  source: Record<string, unknown>;
  evidence: EvidenceRecord[];
  claims: Array<Record<string, unknown>>;
  unknowns: Array<Record<string, unknown>>;
  decisions: Array<Record<string, unknown>>;
}

function sha256(value: string | Uint8Array): string {
  return new Bun.CryptoHasher("sha256").update(value).digest("hex");
}

function boundedText(path: string): string {
  const bytes = readFileSync(path);
  if (bytes.byteLength > MAX_SOURCE_BYTES) throw new Error(`source exceeds ${MAX_SOURCE_BYTES} bytes: ${path}`);
  return bytes.toString("utf8");
}

function repoFiles(root: string): string[] {
  const files: string[] = [];
  const visit = (directory: string): void => {
    for (const entry of readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      if (entry.isSymbolicLink()) continue;
      const absolute = resolve(directory, entry.name);
      if (entry.isDirectory()) {
        if (!IGNORED_DIRECTORIES.has(entry.name)) visit(absolute);
      } else if (entry.isFile()) {
        files.push(absolute);
        if (files.length > MAX_REPO_FILES) throw new Error(`repo exceeds ${MAX_REPO_FILES} files`);
      }
    }
  };
  visit(root);
  return files;
}

function textEvidence(packet: SeedInputPacket): EvidenceRecord[] {
  const text = boundedText(packet.source_path);
  const lines = text.split(/\r?\n/);
  return lines
    .map((line, index) => ({ line: line.trim(), index }))
    .filter(({ line }) => line.length > 0)
    .slice(0, 120)
    .map(({ line, index }, position) => ({
      evidence_id: `E${String(position + 1).padStart(3, "0")}`,
      source_ref: `${packet.source_path}:${index + 1}`,
      sha256: sha256(line),
      excerpt: line.slice(0, 240),
    }));
}

function repoEvidence(packet: SeedInputPacket): EvidenceRecord[] {
  return repoFiles(packet.source_path).map((path, index) => {
    const stat = statSync(path);
    if (stat.size > MAX_REPO_FILE_BYTES) {
      return {
        evidence_id: `E${String(index + 1).padStart(3, "0")}`,
        source_ref: relative(packet.source_path, path),
        sha256: sha256(readFileSync(path)),
        excerpt: `N/A-binary-or-large:${stat.size}`,
      };
    }
    const bytes = readFileSync(path);
    return {
      evidence_id: `E${String(index + 1).padStart(3, "0")}`,
      source_ref: relative(packet.source_path, path),
      sha256: sha256(bytes),
      excerpt: bytes.toString("utf8").replace(/\s+/g, " ").slice(0, 240),
    };
  });
}

export function reducePacket(packet: SeedInputPacket, packetSha256: string): ReducedIR {
  const evidence = packet.source_kind === "repo" ? repoEvidence(packet) : textEvidence(packet);
  const firstEvidence = evidence[0];
  if (!firstEvidence) throw new Error("source produced zero evidence records");
  const claims = evidence.slice(0, 24).map((record, index) => ({
    claim_id: `C${String(index + 1).padStart(3, "0")}`,
    text: record.excerpt,
    evidence_ids: [record.evidence_id],
    grounding: "candidate",
  }));
  const questionEvidence = evidence
    .filter((record) => record.excerpt.includes("?"))
    .map((record) => record.evidence_id);
  const unknowns = [
    {
      unknown_id: "U-KK",
      quadrant: "KK",
      question: "Which source facts are already physically present?",
      evidence_ids: evidence.slice(0, 3).map((item) => item.evidence_id),
    },
    {
      unknown_id: "U-KU",
      quadrant: "KU",
      question: "Which source questions require source or runtime verification?",
      evidence_ids: questionEvidence.length ? questionEvidence : [firstEvidence.evidence_id],
    },
    {
      unknown_id: "U-UK",
      quadrant: "UK",
      question: "Which architecture preference requires a runnable counterfactual?",
      evidence_ids: [],
    },
    {
      unknown_id: "U-UU",
      quadrant: "UU",
      question: "Which negative-space or lifecycle risk is absent from the source framing?",
      evidence_ids: [],
    },
  ];
  return {
    source: {
      schema_version: "perfect-seed-source@1.0.0",
      packet_id: packet.packet_id,
      packet_sha256: packetSha256,
      source_kind: packet.source_kind,
      source_path: packet.source_path,
      task: packet.task,
      task_sha256: sha256(packet.task),
      evidence_count: evidence.length,
      source_refs: packet.source_refs,
      refs_grounded: refsGrounded(packet.source_refs),
      human_gate: packet.human_gate,
    },
    evidence,
    claims,
    unknowns,
    decisions: [
      {
        decision_id: "D001",
        state: "MATCH",
        decision: `route-${packet.source_kind}`,
        grounding: "technical_equivalent",
        evidence_ids: [firstEvidence.evidence_id],
      },
      {
        decision_id: "D002",
        state: "GENERATE",
        decision: "materialize-bounded-local-seed",
        grounding: "candidate",
        evidence_ids: evidence.slice(0, 2).map((item) => item.evidence_id),
      },
      {
        decision_id: "D003",
        state: "ADMIT",
        decision: "human-required-before-seed-admit",
        grounding: "human_required",
        evidence_ids: [],
      },
    ],
  };
}
