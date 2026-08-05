import { expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { CAPABILITIES } from "../src/capabilities";
import { runOperator } from "../src/operator";

test("operator produces exactly twenty dependency-valid local calls", () => {
  const root = resolve(import.meta.dir, "..");
  const results = runOperator(root, "Choose the next bounded implementation action");
  expect(results).toHaveLength(20);
  expect(new Set(results.map((entry) => entry.call_id)).size).toBe(20);
  for (const capability of CAPABILITIES) {
    const position = CAPABILITIES.findIndex((entry) => entry.call_id === capability.call_id);
    for (const dependency of capability.depends_on) {
      expect(CAPABILITIES.findIndex((entry) => entry.call_id === dependency)).toBeLessThan(position);
    }
  }
  expect(results.at(-1)?.output.admit_edge).toBe("human_required");
});

test("operator skill has balanced trigger and polarity cases", () => {
  const root = resolve(import.meta.dir, "..");
  const payload = JSON.parse(readFileSync(resolve(root, ".agents/skills/seed-repo-operator/cases.json"), "utf8"));
  expect(payload.cases).toHaveLength(10);
  expect(payload.cases.filter((entry: { should_trigger: boolean }) => entry.should_trigger)).toHaveLength(5);
  expect(payload.cases.filter((entry: { should_trigger: boolean }) => !entry.should_trigger)).toHaveLength(5);
  expect(payload.cases.filter((entry: { polarity: string }) => entry.polarity === "positive")).toHaveLength(5);
  expect(payload.cases.filter((entry: { polarity: string }) => entry.polarity === "negative")).toHaveLength(5);
});
