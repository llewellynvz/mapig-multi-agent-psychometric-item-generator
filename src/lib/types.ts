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
  model_provider?: "claude" | "openai";
  use_chatgpt_critics?: boolean;
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
  chatgpt_cost?: number;
  total_cost?: number;
  // Smart validation tracking
  smart_validation_used?: boolean;
  validation_model_used?: string;
}

export interface ReviewComment {
  type: 'linguistic' | 'bias' | 'content';
  item_index?: number;
  issue: string;
  severity: number;  // 1-5
  suggested_edit: string;
}

// Phase 7: v2.0 Analytics Types

export interface CorrelationCell {
  item_i_index: number;
  item_j_index: number;
  correlation: number;
  ci_low: number;
  ci_high: number;
}

export interface CorrelationMatrix {
  cells: CorrelationCell[];
  mcdonalds_omega: number;
  mean_inter_item_correlation: number;
  internal_consistency_flag: string;
  disclaimer: string;
}

export interface ComparisonInstrument {
  name: string;
  construct: string;
  source_citation: string;
  publication_year?: number;
  sample_items_count?: number;
  psychometric_properties?: string;
  similarity_rationale?: string;
}

export interface ConstructPairAnalysis {
  construct_a: string;
  construct_b: string;
  estimated_correlation?: number;
  discriminant_validity_flag?: string;
  reasoning?: string;
}

export interface CrossConstructComparison {
  target_construct: string;
  comparison_constructs: string[];
  analysis_summary: string;
  construct_pairs?: ConstructPairAnalysis[];
  disclaimer: string;
}

export interface FinalOutput {
  final_items: FinalItem[];
  audit: AuditMetadata;

  // Phase 03.1 enhancements: Optional metadata for complete export
  user_request?: UserRequest;
  linguistic_feedback?: ReviewComment[];
  bias_feedback?: ReviewComment[];
  content_feedback?: ReviewComment[];

  // Phase 7: v2.0 analytics fields
  correlation_matrix?: CorrelationMatrix;
  comparison_instruments?: ComparisonInstrument[];
  cross_construct_analysis?: CrossConstructComparison;
}

export interface HealthResponse {
  status: string;
  mode?: string;
}
