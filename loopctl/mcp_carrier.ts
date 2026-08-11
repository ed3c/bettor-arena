import { existsSync, readFileSync } from "node:fs";
import {
  McpError,
  assertObject,
  safeArtifactRef,
  safeJoin,
  sha256,
  type GeneratedTool,
} from "./mcp_contract.ts";
import { materializeInlineBundle } from "./mcp_execution.ts";

export const CLOSED_INLINE_BUNDLE_KIND = "closed-inline-bundle@1.0.0";

export interface PreparedInlineCarrier {
  argv: string[];
  output: string;
  resultFile: string;
}

export interface InlineDelivery {
  result: Record<string, unknown>;
  artifacts: Array<{
    kind: unknown;
    sha256: string;
    content_base64: string;
  }>;
}

export function prepareInlineCarrier(
  tool: GeneratedTool,
  base: string,
  argumentsValue: unknown,
  maxBytes: number,
): PreparedInlineCarrier {
  const carrier = tool._carrier;
  if (!carrier) throw new McpError("tool has no closed inline carrier");
  if (carrier.kind !== CLOSED_INLINE_BUNDLE_KIND) {
    throw new McpError(`unsupported carrier: ${carrier.kind}`);
  }
  if (!carrier.result_file) {
    throw new McpError("closed inline carrier has no result_file");
  }
  const materialized = materializeInlineBundle(base, argumentsValue, maxBytes);
  return {
    argv: [
      tool._argv.loop,
      tool._argv.mode,
      "--packet",
      materialized.packet,
      "--output",
      materialized.output,
      "--json",
    ],
    output: materialized.output,
    resultFile: safeArtifactRef(carrier.result_file),
  };
}

export function collectInlineDelivery(
  output: string,
  maxBytes: number,
  resultFile: string,
): InlineDelivery {
  const resultPath = safeJoin(output, safeArtifactRef(resultFile));
  if (!existsSync(resultPath)) {
    throw new McpError(`inline delivery result is absent: ${resultFile}`);
  }
  const resultBytes = readFileSync(resultPath);
  let total = resultBytes.length;
  if (total > maxBytes) {
    throw new McpError("inline delivery result exceeds policy limit");
  }

  let result: Record<string, unknown>;
  try {
    const parsed = JSON.parse(resultBytes.toString("utf8"));
    assertObject(parsed, "inline delivery result");
    result = parsed;
  } catch (error) {
    if (error instanceof McpError) throw error;
    throw new McpError(`inline delivery result is not JSON: ${String(error)}`);
  }

  const rawArtifacts = result.artifacts;
  if (!Array.isArray(rawArtifacts)) {
    throw new McpError("inline delivery artifacts must be an array");
  }
  const artifacts: InlineDelivery["artifacts"] = [];
  for (const [index, raw] of rawArtifacts.entries()) {
    assertObject(raw, `inline delivery artifacts[${index}]`);
    const artifactRef = safeArtifactRef(raw.artifact_ref);
    if (typeof raw.sha256 !== "string" || !/^[0-9a-f]{64}$/.test(raw.sha256)) {
      throw new McpError(
        `inline delivery artifacts[${index}] has invalid sha256`,
      );
    }
    const content = readFileSync(safeJoin(output, artifactRef));
    total += content.length;
    if (total > maxBytes) {
      throw new McpError("inline delivery exceeds policy limit");
    }
    if (sha256(content) !== raw.sha256) {
      throw new McpError(
        `inline delivery artifact digest mismatch: ${artifactRef}`,
      );
    }
    artifacts.push({
      kind: raw.kind,
      sha256: raw.sha256,
      content_base64: content.toString("base64"),
    });
  }
  return { result, artifacts };
}

export function attachInlineDelivery(
  payload: Record<string, unknown>,
  tool: GeneratedTool,
  prepared: PreparedInlineCarrier,
  maxBytes: number,
): void {
  const delivery = collectInlineDelivery(
    prepared.output,
    maxBytes,
    prepared.resultFile,
  );
  payload.artifacts = [];
  payload.inline_delivery = delivery;

  // Compatibility projection for the current CTG consumer. New carriers use
  // inline_delivery and do not acquire a CTG-specific response contract.
  if (tool._argv.loop === "ctg") {
    payload.ctg_delivery = {
      route_result: delivery.result,
      artifacts: delivery.artifacts,
    };
  }
}
