"use client";

import {
  GENERATE_ITEMS_URL,
  GENERATE_ITEMS_STREAM_URL,
  RUN_STATUS_URL,
  type ProgressEvent,
  type RunStatusResponse,
} from "@/lib/api";
import type { FinalOutput, UserRequest } from "@/lib/types";

export interface GenerateItemsParams {
  body: UserRequest;
  threadId?: string;
}

export async function generateItems({
  body,
  threadId,
}: GenerateItemsParams): Promise<FinalOutput> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (threadId) {
    headers["X-Thread-ID"] = threadId;
  }

  const res = await fetch(GENERATE_ITEMS_URL, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const rawText = await res.text();
    let detail: unknown;
    try {
      const errBody = JSON.parse(rawText) as { detail?: unknown };
      detail = errBody.detail;
    } catch {
      detail = undefined;
    }
    throw new GenerateError(res.status, detail, rawText);
  }

  return res.json() as Promise<FinalOutput>;
}

export class GenerateError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
    public rawText: string
  ) {
    super(`Generate failed: ${status}`);
    this.name = "GenerateError";
  }
}

export interface GenerateItemsStreamParams {
  body: UserRequest;
  threadId?: string;
  onProgress?: (event: ProgressEvent) => void;
}

export async function fetchRunStatus(threadId: string): Promise<RunStatusResponse> {
  const res = await fetch(RUN_STATUS_URL(threadId), {
    method: "GET",
  });
  if (!res.ok) {
    const rawText = await res.text();
    let detail: unknown;
    try {
      detail = JSON.parse(rawText);
    } catch {
      detail = rawText;
    }
    throw new GenerateError(res.status, detail, rawText);
  }
  return res.json() as Promise<RunStatusResponse>;
}

export async function generateItemsStream({
  body,
  threadId,
  onProgress,
}: GenerateItemsStreamParams): Promise<FinalOutput> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (threadId) {
    headers["X-Thread-ID"] = threadId;
  }

  const res = await fetch(GENERATE_ITEMS_STREAM_URL, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const rawText = await res.text();
    let detail: unknown;
    try {
      const errBody = JSON.parse(rawText) as { detail?: unknown };
      detail = errBody.detail;
    } catch {
      detail = undefined;
    }
    throw new GenerateError(res.status, detail, rawText);
  }

  // Read SSE stream
  const reader = res.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  if (!reader) {
    throw new GenerateError(500, "No response body", "");
  }

  let finalOutput: FinalOutput | null = null;
  let errorMessage: string | null = null;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6); // Remove "data: " prefix
          try {
            const event: ProgressEvent = JSON.parse(data);
            
            if (onProgress) {
              onProgress(event);
            }

            if (event.type === "complete" && event.data) {
              finalOutput = event.data as FinalOutput;
            } else if (event.type === "error") {
              errorMessage = event.message || "Unknown error";
            }
          } catch (e) {
            console.error("Failed to parse SSE event:", e, data);
          }
        }
      }
    }
  } catch (e) {
    throw e;
  } finally {
    reader.releaseLock();
  }

  if (errorMessage) {
    throw new GenerateError(500, errorMessage, errorMessage);
  }

  if (!finalOutput) {
    throw new GenerateError(500, "No final output received", "");
  }

  return finalOutput;
}

/**
 * Map form values to API UserRequest (exclude empty optionals).
 */
export function formToRequest(values: {
  construct_name: string;
  construct_definition: string;
  target_population: string;
  response_scale: string;
  item_count: number;
  constraints: string[];
  cultural_group?: string;
  construct_exclusions?: string;
  native_construct?: string;
  example_item?: string;
  approved_domains: string[];
  human_feedback?: string;
  previous_items?: string[];
  model_provider?: "claude" | "openai";
  use_chatgpt_critics?: boolean;
}): UserRequest {
  const req: UserRequest = {
    construct_name: values.construct_name,
    construct_definition: values.construct_definition,
    target_population: values.target_population,
    response_scale: values.response_scale,
    item_count: values.item_count,
    constraints: values.constraints.length ? values.constraints : undefined,
    approved_domains: values.approved_domains.length ? values.approved_domains : undefined,
    previous_items: values.previous_items?.length ? values.previous_items : undefined,
    model_provider: values.model_provider || "claude",
    use_chatgpt_critics: values.use_chatgpt_critics || false,
  };
  if (values.cultural_group?.trim()) req.cultural_group = values.cultural_group.trim();
  if (values.construct_exclusions?.trim()) req.construct_exclusions = values.construct_exclusions.trim();
  if (values.native_construct?.trim()) req.native_construct = values.native_construct.trim();
  if (values.example_item?.trim()) req.example_item = values.example_item.trim();
  if (values.human_feedback?.trim()) req.human_feedback = values.human_feedback.trim();
  return req;
}
