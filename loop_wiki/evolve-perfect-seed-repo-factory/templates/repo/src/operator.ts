import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { CAPABILITIES } from "./capabilities";
import type { CallResult } from "./contracts";
import { HANDLERS } from "./functions";
import { loadLocalContext } from "./local_store";

function sha256(value: string): string {
  return new Bun.CryptoHasher("sha256").update(value).digest("hex");
}

export function runOperator(root: string, task: string): CallResult[] {
  if (CAPABILITIES.length !== 20)
    throw new Error(`capability registry must contain exactly 20 calls, got ${CAPABILITIES.length}`);
  if (new Set(CAPABILITIES.map((entry) => entry.call_id)).size !== 20)
    throw new Error("capability registry contains duplicate call ids");
  const context = loadLocalContext(root, task);
  const prior = new Map<string, CallResult>();
  const results: CallResult[] = [];
  for (const capability of CAPABILITIES) {
    for (const dependency of capability.depends_on) {
      if (!prior.has(dependency)) throw new Error(`${capability.call_id} dependency not satisfied: ${dependency}`);
    }
    const handler = HANDLERS[capability.function_name];
    if (!handler) throw new Error(`missing handler: ${capability.function_name}`);
    const input = JSON.stringify({
      task: context.task,
      source_sha256: context.source.packet_sha256,
      dependencies: capability.depends_on.map((id) => prior.get(id)?.output_sha256),
    });
    const output = handler(context, prior);
    const result = {
      call_id: capability.call_id,
      function_name: capability.function_name,
      input_sha256: sha256(input),
      output,
      output_sha256: sha256(JSON.stringify(output)),
    };
    prior.set(capability.call_id, result);
    results.push(result);
  }
  writeFileSync(
    join(root, "data/call-plan.json"),
    `${JSON.stringify({ schema_version: "perfect-seed-call-plan@1.0.0", task: context.task, task_sha256: sha256(context.task), calls: CAPABILITIES }, null, 2)}\n`,
    "utf8",
  );
  writeFileSync(
    join(root, "data/call-results.jsonl"),
    `${results.map((result) => JSON.stringify(result)).join("\n")}\n`,
    "utf8",
  );
  return results;
}
