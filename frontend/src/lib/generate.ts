"use client";

import { GENERATE_ITEMS_URL } from "@/lib/api";
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
