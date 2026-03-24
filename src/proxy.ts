import { NextResponse } from "next/server";
import type { NextFetchEvent, NextRequest } from "next/server";

// #region agent log
const INGEST_URL = "http://127.0.0.1:7242/ingest/880aa556-4a60-4d2b-b968-9cf36e6efa6b";

function logRequest(req: NextRequest) {
  return fetch(INGEST_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: `log_${Date.now()}`,
      location: "frontend/proxy.ts",
      message: "next_request",
      data: { path: req.nextUrl.pathname, method: req.method },
      timestamp: Date.now(),
      hypothesisId: "H1_H4",
    }),
  }).catch(() => {});
}
// #endregion

export function proxy(request: NextRequest, event: NextFetchEvent) {
  // #region agent log
  event.waitUntil(logRequest(request));
  // #endregion
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Exclude Next.js internals and static assets from proxy so chunk/js/css
     * requests are served directly and cannot be delayed by logging.
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)",
  ],
};
