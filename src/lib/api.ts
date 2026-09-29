/**
 * Single config for MAPIG API base URL.
 * All client requests use this base.
 *
 * Resolution order:
 * 1. NEXT_PUBLIC_API_PROXY=1 -> "/api/mapig", the same-origin Next route handler that
 *    forwards to the backend and injects the server-only MAPIG_API_KEY.
 * 2. NEXT_PUBLIC_API_URL, when set (an empty string means same-origin).
 * 3. "" (same-origin) on a Vercel build, where vercel.json rewrites /v1/* and /healthz
 *    to the Python function; http://localhost:8000 otherwise (local dev).
 *
 * MAPIG_ON_VERCEL is inlined at build time by next.config.js.
 */
export function resolveApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_PROXY === "1") return "/api/mapig";
  const explicit = process.env.NEXT_PUBLIC_API_URL;
  if (explicit !== undefined) return explicit;
  return process.env.MAPIG_ON_VERCEL === "1" ? "" : "http://localhost:8000";
}

export const API_BASE_URL = resolveApiBaseUrl();

export const HEALTH_URL = `${API_BASE_URL}/healthz`;
export const GENERATE_ITEMS_URL = `${API_BASE_URL}/v1/generate-items`;
export const GENERATE_ITEMS_STREAM_URL = `${API_BASE_URL}/v1/generate-items-stream`;
export const RUN_STATUS_URL = (threadId: string) =>
  `${API_BASE_URL}/v1/runs/${encodeURIComponent(threadId)}/status`;

export interface ProgressEvent {
  type: "start" | "node_start" | "iteration" | "complete" | "error" | "log" | "status" | "warning";
  node?: string;
  display_name?: string;
  iteration?: number;
  run_id?: string;
  thread_id?: string;
  data?: unknown;
  message?: string;
  trace?: string;

  // Log event fields
  timestamp?: string;
  level?: "info" | "warning" | "error";
  source?: string;
  metadata?: Record<string, unknown>;
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
