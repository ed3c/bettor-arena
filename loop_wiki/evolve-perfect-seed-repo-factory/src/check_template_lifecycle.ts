import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const ROOT = resolve(import.meta.dir, "..");
const metadata = JSON.parse(readFileSync(resolve(ROOT, "templates", "template-metadata.json"), "utf8"));
if (metadata.schema_version !== "perfect-seed-template-lifecycle@1.0.0")
  throw new Error("invalid template lifecycle schema");
if (!new Set(["draft", "validated", "seed", "deprecated", "retired"]).has(metadata.lifecycle_state))
  throw new Error("invalid lifecycle_state");
if (metadata.lifecycle_state === "seed" && metadata.human_admit !== true)
  throw new Error("seed lifecycle requires human_admit=true");
for (const evidence of metadata.promotion_evidence ?? []) {
  if (typeof evidence !== "string" || !existsSync(resolve(ROOT, evidence)))
    throw new Error(`template promotion evidence missing: ${String(evidence)}`);
}
console.log("PASS: perfect-seed template lifecycle");
