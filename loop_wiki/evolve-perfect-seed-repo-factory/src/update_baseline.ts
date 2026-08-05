import { readFileSync, writeFileSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { computeStats } from "./stats";

const args = Bun.argv.slice(2);
const packetIndex = args.indexOf("--packet");
const packetPath = packetIndex >= 0 ? args[packetIndex + 1] : undefined;
if (!packetPath) throw new Error("usage: update_baseline.ts --packet <absolute-path>");
if (!isAbsolute(packetPath)) throw new Error("baseline packet path must be absolute");
const packet = JSON.parse(readFileSync(packetPath, "utf8"));
if (
  packet.packet_kind !== "baseline-update" ||
  !["admitted", "reviewed"].includes(packet.packet_state) ||
  packet.human_gate !== "required_before_baseline_update"
) {
  throw new Error("baseline update requires an admitted baseline-update packet and human gate");
}
const current = computeStats();
if (JSON.stringify(packet.expected_stats) !== JSON.stringify(current))
  throw new Error("baseline packet expected_stats do not match current computed stats");
const outputIndex = args.indexOf("--output");
const output =
  outputIndex >= 0 ? args[outputIndex + 1] : resolve(import.meta.dir, "..", "baselines", "seed-stats.json");
if (!output || !isAbsolute(output)) throw new Error("baseline output must be absolute");
writeFileSync(output, `${JSON.stringify(current, null, 2)}\n`, "utf8");
console.log("PASS: governed seed stats baseline update");
