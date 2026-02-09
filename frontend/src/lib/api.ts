/**
 * Single config for MAPIG API base URL.
 * All client requests use this base.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const HEALTH_URL = `${API_BASE_URL}/healthz`;
export const GENERATE_ITEMS_URL = `${API_BASE_URL}/v1/generate-items`;
