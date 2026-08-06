#!/usr/bin/env bun
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

type Platform = "local-forgejo" | "external-forgejo" | "github" | "gitlab" | "non-forgejo";
type LoopSize = "small" | "large";
type Operation =
  | "status"
  | "login"
  | "repository-bootstrap"
  | "issue"
  | "pull-request"
  | "merge"
  | "git-write"
  | "recover"
  | "none";
type AuthState = "authenticated" | "login-required" | "not-selected";
type RequestState = "absent" | "projected" | "admitted";

export type RouteInput = {
  schema_version: "forgejo-loop-route-input@v1";
  platform: Platform;
  loop_size: LoopSize;
  operation: Operation;
  auth_state: AuthState;
  request_state: RequestState;
  repo_local_operator_ready: boolean;
};

export type Route = {
  schema_version: "forgejo-loop-route@v1";
  status: "routed" | "not-applicable";
  actor: string;
  mode: string;
  mutation_allowed: boolean;
  next_mode: string;
  next_prompt: string;
  constraints: string[];
};

const INPUT_FIELDS = [
  "schema_version",
  "platform",
  "loop_size",
  "operation",
  "auth_state",
  "request_state",
  "repo_local_operator_ready",
] as const;
const PLATFORMS = new Set<Platform>(["local-forgejo", "external-forgejo", "github", "gitlab", "non-forgejo"]);
const LOOP_SIZES = new Set<LoopSize>(["small", "large"]);
const OPERATIONS = new Set<Operation>([
  "status",
  "login",
  "repository-bootstrap",
  "issue",
  "pull-request",
  "merge",
  "git-write",
  "recover",
  "none",
]);
const AUTH_STATES = new Set<AuthState>(["authenticated", "login-required", "not-selected"]);
const REQUEST_STATES = new Set<RequestState>(["absent", "projected", "admitted"]);
const CONSTRAINTS = [
  "loopback-only",
  "existing-chrome-only",
  "credential-secret-memory-only",
  "no-main-worktree-branch-switch",
  "no-force-push-or-gate-bypass",
  "git-and-typed-receipts-remain-evidence-ssot",
];

function object(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
  return value as Record<string, unknown>;
}

function enumValue<T extends string>(value: unknown, allowed: Set<T>, label: string): T {
  if (typeof value !== "string" || !allowed.has(value as T)) {
    throw new Error(`${label} is invalid`);
  }
  return value as T;
}

export function parseRouteInput(value: unknown): RouteInput {
  const input = object(value, "route input");
  const fields = Object.keys(input).sort();
  const expected = [...INPUT_FIELDS].sort();
  if (JSON.stringify(fields) !== JSON.stringify(expected)) {
    throw new Error("route input fields do not match the v1 contract");
  }
  if (input.schema_version !== "forgejo-loop-route-input@v1") {
    throw new Error("route input schema_version is invalid");
  }
  if (typeof input.repo_local_operator_ready !== "boolean") {
    throw new Error("repo_local_operator_ready must be boolean");
  }
  return {
    schema_version: "forgejo-loop-route-input@v1",
    platform: enumValue(input.platform, PLATFORMS, "platform"),
    loop_size: enumValue(input.loop_size, LOOP_SIZES, "loop_size"),
    operation: enumValue(input.operation, OPERATIONS, "operation"),
    auth_state: enumValue(input.auth_state, AUTH_STATES, "auth_state"),
    request_state: enumValue(input.request_state, REQUEST_STATES, "request_state"),
    repo_local_operator_ready: input.repo_local_operator_ready,
  };
}

function result(actor: string, mode: string, mutationAllowed: boolean, nextMode: string, nextPrompt: string): Route {
  return {
    schema_version: "forgejo-loop-route@v1",
    status: "routed",
    actor,
    mode,
    mutation_allowed: mutationAllowed,
    next_mode: nextMode,
    next_prompt: nextPrompt,
    constraints: CONSTRAINTS,
  };
}

function browserLogin(): Route {
  return result(
    "chrome:control-chrome",
    "forgejo/existing-chrome-login",
    false,
    "forgejo/live-precondition-check",
    "Use the user's existing Chrome tab, authenticate without exposing credentials, then rerun the read-only Forgejo precondition check.",
  );
}

function smallRoute(input: RouteInput): Route {
  if (input.operation === "status") {
    return result(
      "main-session",
      "forgejo/read-only-preflight",
      false,
      "forgejo/report-status",
      "Read Forgejo version, authenticated user, exact repository identity, Git remote and branch; emit no secret and perform no mutation.",
    );
  }
  if (input.operation === "login" || input.auth_state === "login-required") {
    return browserLogin();
  }
  if (input.operation === "recover") {
    return result(
      "main-session",
      "forgejo/bounded-recovery",
      false,
      "forgejo/degraded-outbox",
      "With explicit recovery authority, try at most three bounded restarts with canaries; otherwise append the operation to the idempotent outbox and block merge, release and admission.",
    );
  }
  if (input.operation === "repository-bootstrap") {
    if (input.request_state !== "admitted") {
      return result(
        "main-session",
        "forgejo/project-repository-bootstrap-request",
        false,
        "forgejo/human-admit",
        "Project one local-only repository bootstrap request with exact owner, name and visibility; do not create or configure a remote before admission.",
      );
    }
    return result(
      "chrome:control-chrome",
      "forgejo/execute-repository-bootstrap",
      true,
      "repo-local/configure-forgejo-remote",
      "Create exactly one admitted local repository in the existing Chrome session, reopen its owner/name/visibility, then delegate remote configuration to the repo-local operator.",
    );
  }
  if (input.operation === "git-write") {
    return result(
      "repo-terminal-operator",
      "repo-local/terminal-write",
      input.request_state === "admitted",
      "forgejo/readback-git-handoff",
      "Delegate the typed terminal slice to the output repo operator; never switch the main worktree branch, rewrite origin, force push or bypass gates.",
    );
  }
  if (input.operation === "none") {
    throw new Error("local Forgejo route requires a concrete operation");
  }
  if (input.request_state === "absent") {
    return result(
      "main-session",
      "forgejo/project-typed-request",
      false,
      "forgejo/live-precondition-check",
      "Project and schema-validate one hash-bound Forgejo request before any external mutation.",
    );
  }
  if (!input.repo_local_operator_ready && input.operation !== "issue") {
    return result(
      "repo-terminal-operator",
      "repo-local/prepare-forgejo-handoff",
      false,
      "forgejo/live-precondition-check",
      "Finish the repo-local code-quality, production-use, branch and commit handoff before creating or merging a pull request.",
    );
  }
  if (input.request_state !== "admitted") {
    return result(
      "chrome:control-chrome",
      "forgejo/live-precondition-check",
      false,
      "forgejo/human-admit",
      "In the existing Chrome session, verify authentication, exact repository and idempotency marker; stop before mutation until the typed request is admitted.",
    );
  }
  return result(
    "chrome:control-chrome",
    `forgejo/execute-${input.operation}`,
    true,
    "forgejo/readback-and-project-next",
    "Execute exactly one admitted local Forgejo operation in the existing Chrome session, then reopen and hash-bind its identity before advancing.",
  );
}

export function routeForgejoOperation(value: unknown): Route {
  const input = parseRouteInput(value);
  if (input.platform !== "local-forgejo") {
    return {
      schema_version: "forgejo-loop-route@v1",
      status: "not-applicable",
      actor: "none",
      mode: "none",
      mutation_allowed: false,
      next_mode: "route/platform-owner",
      next_prompt:
        "Forgejo loop ops only handles the allowlisted local Forgejo; route this request to the platform-specific owner.",
      constraints: CONSTRAINTS,
    };
  }
  if (input.loop_size === "large") {
    return result(
      "macro-loop",
      "forgejo/project-bounded-small-loop",
      false,
      "small-loop/forgejo-terminal-slice",
      "Project one highest-priority terminal slice with an idempotency key; keep at most ten open gaps and one in-progress slice per repo, then invoke the small loop.",
    );
  }
  return smallRoute(input);
}

type Case = {
  id: string;
  should_trigger: boolean;
  polarity: "positive" | "negative";
  input: unknown;
  expected: Partial<Route>;
};

function assertExpected(actual: Route, expected: Partial<Route>, id: string) {
  for (const [key, value] of Object.entries(expected)) {
    if (JSON.stringify(actual[key as keyof Route]) !== JSON.stringify(value)) {
      throw new Error(`${id} expected ${key}=${JSON.stringify(value)}`);
    }
  }
}

export function selftest(): void {
  const path = resolve(import.meta.dir, "../cases.json");
  const cases = JSON.parse(readFileSync(path, "utf8")) as Case[];
  if (cases.length < 10 || cases.length > 20) {
    throw new Error("cases.json must contain 10-20 cases");
  }
  const triggerTrue = cases.filter((item) => item.should_trigger).length;
  const triggerFalse = cases.length - triggerTrue;
  const positive = cases.filter((item) => item.polarity === "positive").length;
  const negative = cases.length - positive;
  if (Math.min(triggerTrue, triggerFalse, positive, negative) < 5) {
    throw new Error("cases.json needs at least five cases per trigger/polarity arm");
  }
  for (const item of cases) {
    const actual = routeForgejoOperation(item.input);
    if (item.should_trigger !== (actual.status === "routed")) {
      throw new Error(`${item.id} trigger verdict mismatch`);
    }
    assertExpected(actual, item.expected, item.id);
  }
  console.log(`SELFTEST GREEN forgejo-loop-ops ${cases.length}/${cases.length}`);
}

function cliFailure(error: unknown): Record<string, unknown> {
  return {
    schema_version: "forgejo-loop-route-error@v1",
    status: "failed",
    reason: "invalid-input",
    detail: error instanceof Error ? error.message : "unexpected route failure",
  };
}

if (import.meta.main) {
  try {
    if (process.argv.length === 3 && process.argv[2] === "--selftest") {
      selftest();
    } else if (process.argv.length === 4 && process.argv[2] === "--input" && process.argv[3]) {
      const input = JSON.parse(readFileSync(process.argv[3], "utf8"));
      console.log(JSON.stringify(routeForgejoOperation(input)));
    } else {
      throw new Error("usage: route.ts --input <json> | --selftest");
    }
  } catch (error) {
    console.log(JSON.stringify(cliFailure(error)));
    process.exitCode = 2;
  }
}
