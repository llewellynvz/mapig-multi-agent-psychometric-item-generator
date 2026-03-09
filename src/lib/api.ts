/**
 * Single config for MAPIG API base URL.
 * All client requests use this base.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const HEALTH_URL = `${API_BASE_URL}/healthz`;
export const GENERATE_ITEMS_URL = `${API_BASE_URL}/v1/generate-items`;
export const GENERATE_ITEMS_STREAM_URL = `${API_BASE_URL}/v1/generate-items-stream`;
export const RUN_STATUS_URL = (threadId: string) =>
  `${API_BASE_URL}/v1/runs/${encodeURIComponent(threadId)}/status`;

export interface ProgressEvent {
  type: "start" | "node_start" | "iteration" | "complete" | "error";
  node?: string;
  display_name?: string;
  iteration?: number;
  run_id?: string;
  thread_id?: string;
  data?: unknown;
  message?: string;
  trace?: string;
}

export interface RunStatusResponse {
  thread_id: string;
  run_id: string;
  status: "running" | "complete" | "error";
  current_node?: string | null;
  display_name?: string | null;
  iteration?: number;
  error?: string | null;
  final_output?: unknown;
  started_at?: string;
  updated_at?: string;
}
