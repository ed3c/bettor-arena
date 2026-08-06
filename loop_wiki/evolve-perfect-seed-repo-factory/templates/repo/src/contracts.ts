export interface Capability {
  call_id: string;
  function_name: string;
  depends_on: string[];
}

export interface LocalContext {
  root: string;
  task: string;
  source: Record<string, unknown>;
  evidence: Array<Record<string, unknown>>;
  claims: Array<Record<string, unknown>>;
  unknowns: Array<Record<string, unknown>>;
  decisions: Array<Record<string, unknown>>;
}

export interface CallResult {
  call_id: string;
  function_name: string;
  input_sha256: string;
  output: Record<string, unknown>;
  output_sha256: string;
}
