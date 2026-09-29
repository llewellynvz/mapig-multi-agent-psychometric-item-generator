import { describe, it, expect, vi, afterEach } from 'vitest';
import { resolveApiBaseUrl } from '../api';

afterEach(() => {
  vi.unstubAllEnvs();
});

function stubEnv(env: Record<string, string | undefined>) {
  for (const [key, value] of Object.entries(env)) {
    vi.stubEnv(key, value);
  }
}

describe('resolveApiBaseUrl', () => {
  it('uses the same-origin proxy when NEXT_PUBLIC_API_PROXY=1', () => {
    stubEnv({ NEXT_PUBLIC_API_PROXY: '1', NEXT_PUBLIC_API_URL: 'https://api.example.com' });
    expect(resolveApiBaseUrl()).toBe('/api/mapig');
  });

  it('uses NEXT_PUBLIC_API_URL when set, including empty (same-origin)', () => {
    stubEnv({ NEXT_PUBLIC_API_PROXY: undefined, NEXT_PUBLIC_API_URL: 'https://api.example.com' });
    expect(resolveApiBaseUrl()).toBe('https://api.example.com');
    stubEnv({ NEXT_PUBLIC_API_URL: '' });
    expect(resolveApiBaseUrl()).toBe('');
  });

  it('defaults to same-origin on a Vercel build', () => {
    stubEnv({ NEXT_PUBLIC_API_PROXY: undefined, NEXT_PUBLIC_API_URL: undefined, MAPIG_ON_VERCEL: '1' });
    expect(resolveApiBaseUrl()).toBe('');
  });

  it('defaults to localhost:8000 for local dev', () => {
    stubEnv({ NEXT_PUBLIC_API_PROXY: undefined, NEXT_PUBLIC_API_URL: undefined, MAPIG_ON_VERCEL: '' });
    expect(resolveApiBaseUrl()).toBe('http://localhost:8000');
  });
});
