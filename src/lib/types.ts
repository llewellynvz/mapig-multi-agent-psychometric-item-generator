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
  construct_exclusions?: string;
  native_construct?: string;
  example_item?: string;
  approved_domains?: string[];
  exclude_sources?: string[];
  human_feedback?: string;
  previous_items?: string[];
}

export interface DimensionScore {
  dimension: string;
  reasoning: string; // Empty string for passing dimensions (score >= 7), detailed for failing (score < 7)
  score: number;
}

export interface ItemValidation {
  item_index: number;
  item_text: string;
  dimension_scores: DimensionScore[];
  weighted_score: number;
  accept: boolean;
  attempt: number;
}

export interface FinalItem {
  item_text: string;
  construct_name: string;
  rationale: string;
  evidence_citations: string[];
  validation_result?: ItemValidation;
}

export interface AuditMetadata {
  thread_id: string;
  run_id: string;
  timestamp_utc: string;
  iteration_count: number;
  stop_reason: string;
  model_info: Record<string, unknown>;
  approved_sources: string[];
  validation_attempts?: number;
  validation_failures?: number;
  // Cost tracking fields (added in Phase 03)
  opus_cost?: number;
  sonnet_cost?: number;
  openai_cost?: number;
  total_cost?: number;
}

export interface ReviewComment {
  type: 'linguistic' | 'bias' | 'content';
  item_index?: number;
  issue: string;
  severity: number;  // 1-5
  suggested_edit: string;
}

export interface FinalOutput {
  final_items: FinalItem[];
  audit: AuditMetadata;

  // Phase 03.1 enhancements: Optional metadata for complete export
  user_request?: UserRequest;
  linguistic_feedback?: ReviewComment[];
  bias_feedback?: ReviewComment[];
  content_feedback?: ReviewComment[];
}

export interface HealthResponse {
  status: string;
  mode?: string;
}
