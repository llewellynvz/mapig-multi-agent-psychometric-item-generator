/**
 * Single config for MAPIG API base URL.
 * All client requests use this base.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const HEALTH_URL = `${API_BASE_URL}/healthz`;
export const GENERATE_ITEMS_URL = `${API_BASE_URL}/v1/generate-items`;
export const GENERATE_ITEMS_STREAM_URL = `${API_BASE_URL}/v1/generate-items-stream`;

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