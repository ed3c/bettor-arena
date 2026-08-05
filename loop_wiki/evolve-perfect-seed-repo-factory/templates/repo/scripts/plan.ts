import { resolve } from "node:path";
import { runOperator } from "../src/operator";

const args = Bun.argv.slice(2);
const taskIndex = args.indexOf("--task");
const task = taskIndex >= 0 ? args[taskIndex + 1] : undefined;
if (!task) {
  console.error("FAIL: usage: bun run scripts/plan.ts --task <task>");
  process.exit(64);
}

try {
  const results = runOperator(resolve(import.meta.dir, ".."), task);
  console.log(
    JSON.stringify({
      status: "candidate-human-admit-required",
      call_count: results.length,
      final_call: results.at(-1)?.call_id,
    }),
  );
} catch (error) {
  console.error(`FAIL: ${error instanceof Error ? error.message : String(error)}`);
  process.exit(1);
}
