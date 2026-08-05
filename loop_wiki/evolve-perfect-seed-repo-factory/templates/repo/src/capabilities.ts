import type { Capability } from "./contracts";

export const CAPABILITIES: Capability[] = [
  { call_id: "F01", function_name: "load_task_context", depends_on: [] },
  { call_id: "F02", function_name: "load_source_identity", depends_on: [] },
  { call_id: "F03", function_name: "inventory_local_evidence", depends_on: ["F01", "F02"] },
  { call_id: "F04", function_name: "extract_task_goal", depends_on: ["F01"] },
  { call_id: "F05", function_name: "extract_task_constraints", depends_on: ["F01"] },
  { call_id: "F06", function_name: "inspect_claims", depends_on: ["F03"] },
  { call_id: "F07", function_name: "bind_claims_to_evidence", depends_on: ["F06"] },
  { call_id: "F08", function_name: "classify_knowns_unknowns", depends_on: ["F04", "F05", "F06"] },
  { call_id: "F09", function_name: "inspect_repo_invariants", depends_on: ["F03"] },
  { call_id: "F10", function_name: "map_dependencies", depends_on: ["F09"] },
  { call_id: "F11", function_name: "detect_negative_space", depends_on: ["F08", "F09"] },
  { call_id: "F12", function_name: "propose_seed_architecture", depends_on: ["F07", "F10", "F11"] },
  { call_id: "F13", function_name: "build_counterfactual", depends_on: ["F12"] },
  { call_id: "F14", function_name: "compare_architectures", depends_on: ["F12", "F13"] },
  { call_id: "F15", function_name: "select_bounded_architecture", depends_on: ["F14"] },
  { call_id: "F16", function_name: "derive_public_interfaces", depends_on: ["F15"] },
  { call_id: "F17", function_name: "derive_verification_contract", depends_on: ["F16", "F11"] },
  { call_id: "F18", function_name: "derive_implementation_slices", depends_on: ["F16", "F17"] },
  { call_id: "F19", function_name: "audit_traceability", depends_on: ["F07", "F17", "F18"] },
  { call_id: "F20", function_name: "synthesize_next_action", depends_on: ["F19"] },
];
