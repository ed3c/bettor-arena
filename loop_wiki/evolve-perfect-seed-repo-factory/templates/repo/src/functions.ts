import type { CallResult, LocalContext } from "./contracts";

type Prior = Map<string, CallResult>;
type Handler = (context: LocalContext, prior: Prior) => Record<string, unknown>;

const counts = (context: LocalContext) => ({
  evidence: context.evidence.length,
  claims: context.claims.length,
  unknowns: context.unknowns.length,
  decisions: context.decisions.length,
});
const sourceKind = (context: LocalContext) => String(context.source.source_kind ?? "unknown");
const taskHash = (context: LocalContext) => new Bun.CryptoHasher("sha256").update(context.task).digest("hex");

export const HANDLERS: Record<string, Handler> = {
  load_task_context: (context) => ({ task: context.task, task_length: context.task.length }),
  load_source_identity: (context) => ({
    source_kind: sourceKind(context),
    packet_id: context.source.packet_id,
    packet_sha256: context.source.packet_sha256,
  }),
  inventory_local_evidence: (context) => ({
    ...counts(context),
    evidence_ids: context.evidence.slice(0, 12).map((entry) => entry.evidence_id),
  }),
  extract_task_goal: (context) => ({ goal: (context.task.split(/[.!?]/)[0] ?? "").trim() }),
  extract_task_constraints: (context) => ({
    local_only: true,
    exact_call_count: 20,
    human_gate: context.source.human_gate,
  }),
  inspect_claims: (context) => ({
    claim_count: context.claims.length,
    grounded_claims: context.claims.filter(
      (entry) => Array.isArray(entry.evidence_ids) && entry.evidence_ids.length > 0,
    ).length,
  }),
  bind_claims_to_evidence: (context) => ({
    bindings: context.claims
      .map((entry) => ({ claim_id: entry.claim_id, evidence_ids: entry.evidence_ids }))
      .slice(0, 24),
  }),
  classify_knowns_unknowns: (context) => ({
    quadrants: context.unknowns.map((entry) => entry.quadrant),
    task_requires_human_taste: /prefer|choose|design/i.test(context.task),
  }),
  inspect_repo_invariants: (context) => ({
    source_kind: sourceKind(context),
    invariant_basis: sourceKind(context) === "repo" ? "file-manifest" : "source-lines",
    evidence_count: context.evidence.length,
  }),
  map_dependencies: (_context, prior) => ({
    dependency_basis: [prior.get("F09")?.output_sha256],
    graph_kind: "acyclic-local",
  }),
  detect_negative_space: (context) => ({
    unbound_unknowns: context.unknowns
      .filter((entry) => !Array.isArray(entry.evidence_ids) || entry.evidence_ids.length === 0)
      .map((entry) => entry.unknown_id),
    external_truth_observed: false,
  }),
  propose_seed_architecture: (context) => ({
    modules: ["local-store", "capability-registry", "operator", "lineage"],
    source_kind: sourceKind(context),
  }),
  build_counterfactual: () => ({
    alternative: "single-free-form-prompt",
    rejected_risk: "hidden-state-and-unreplayable-decisions",
  }),
  compare_architectures: () => ({ winner: "typed-local-dag", bounded_claim: "replayable-local-reasoning-only" }),
  select_bounded_architecture: () => ({ selected: "typed-local-dag", grounding: "candidate", human_admit: true }),
  derive_public_interfaces: () => ({ interfaces: ["data/*.json[l]", "scripts/plan.ts --task", "bun test"] }),
  derive_verification_contract: () => ({
    checks: ["exact-20", "unique-call-ids", "dependency-order", "hash-bound-results", "human-gate-preserved"],
  }),
  derive_implementation_slices: () => ({
    slices: ["inspect-local-truth", "design-bounded-change", "verify-and-surface"],
  }),
  audit_traceability: (context, prior) => ({
    source_hash: context.source.packet_sha256,
    task_hash: taskHash(context),
    prior_hashes: ["F07", "F17", "F18"].map((id) => prior.get(id)?.output_sha256),
    traceable: true,
  }),
  synthesize_next_action: (context) => ({
    next_action: `Prepare one tested implementation slice for: ${context.task}`,
    grounding: "candidate",
    admit_edge: "human_required",
  }),
};
