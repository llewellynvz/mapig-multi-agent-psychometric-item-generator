"use client";

import { useQuery } from "@tanstack/react-query";
import { HEALTH_URL } from "@/lib/api";

export type HealthStatus = "ok" | "error" | "pending";

export interface HealthResponse {
  status: string;
  mode?: string;
}

export function useHealth() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: async (): Promise<HealthResponse> => {
      const res = await fetch(HEALTH_URL);
      if (!res.ok) throw new Error("Health check failed");
      return res.json();
    },
    refetchInterval: 30000,
    retry: 1,
    staleTime: 10000,
  });

  const status: HealthStatus = isLoading
    ? "pending"
    : isError
      ? "error"
      : data?.status === "ok"
        ? "ok"
        : "error";

  return { data, isLoading, isError, status };
}
