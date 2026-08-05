import { readFileSync, writeFileSync } from "node:fs";
import { isAbsolute } from "node:path";

const args = Bun.argv.slice(2);
const inputIndex = args.indexOf("--input");
const outputIndex = args.indexOf("--output");
const input = inputIndex >= 0 ? args[inputIndex + 1] : undefined;
const output = outputIndex >= 0 ? args[outputIndex + 1] : undefined;
if (!input || !output) {
  throw new Error("usage: migrate_packet.ts --input <absolute-path> --output <absolute-path>");
}
if (!isAbsolute(input) || !isAbsolute(output)) throw new Error("migration paths must be absolute");
const legacy = JSON.parse(readFileSync(input, "utf8"));
if (legacy.schema_version !== "perfect-seed-input@0.1.0")
  throw new Error("only perfect-seed-input@0.1.0 can be migrated");
const migrated = {
  ...legacy,
  schema_version: "perfect-seed-input@1.0.0",
  packet_state: legacy.packet_state ?? "draft",
  fixed_prompt_context: legacy.fixed_prompt_context ?? ["PROMPT.md", "modules/semantic-truth-context.md"],
  emergent_prompt_context: legacy.emergent_prompt_context ?? "N/A-none",
  // Pre-source-refs packets carry a marked sentinel ref: validate accepts it,
  // but route-result records refs_grounded:false so the packet never fakes an anchor.
  source_refs: legacy.source_refs ?? [
    { repo: "unknown", commit: "0000000", path: "unmigrated/unknown", anchor: "pre-source-refs" },
  ],
  human_gate: "required_before_seed_admit",
};
writeFileSync(output, `${JSON.stringify(migrated, null, 2)}\n`, "utf8");
console.log("PASS: perfect-seed packet schema replay migration");
