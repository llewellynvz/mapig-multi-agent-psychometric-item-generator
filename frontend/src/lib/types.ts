/**
 * Types aligned with MAPIG API (FinalOutput, UserRequest, etc.)
 */

export interface UserRequest {
  construct_name: string;
  construct_definition: string;
  target_population: string;
  response_scale: string;
  item_count?: number;
  constraints?: string[];
  native_construct?: string;
  example_item?: string;
  approved_domains?: string[];
  exclude_sources?: string[];
}

export interface FinalItem {
  item_text: string;
  construct_name: string;
  rationale: string;
  evidence_citations: string[];
}

export interface AuditMetadata {
  thread_id: string;
  run_id: string;
  timestamp_utc: string;
  iteration_count: number;
  stop_reason: string;
  model_info: Record<string, unknown>;
  approved_sources: string[];
}

export interface FinalOutput {
  final_items: FinalItem[];
  audit: AuditMetadata;
}

export interface HealthResponse {
  status: string;
  mode?: string;
}
