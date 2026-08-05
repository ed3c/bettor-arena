import { existsSync, readFileSync, statSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";

export const SOURCE_KINDS = ["dr", "gcr", "repo", "grill-me"] as const;
export type SourceKind = (typeof SOURCE_KINDS)[number];

export interface SeedInputPacket {
  schema_version: "perfect-seed-input@1.0.0";
  packet_id: string;
  packet_state: "admitted";
  source_kind: SourceKind;
  source_path: string;
  task: string;
  fixed_prompt_context: string[];
  emergent_prompt_context: string;
  human_gate: "required_before_seed_admit";
}

function requireCondition(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function readInputPacket(packetPath: string): SeedInputPacket {
  requireCondition(isAbsolute(packetPath), "packet path must be absolute");
  requireCondition(existsSync(packetPath), `packet not found: ${packetPath}`);
  const value = JSON.parse(readFileSync(packetPath, "utf8")) as Partial<SeedInputPacket>;
  requireCondition(value.schema_version === "perfect-seed-input@1.0.0", "unsupported schema_version");
  requireCondition(
    typeof value.packet_id === "string" && /^[a-zA-Z0-9][a-zA-Z0-9._-]{2,80}$/.test(value.packet_id),
    "invalid packet_id",
  );
  requireCondition(value.packet_state === "admitted", "packet_state must be admitted before build");
  requireCondition(
    SOURCE_KINDS.includes(value.source_kind as SourceKind),
    `unsupported source_kind: ${String(value.source_kind)}`,
  );
  requireCondition(typeof value.source_path === "string" && value.source_path.length > 0, "source_path is required");
  requireCondition(!/[\0\r\n]/.test(value.source_path), "source_path contains unsafe characters");
  const sourcePath = isAbsolute(value.source_path)
    ? resolve(value.source_path)
    : resolve(import.meta.dir, "..", value.source_path);
  requireCondition(existsSync(sourcePath), `source not found: ${sourcePath}`);
  requireCondition(
    value.source_kind === "repo" ? statSync(sourcePath).isDirectory() : statSync(sourcePath).isFile(),
    "source kind does not match source path",
  );
  requireCondition(
    typeof value.task === "string" && value.task.trim().length >= 12 && value.task.length <= 4000,
    "task must contain 12-4000 characters",
  );
  requireCondition(Array.isArray(value.fixed_prompt_context), "fixed_prompt_context must be an array");
  requireCondition(
    value.fixed_prompt_context.includes("modules/semantic-truth-context.md"),
    "fixed_prompt_context must include modules/semantic-truth-context.md",
  );
  requireCondition(
    typeof value.emergent_prompt_context === "string" && value.emergent_prompt_context.length > 0,
    "emergent_prompt_context is required",
  );
  requireCondition(value.human_gate === "required_before_seed_admit", "human_gate must preserve seed admission");
  return { ...value, source_path: sourcePath } as SeedInputPacket;
}
