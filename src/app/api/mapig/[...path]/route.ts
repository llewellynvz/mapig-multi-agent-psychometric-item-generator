/**
 * Opt-in server-side proxy to the MAPIG FastAPI backend.
 *
 * Enabled from the browser side with NEXT_PUBLIC_API_PROXY=1 (see src/lib/api.ts).
 * The proxy injects the server-only MAPIG_API_KEY as X-API-Key so the key is never
 * shipped to the browser. Only /v1/* and /healthz are forwarded (not an open proxy).
 */

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

type RouteContext = { params: Promise<{ path?: string[] }> };

// Request headers forwarded to the backend (everything else is dropped, including
// any client-supplied X-API-Key).
const FORWARDED_REQUEST_HEADERS = ["content-type", "accept", "x-thread-id"];

// Response headers passed back to the browser.
const FORWARDED_RESPONSE_HEADERS = ["content-type", "cache-control", "retry-after", "x-thread-id"];

function backendBaseUrl(): string {
  const configured = process.env.MAPIG_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL;
  if (configured) return configured.replace(/\/+$/, "");
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return "http://localhost:8000";
}

function isAllowedPath(segments: string[]): boolean {
  if (segments.length === 0) return false;
  if (segments.some((s) => s === "" || s === "." || s === "..")) return false;
  if (segments.length === 1 && segments[0] === "healthz") return true;
  return segments[0] === "v1" && segments.length > 1;
}

function jsonError(status: number, detail: string): Response {
  return Response.json({ detail }, { status, headers: { "Cache-Control": "no-store" } });
}

async function proxy(request: Request, context: RouteContext): Promise<Response> {
  const { path = [] } = await context.params;
  if (!isAllowedPath(path)) {
    return jsonError(404, "Not found");
  }

  // Re-encode each (already decoded) segment so an encoded "/" cannot escape the allowlist.
  const upstreamPath = path.map(encodeURIComponent).join("/");
  const { search } = new URL(request.url);
  const upstreamUrl = `${backendBaseUrl()}/${upstreamPath}${search}`;

  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const apiKey = process.env.MAPIG_API_KEY;
  if (apiKey) headers.set("X-API-Key", apiKey);

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body: request.method === "GET" ? undefined : await request.arrayBuffer(),
      cache: "no-store",
      // Client disconnect aborts the upstream request (stops a long SSE run).
      signal: request.signal,
    });
  } catch (err) {
    if (request.signal.aborted) {
      return new Response(null, { status: 499 });
    }
    console.error("[mapig-proxy] upstream fetch failed:", err);
    return jsonError(502, "Backend unreachable");
  }

  const responseHeaders = new Headers();
  for (const name of FORWARDED_RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }

  const contentType = upstream.headers.get("content-type") ?? "";
  if (contentType.startsWith("text/event-stream")) {
    // Stream SSE through unbuffered.
    responseHeaders.set("Content-Type", "text/event-stream");
    responseHeaders.set("Cache-Control", "no-cache, no-transform");
    responseHeaders.set("X-Accel-Buffering", "no");
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

export function GET(request: Request, context: RouteContext): Promise<Response> {
  return proxy(request, context);
}

export function POST(request: Request, context: RouteContext): Promise<Response> {
  return proxy(request, context);
}
