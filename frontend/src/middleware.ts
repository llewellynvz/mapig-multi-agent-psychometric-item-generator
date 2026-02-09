import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// #region agent log
const INGEST_URL = "http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b";

function logRequest(req: NextRequest) {
  fetch(INGEST_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: `log_${Date.now()}`,
      location: "frontend/middleware.ts",
      message: "next_request",
      data: { path: req.nextUrl.pathname, method: req.method },
      timestamp: Date.now(),
      hypothesisId: "H1_H4",
    }),
  }).catch(() => {});
}
// #endregion

export function middleware(request: NextRequest) {
  // #region agent log
  logRequest(request);
  // #endregion
  return NextResponse.next();
}
