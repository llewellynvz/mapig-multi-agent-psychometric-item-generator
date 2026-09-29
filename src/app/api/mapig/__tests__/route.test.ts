import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { GET, POST } from '../[...path]/route';

const fetchMock = vi.fn();

function ctx(path: string[]) {
  return { params: Promise.resolve({ path }) };
}

function lastUpstreamCall(): { url: string; init: RequestInit; headers: Headers } {
  const [url, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
  return { url, init, headers: new Headers(init.headers) };
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
  vi.stubEnv('MAPIG_BACKEND_URL', 'http://backend.test/');
  vi.stubEnv('MAPIG_API_KEY', 'secret-key');
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe('/api/mapig proxy route', () => {
  it('injects X-API-Key and forwards path, query, thread id and body', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 201,
        headers: { 'content-type': 'application/json' },
      })
    );

    const req = new Request('http://app.test/api/mapig/v1/generate-items?debug=1', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-thread-id': 'thread-123',
        'x-api-key': 'client-supplied',
        cookie: 'session=abc',
      },
      body: JSON.stringify({ construct_name: 'Grit' }),
    });
    const res = await POST(req, ctx(['v1', 'generate-items']));

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const { url, init, headers } = lastUpstreamCall();
    expect(url).toBe('http://backend.test/v1/generate-items?debug=1');
    expect(init.method).toBe('POST');
    expect(headers.get('x-api-key')).toBe('secret-key');
    expect(headers.get('x-thread-id')).toBe('thread-123');
    expect(headers.get('content-type')).toBe('application/json');
    expect(headers.get('cookie')).toBeNull();
    expect(new TextDecoder().decode(init.body as ArrayBuffer)).toBe('{"construct_name":"Grit"}');
    expect(init.signal).toBe(req.signal);

    expect(res.status).toBe(201);
    expect(await res.json()).toEqual({ ok: true });
  });

  it('omits X-API-Key when MAPIG_API_KEY is unset', async () => {
    vi.stubEnv('MAPIG_API_KEY', '');
    fetchMock.mockResolvedValue(new Response('{"status":"ok"}', { status: 200 }));

    await GET(new Request('http://app.test/api/mapig/healthz'), ctx(['healthz']));

    const { url, headers } = lastUpstreamCall();
    expect(url).toBe('http://backend.test/healthz');
    expect(headers.has('x-api-key')).toBe(false);
  });

  it('passes upstream error status and body through', async () => {
    fetchMock.mockResolvedValue(
      new Response('{"detail":"busy"}', {
        status: 429,
        headers: { 'content-type': 'application/json', 'retry-after': '5' },
      })
    );

    const res = await GET(
      new Request('http://app.test/api/mapig/v1/runs/abc/status'),
      ctx(['v1', 'runs', 'abc', 'status'])
    );

    expect(res.status).toBe(429);
    expect(res.headers.get('retry-after')).toBe('5');
    expect(await res.json()).toEqual({ detail: 'busy' });
  });

  it.each([
    [['admin']],
    [['v1']],
    [['docs']],
    [['openapi.json']],
    [['healthz', 'extra']],
    [['v1', '..', 'admin']],
  ])('rejects non-allowlisted path %j with 404', async (path) => {
    const res = await GET(new Request(`http://app.test/api/mapig/${path.join('/')}`), ctx(path));
    expect(res.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('re-encodes path segments so an encoded slash cannot escape v1/', async () => {
    fetchMock.mockResolvedValue(new Response('{}', { status: 200 }));

    await GET(new Request('http://app.test/api/mapig/v1/runs/x'), ctx(['v1', 'runs', 'a/../../admin', 'status']));

    expect(lastUpstreamCall().url).toBe('http://backend.test/v1/runs/a%2F..%2F..%2Fadmin/status');
  });

  it('streams SSE through unbuffered with no-cache headers', async () => {
    const encoder = new TextEncoder();
    const upstreamBody = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode('data: {"type":"start"}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"complete"}\n\n'));
        controller.close();
      },
    });
    fetchMock.mockResolvedValue(
      new Response(upstreamBody, {
        status: 200,
        headers: { 'content-type': 'text/event-stream; charset=utf-8' },
      })
    );

    const res = await POST(
      new Request('http://app.test/api/mapig/v1/generate-items-stream', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: '{}',
      }),
      ctx(['v1', 'generate-items-stream'])
    );

    expect(res.status).toBe(200);
    expect(res.headers.get('content-type')).toBe('text/event-stream');
    expect(res.headers.get('cache-control')).toBe('no-cache, no-transform');
    expect(res.headers.get('x-accel-buffering')).toBe('no');
    // The upstream stream object is handed through as-is (no buffering).
    expect(res.body).toBe(upstreamBody);
    expect(await res.text()).toBe('data: {"type":"start"}\n\ndata: {"type":"complete"}\n\n');
  });

  it('returns 502 when the backend is unreachable', async () => {
    fetchMock.mockRejectedValue(new TypeError('fetch failed'));
    const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const res = await GET(new Request('http://app.test/api/mapig/healthz'), ctx(['healthz']));

    expect(res.status).toBe(502);
    errSpy.mockRestore();
  });
});
