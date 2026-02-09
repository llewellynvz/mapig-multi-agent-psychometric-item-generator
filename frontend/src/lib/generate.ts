"use client";

import { GENERATE_ITEMS_URL, GENERATE_ITEMS_STREAM_URL, type ProgressEvent } from "@/lib/api";
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

  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'generate.ts:72',message:'Starting fetch to stream endpoint',data:{url:GENERATE_ITEMS_STREAM_URL,hasThreadId:!!threadId},timestamp:Date.now(),hypothesisId:'H1_H2_H3_H4_H5'})}).catch(()=>{});
  // #endregion
  const res = await fetch(GENERATE_ITEMS_STREAM_URL, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'generate.ts:78',message:'Fetch response received',data:{ok:res.ok,status:res.status,statusText:res.statusText,hasBody:!!res.body},timestamp:Date.now(),hypothesisId:'H1_H2_H3_H4_H5'})}).catch(()=>{});
  // #endregion

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
  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'generate.ts:91',message:'Checking reader availability',data:{hasReader:!!reader},timestamp:Date.now(),hypothesisId:'H1_H2_H3'})}).catch(()=>{});
  // #endregion
  const decoder = new TextDecoder();
  let buffer = "";

  if (!reader) {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'generate.ts:96',message:'No reader available - throwing error',data:{},timestamp:Date.now(),hypothesisId:'H3'})}).catch(()=>{});
    // #endregion
    throw new GenerateError(500, "No response body", "");
  }

  let finalOutput: FinalOutput | null = null;
  let errorMessage: string | null = null;

  try {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'generate.ts:103',message:'Starting SSE read loop',data:{},timestamp:Date.now(),hypothesisId:'H1_H2_H3_H4'})}).catch(()=>{});
    // #endregion
    while (true) {
      const { done, value } = await reader.read();
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'generate.ts:105',message:'Read chunk from stream',data:{done:done,hasValue:!!value,valueLength:value?.length},timestamp:Date.now(),hypothesisId:'H1_H2_H3_H4'})}).catch(()=>{});
      // #endregion
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6); // Remove "data: " prefix
          try {
            const event: ProgressEvent = JSON.parse(data);
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'generate.ts:115',message:'Parsed SSE event',data:{eventType:event.type},timestamp:Date.now(),hypothesisId:'H1_H2'})}).catch(()=>{});
            // #endregion
            
            if (onProgress) {
              onProgress(event);
            }

            if (event.type === "complete" && event.data) {
              finalOutput = event.data as FinalOutput;
            } else if (event.type === "error") {
              errorMessage = event.message || "Unknown error";
            }
          } catch (e) {
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'generate.ts:127',message:'Failed to parse SSE event',data:{error:String(e),data:data},timestamp:Date.now(),hypothesisId:'H2'})}).catch(()=>{});
            // #endregion
            console.error("Failed to parse SSE event:", e, data);
          }
        }
      }
    }
  } catch (e) {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'generate.ts:132',message:'Exception in SSE read loop',data:{error:String(e),errorType:typeof e},timestamp:Date.now(),hypothesisId:'H1_H2_H3_H4_H5'})}).catch(()=>{});
    // #endregion
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
  native_construct?: string;
  example_item?: string;
  approved_domains: string[];
}): UserRequest {
  const req: UserRequest = {
    construct_name: values.construct_name,
    construct_definition: values.construct_definition,
    target_population: values.target_population,
    response_scale: values.response_scale,
    item_count: values.item_count,
    constraints: values.constraints.length ? values.constraints : undefined,
    approved_domains: values.approved_domains.length ? values.approved_domains : undefined,
  };
  if (values.native_construct?.trim()) req.native_construct = values.native_construct.trim();
  if (values.example_item?.trim()) req.example_item = values.example_item.trim();
  return req;
}
