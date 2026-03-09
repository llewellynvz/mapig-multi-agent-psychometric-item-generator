"use client";

import { useEffect } from "react";

// #region agent log
const INGEST_URL = "http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b";

export function DebugLogger() {
  useEffect(() => {
    fetch("/api/debug-ping").catch(() => {});
    fetch(INGEST_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        location: "frontend/DebugLogger.tsx",
        message: "client_loaded",
        data: { href: typeof window !== "undefined" ? window.location.href : "" },
        timestamp: Date.now(),
        hypothesisId: "H1_H4",
      }),
    }).catch(() => {});
  }, []);
  return null;
}
// #endregion
