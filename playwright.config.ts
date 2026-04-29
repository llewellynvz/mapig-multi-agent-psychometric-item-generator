import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for MAPIG end-to-end smoke tests.
 *
 * Test files live in `tests-e2e/`. Each test starts the local Next.js dev
 * server (on :3000) which proxies the FastAPI backend on :8000. Use APP_MODE=mock
 * environment to avoid burning OpenAI/Anthropic credits during E2E.
 *
 * Run locally:
 *   npm run e2e:install   # one-time: download Chromium binary
 *   APP_MODE=mock SEARCH_PROVIDER=local npm run dev   # in one terminal
 *   npm run e2e                                       # in another terminal
 */
export default defineConfig({
  testDir: './tests-e2e',
  timeout: 120_000, // generous: full pipeline can take ~60s in mock mode
  expect: { timeout: 10_000 },
  fullyParallel: false, // single test, sequential is fine
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
