#!/usr/bin/env bun
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  EnvironmentContractError,
  ID,
  closedObject,
  readJson,
  sha256Json,
  uniqueStrings,
  withDigest,
  writeJson,
} from "./environment_types.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = resolve(HERE, "..");
const CONTRACT_SCHEMA = "bettor-arena/browser-contract/v2";
const STATUS_SCHEMA = "bettor-arena/browser-status/v1";
const ROUTE_FIELDS = [
  "id",
  "workflow",
  "actor",
  "surface",
  "transport",
  "session",
  "environment",
  "support",
  "assurance",
  "evidence_state",
  "receipt",
  "fallback_to",
  "output_trust",
];
const EVIDENCE_STATES = ["PASS", "FAIL", "ABSENT", "NOT_EXERCISED", "NOT_IMPLEMENTED"] as const;
const OUTPUT_TRUST_STATES = ["trusted-artifact", "untrusted-raw", "primary-evidence", "candidate-only"] as const;

type Support = "supported" | "unsupported" | "not-implemented";
type Assurance = "declared" | "offline-exercised" | "live-exercised";
interface Actor {
  category: "actor";
  surfaces: string[];
}
interface Surface {
  category: "surface";
  actor: string;
  kind: string;
}
interface Session {
  category: "session";
  credential_bearing: boolean;
  sync_policy: "none" | "forbidden";
  environment: "none" | "local" | "cloud";
}
interface Transport {
  category: "transport";
  implemented: boolean;
  runtime_scope: "local" | "cloud" | "local-cloud";
  session_owner: string;
  compatible_actors: string[];
  capabilities: string[];
}
interface BrowserRoute {
  id: string;
  workflow: string;
  actor: string;
  surface: string;
  transport: string | null;
  session: string;
  environment: "local" | "cloud" | "local-cloud";
  support: Support;
  assurance: Assurance;
  evidence_state: "PASS" | "FAIL" | "ABSENT" | "NOT_EXERCISED" | "NOT_IMPLEMENTED";
  receipt: string | null;
  fallback_to: string[];
  output_trust: "trusted-artifact" | "untrusted-raw" | "primary-evidence" | "candidate-only";
}
interface BrowserContract {
  schema: typeof CONTRACT_SCHEMA;
  actors: Record<string, Actor>;
  surfaces: Record<string, Surface>;
  sessions: Record<string, Session>;
  transports: Record<string, Transport>;
  workflows: Record<string, Record<string, unknown>>;
  routes: BrowserRoute[];
}

function objectRecord(value: unknown, label: string): Record<string, Record<string, unknown>> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new EnvironmentContractError(`${label}: object required`);
  return value as Record<string, Record<string, unknown>>;
}

function requiredEntry<T>(records: Record<string, T>, id: string, label: string): T {
  const value = records[id];
  if (value === undefined) throw new EnvironmentContractError(`${label}: unknown entry ${id}`);
  return value;
}

function requiredMapEntry<T>(records: ReadonlyMap<string, T>, id: string, label: string): T {
  const value = records.get(id);
  if (value === undefined) throw new EnvironmentContractError(`${label}: unknown entry ${id}`);
  return value;
}

function runtimeSupports(scope: Transport["runtime_scope"], environment: BrowserRoute["environment"]): boolean {
  return scope === "local-cloud" || scope === environment;
}

function validateActorRecords(records: Record<string, Record<string, unknown>>): Record<string, Actor> {
  const result: Record<string, Actor> = {};
  for (const [id, value] of Object.entries(records)) {
    closedObject(value, ["category", "surfaces"], `actor ${id}`);
    if (!ID.test(id) || value.category !== "actor")
      throw new EnvironmentContractError(`actor ${id}: invalid identity/category`);
    result[id] = { category: "actor", surfaces: uniqueStrings(value.surfaces, `actor ${id}.surfaces`) };
  }
  return result;
}

function validateSurfaceRecords(records: Record<string, Record<string, unknown>>): Record<string, Surface> {
  const result: Record<string, Surface> = {};
  for (const [id, value] of Object.entries(records)) {
    closedObject(value, ["category", "actor", "kind"], `surface ${id}`);
    if (
      !ID.test(id) ||
      value.category !== "surface" ||
      typeof value.actor !== "string" ||
      typeof value.kind !== "string"
    )
      throw new EnvironmentContractError(`surface ${id}: invalid`);
    result[id] = { category: "surface", actor: value.actor, kind: value.kind };
  }
  return result;
}

function validateSessionRecords(records: Record<string, Record<string, unknown>>): Record<string, Session> {
  const result: Record<string, Session> = {};
  for (const [id, value] of Object.entries(records)) {
    closedObject(value, ["category", "credential_bearing", "sync_policy", "environment"], `session ${id}`);
    if (!ID.test(id) || value.category !== "session" || typeof value.credential_bearing !== "boolean")
      throw new EnvironmentContractError(`session ${id}: invalid`);
    if (
      !["none", "forbidden"].includes(String(value.sync_policy)) ||
      !["none", "local", "cloud"].includes(String(value.environment))
    )
      throw new EnvironmentContractError(`session ${id}: invalid policy/environment`);
    if (value.credential_bearing && value.sync_policy !== "forbidden")
      throw new EnvironmentContractError(`session ${id}: credential-bearing profiles may never sync`);
    if (!value.credential_bearing && value.sync_policy !== "none")
      throw new EnvironmentContractError(`session ${id}: non-credential session uses an unnecessary sync policy`);
    result[id] = {
      category: "session",
      credential_bearing: value.credential_bearing,
      sync_policy: value.sync_policy as Session["sync_policy"],
      environment: value.environment as Session["environment"],
    };
  }
  return result;
}

function validateTransportRecords(
  records: Record<string, Record<string, unknown>>,
  actors: Record<string, Actor>,
  sessions: Record<string, Session>,
): Record<string, Transport> {
  const result: Record<string, Transport> = {};
  for (const [id, value] of Object.entries(records)) {
    closedObject(
      value,
      ["category", "implemented", "runtime_scope", "session_owner", "compatible_actors", "capabilities"],
      `transport ${id}`,
    );
    if (
      !ID.test(id) ||
      value.category !== "transport" ||
      typeof value.implemented !== "boolean" ||
      typeof value.session_owner !== "string"
    )
      throw new EnvironmentContractError(`transport ${id}: invalid`);
    if (!["local", "cloud", "local-cloud"].includes(String(value.runtime_scope)))
      throw new EnvironmentContractError(`transport ${id}: invalid runtime scope`);
    if (!(value.session_owner in sessions))
      throw new EnvironmentContractError(`transport ${id}: unknown session owner ${value.session_owner}`);
    const compatibleActors = uniqueStrings(value.compatible_actors, `transport ${id}.compatible_actors`);
    for (const actor of compatibleActors)
      if (!(actor in actors)) throw new EnvironmentContractError(`transport ${id}: unknown actor ${actor}`);
    const capabilities = uniqueStrings(value.capabilities, `transport ${id}.capabilities`);
    const session = requiredEntry(sessions, value.session_owner, `transport ${id}.session_owner`);
    if (capabilities.includes("signed-in-session") !== session.credential_bearing)
      throw new EnvironmentContractError(`transport ${id}: signed-in capability/session ownership disagree`);
    if (value.runtime_scope === "local" && session.environment === "cloud")
      throw new EnvironmentContractError(`transport ${id}: local route owns a cloud profile`);
    if (value.runtime_scope === "cloud" && session.environment === "local")
      throw new EnvironmentContractError(`transport ${id}: cloud route owns a local profile`);
    if (value.runtime_scope === "local-cloud" && session.credential_bearing)
      throw new EnvironmentContractError(
        `transport ${id}: cross-environment transport may not move a credential profile`,
      );
    result[id] = {
      category: "transport",
      implemented: value.implemented,
      runtime_scope: value.runtime_scope as Transport["runtime_scope"],
      session_owner: value.session_owner,
      compatible_actors: compatibleActors,
      capabilities,
    };
  }
  return result;
}

function validateWorkflows(workflows: Record<string, Record<string, unknown>>): void {
  const expected = ["gemini-conversation-research", "dr-research-loop", "external-verify"];
  if (JSON.stringify(Object.keys(workflows).sort()) !== JSON.stringify(expected.sort()))
    throw new EnvironmentContractError("browser workflows must be exactly GCR, DR, and external-verify");
  const gcr = requiredEntry(workflows, "gemini-conversation-research", "browser workflows");
  if (
    gcr.skill !== "gemini-conversation-research" ||
    gcr.browser_required !== true ||
    gcr.body_to_main_context !== "denied" ||
    gcr.artifact_output !== "file-only" ||
    gcr.metadata_receipt_max_chars !== 4096 ||
    gcr.route_selection !== "explicit"
  ) {
    throw new EnvironmentContractError(
      "GCR must require explicit browser routing, file-only body extraction, and bounded metadata",
    );
  }
  uniqueStrings(gcr.required_capabilities, "GCR required_capabilities");
  const dr = requiredEntry(workflows, "dr-research-loop", "browser workflows");
  if (
    dr.skill !== "dr-research-loop" ||
    dr.core_browser_required !== false ||
    dr.stage1_browser !== "optional" ||
    dr.stage1_output_trust !== "untrusted-raw" ||
    dr.route_selection !== "explicit"
  ) {
    throw new EnvironmentContractError("DR core must remain browser-optional and subscription Stage 1 untrusted");
  }
  const external = requiredEntry(workflows, "external-verify", "browser workflows");
  if (
    external.skill !== "external-verify" ||
    external.browser_required !== false ||
    external.primary_evidence !== "raw-primary" ||
    external.route_selection !== "explicit"
  ) {
    throw new EnvironmentContractError("external-verify must remain raw-primary-first and browser-optional");
  }
  const priority = uniqueStrings(external.route_priority, "external-verify route_priority");
  if (priority[0] !== "github-api" || priority[1] !== "raw-http" || priority.indexOf("playwright-cdp") < 2)
    throw new EnvironmentContractError("external-verify route priority silently upgraded browser evidence");
}

export function validateContract(value: unknown): BrowserContract {
  closedObject(
    value,
    ["schema", "actors", "surfaces", "sessions", "transports", "workflows", "routes"],
    "browser contract",
  );
  if (value.schema !== CONTRACT_SCHEMA)
    throw new EnvironmentContractError(`browser contract schema must be ${CONTRACT_SCHEMA}`);
  const actors = validateActorRecords(objectRecord(value.actors, "actors"));
  const surfaces = validateSurfaceRecords(objectRecord(value.surfaces, "surfaces"));
  const sessions = validateSessionRecords(objectRecord(value.sessions, "sessions"));
  const transports = validateTransportRecords(objectRecord(value.transports, "transports"), actors, sessions);
  const workflows = objectRecord(value.workflows, "workflows");
  validateWorkflows(workflows);
  for (const [surfaceId, surface] of Object.entries(surfaces)) {
    const actor = requiredEntry(actors, surface.actor, `surface ${surfaceId}.actor`);
    if (!actor.surfaces.includes(surfaceId))
      throw new EnvironmentContractError(`surface ${surfaceId}: actor mapping is not bidirectional`);
  }
  if (!Array.isArray(value.routes)) throw new EnvironmentContractError("browser routes array required");
  const seen = new Set<string>();
  const routes = value.routes.map((raw, index) => {
    closedObject(raw, ROUTE_FIELDS, `route[${index}]`);
    if (typeof raw.id !== "string" || !ID.test(raw.id) || seen.has(raw.id))
      throw new EnvironmentContractError(`route[${index}]: invalid or duplicate id`);
    seen.add(raw.id);
    for (const field of [
      "workflow",
      "actor",
      "surface",
      "session",
      "environment",
      "support",
      "assurance",
      "evidence_state",
      "output_trust",
    ])
      if (typeof raw[field] !== "string")
        throw new EnvironmentContractError(`route ${raw.id}: ${field} must be string`);
    if (raw.transport !== null && typeof raw.transport !== "string")
      throw new EnvironmentContractError(`route ${raw.id}: transport must be string or null`);
    if (raw.receipt !== null && typeof raw.receipt !== "string")
      throw new EnvironmentContractError(`route ${raw.id}: receipt must be string or null`);
    const fallback = uniqueStrings(raw.fallback_to, `route ${raw.id}.fallback_to`);
    const workflow = raw.workflow as string;
    const actorId = raw.actor as string;
    const surfaceId = raw.surface as string;
    const sessionId = raw.session as string;
    const environment = raw.environment as string;
    const support = raw.support as string;
    const assurance = raw.assurance as string;
    const evidenceState = raw.evidence_state as string;
    const outputTrust = raw.output_trust as string;
    const workflowRecord = requiredEntry(workflows, workflow, `route ${raw.id}.workflow`);
    requiredEntry(actors, actorId, `route ${raw.id}.actor`);
    const surface = requiredEntry(surfaces, surfaceId, `route ${raw.id}.surface`);
    const session = requiredEntry(sessions, sessionId, `route ${raw.id}.session`);
    if (surface.actor !== actorId)
      throw new EnvironmentContractError(`route ${raw.id}: actor and product surface collapsed`);
    if (
      !["local", "cloud", "local-cloud"].includes(environment) ||
      !["supported", "unsupported", "not-implemented"].includes(support) ||
      !["declared", "offline-exercised", "live-exercised"].includes(assurance) ||
      !EVIDENCE_STATES.includes(evidenceState as BrowserRoute["evidence_state"]) ||
      !OUTPUT_TRUST_STATES.includes(outputTrust as BrowserRoute["output_trust"])
    )
      throw new EnvironmentContractError(`route ${raw.id}: invalid state`);
    const route: BrowserRoute = {
      id: raw.id,
      workflow,
      actor: actorId,
      surface: surfaceId,
      transport: raw.transport as string | null,
      session: sessionId,
      environment: environment as BrowserRoute["environment"],
      support: support as Support,
      assurance: assurance as Assurance,
      evidence_state: evidenceState as BrowserRoute["evidence_state"],
      receipt: raw.receipt as string | null,
      fallback_to: fallback,
      output_trust: outputTrust as BrowserRoute["output_trust"],
    };
    if (route.actor === "agy" && session.credential_bearing)
      throw new EnvironmentContractError(`route ${route.id}: agy is a replay actor, not a signed-in browser owner`);
    if (route.actor === "codex-cli" && route.transport === "codex-chrome-extension")
      throw new EnvironmentContractError(`route ${route.id}: bare Codex CLI was upgraded to a desktop Chrome surface`);
    if (route.support === "unsupported") {
      if (route.transport !== null || route.session !== "none")
        throw new EnvironmentContractError(
          `route ${route.id}: unsupported route may not carry a fake transport/session`,
        );
    } else {
      if (!route.transport) throw new EnvironmentContractError(`route ${route.id}: known transport required`);
      const transport = requiredEntry(transports, route.transport, `route ${route.id}.transport`);
      if (route.support === "supported" && !transport.implemented)
        throw new EnvironmentContractError(`route ${route.id}: unimplemented transport declared supported`);
      if (route.support === "not-implemented" && transport.implemented)
        throw new EnvironmentContractError(`route ${route.id}: implemented transport mislabeled not-implemented`);
      if (!transport.compatible_actors.includes(route.actor))
        throw new EnvironmentContractError(`route ${route.id}: actor cannot use transport ${route.transport}`);
      if (transport.session_owner !== route.session)
        throw new EnvironmentContractError(`route ${route.id}: session owner differs from transport`);
      if (!runtimeSupports(transport.runtime_scope, route.environment))
        throw new EnvironmentContractError(`route ${route.id}: environment exceeds transport scope`);
    }
    if (session.credential_bearing && session.sync_policy !== "forbidden")
      throw new EnvironmentContractError(`route ${route.id}: credential profile may move between environments`);
    if (route.assurance === "live-exercised") {
      if (route.evidence_state !== "PASS" || !route.receipt)
        throw new EnvironmentContractError(`route ${route.id}: live assurance has no immutable PASS receipt`);
    } else if (route.receipt !== null || route.evidence_state === "PASS")
      throw new EnvironmentContractError(`route ${route.id}: non-live route carries fake live evidence`);
    if (route.workflow === "gemini-conversation-research" && route.support === "supported") {
      const required = uniqueStrings(workflowRecord.required_capabilities, `route ${route.id}.required_capabilities`);
      if (!route.transport) throw new EnvironmentContractError(`route ${route.id}: GCR transport required`);
      const capabilities = requiredEntry(transports, route.transport, `route ${route.id}.transport`).capabilities;
      const missing = required.filter((capability) => !capabilities.includes(capability));
      if (missing.length)
        throw new EnvironmentContractError(`route ${route.id}: GCR capabilities missing ${missing.join(", ")}`);
      if (route.output_trust !== "trusted-artifact")
        throw new EnvironmentContractError(`route ${route.id}: GCR body is not isolated as a trusted file artifact`);
    }
    return { ...route, fallback_to: fallback };
  });
  const routeMap = new Map(routes.map((route) => [route.id, route]));
  for (const route of routes) {
    for (const fallback of route.fallback_to) {
      const target = routeMap.get(fallback);
      if (!target || target.workflow !== route.workflow || fallback === route.id)
        throw new EnvironmentContractError(`route ${route.id}: invalid explicit fallback ${fallback}`);
    }
  }
  const requiredNegativeRoutes = ["gcr-codex-cli-native-chrome", "gcr-agy-signed-in", "gcr-cloud-browser"];
  for (const id of requiredNegativeRoutes)
    if (!routeMap.has(id)) throw new EnvironmentContractError(`browser contract lost negative route ${id}`);
  const codexChrome = requiredMapEntry(routeMap, "gcr-codex-cli-native-chrome", "browser negative routes");
  const agySignedIn = requiredMapEntry(routeMap, "gcr-agy-signed-in", "browser negative routes");
  const cloudBrowser = requiredMapEntry(routeMap, "gcr-cloud-browser", "browser negative routes");
  if (
    codexChrome.support !== "unsupported" ||
    agySignedIn.support !== "unsupported" ||
    cloudBrowser.support !== "not-implemented"
  ) {
    throw new EnvironmentContractError("browser negative route states drifted");
  }
  return { schema: CONTRACT_SCHEMA, actors, surfaces, sessions, transports, workflows, routes };
}

export function loadContract(root: string): BrowserContract {
  return validateContract(readJson(join(root, ".arena/browser/contract.json")));
}

export function status(root: string): Record<string, unknown> & { content_sha256: string } {
  const contract = loadContract(root);
  return withDigest({
    schema: STATUS_SCHEMA,
    contract_sha256: sha256Json(contract),
    offline_contract: "PASS",
    live_state: "NOT_EXERCISED",
    cloud_signed_in_broker: "NOT_IMPLEMENTED",
    routes: contract.routes.map((route) => ({
      id: route.id,
      workflow: route.workflow,
      support:
        route.support === "supported"
          ? "SUPPORTED"
          : route.support === "unsupported"
            ? "UNSUPPORTED"
            : "NOT_IMPLEMENTED",
      assurance: route.assurance,
      live_state: route.evidence_state,
      receipt: route.receipt,
      note:
        route.support === "supported"
          ? "A host-owned live receipt is required before promotion."
          : route.support === "unsupported"
            ? "Unsupported by category/ownership contract."
            : "Provider/session broker is not implemented.",
    })),
  });
}

function expectError(name: string, contract: BrowserContract, mutate: (copy: any) => void): void {
  const copy = JSON.parse(JSON.stringify(contract));
  mutate(copy);
  try {
    validateContract(copy);
  } catch {
    return;
  }
  throw new EnvironmentContractError(`selftest ${name}: mutation unexpectedly passed`);
}

export function selftest(root = DEFAULT_ROOT): number {
  const contract = loadContract(root);
  expectError("credential-sync", contract, (copy) => {
    copy.sessions["user-chrome-profile"].sync_policy = "none";
  });
  expectError("bare-codex-native-chrome", contract, (copy) => {
    const route = copy.routes.find((item: BrowserRoute) => item.id === "gcr-codex-cli-native-chrome");
    route.transport = "codex-chrome-extension";
    route.session = "user-chrome-profile";
    route.support = "supported";
  });
  expectError("agy-signed-in", contract, (copy) => {
    const route = copy.routes.find((item: BrowserRoute) => item.id === "gcr-agy-signed-in");
    route.transport = "claude-in-chrome";
    route.session = "user-chrome-profile";
    route.support = "supported";
  });
  expectError("cloud-provider-upgrade", contract, (copy) => {
    copy.routes.find((item: BrowserRoute) => item.id === "gcr-cloud-browser").support = "supported";
  });
  expectError("gcr-body-leak", contract, (copy) => {
    copy.workflows["gemini-conversation-research"].body_to_main_context = "allowed";
  });
  expectError("dr-core-browser", contract, (copy) => {
    copy.workflows["dr-research-loop"].core_browser_required = true;
  });
  expectError("browser-first-verification", contract, (copy) => {
    copy.workflows["external-verify"].route_priority = ["playwright-cdp", "github-api", "raw-http"];
  });
  expectError("fake-live-assurance", contract, (copy) => {
    copy.routes[0].assurance = "live-exercised";
  });
  expectError("invalid-evidence-state", contract, (copy) => {
    copy.routes[0].evidence_state = "UNKNOWN";
  });
  expectError("invalid-output-trust", contract, (copy) => {
    copy.routes[0].output_trust = "trusted-inline";
  });
  expectError("silent-fallback", contract, (copy) => {
    copy.routes[0].fallback_to = ["external-raw-http"];
  });
  console.log("SELFTEST GREEN: Browser Contract v2");
  return 0;
}

interface Options {
  root: string;
  command: "check" | "status" | null;
  selftest: boolean;
  output?: string;
}
function parse(argv: string[]): Options {
  const options: Options = { root: DEFAULT_ROOT, command: null, selftest: false };
  const rest = [...argv];
  while (rest.length) {
    const token = rest.shift()!;
    if (token === "check" || token === "status") {
      options.command = token;
      continue;
    }
    if (token === "--selftest") {
      options.selftest = true;
      continue;
    }
    if (token === "--root" || token === "--output") {
      const value = rest.shift();
      if (!value) throw new EnvironmentContractError(`${token} requires a value`);
      if (token === "--root") options.root = value;
      else options.output = value;
      continue;
    }
    throw new EnvironmentContractError(`unknown argument: ${token}`);
  }
  options.root = resolve(options.root);
  if (!options.selftest && !options.command) options.command = "check";
  return options;
}

export async function main(argv = process.argv.slice(2)): Promise<number> {
  try {
    const options = parse(argv);
    if (options.selftest) return selftest(options.root);
    const contract = loadContract(options.root);
    if (options.command === "check")
      console.log(`PASS Browser Contract v2 (${contract.routes.length} explicit routes)`);
    else {
      if (!options.output) throw new EnvironmentContractError("status requires --output");
      writeJson(resolve(options.output), status(options.root));
    }
    return 0;
  } catch (error) {
    console.error(`BROWSER-CONTRACT-RED ${String(error instanceof Error ? error.message : error)}`);
    return error instanceof EnvironmentContractError ? 2 : 64;
  }
}

if (resolve(process.argv[1] ?? "") === fileURLToPath(import.meta.url)) process.exit(await main());
