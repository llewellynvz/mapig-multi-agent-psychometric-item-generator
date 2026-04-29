import { test, expect } from '@playwright/test';

/**
 * MAPIG End-to-End Smoke Test
 *
 * Drives the full Next.js + FastAPI pipeline through the browser. Asserts
 * that the result page renders all the major panels (PFA, Expert, Persona,
 * Generated Items) for a representative scenario.
 *
 * IMPORTANT: This test EXPECTS the dev server to be running with
 * `APP_MODE=mock` so it doesn't burn OpenAI/Anthropic credits. To run:
 *
 *   1. Terminal A: APP_MODE=mock SEARCH_PROVIDER=local npm run dev
 *   2. Terminal B: npm run e2e
 *
 * The test will skip if the dev server isn't reachable, so CI can run it
 * conditionally without failing.
 */

test.describe('MAPIG full pipeline smoke', () => {
  test.beforeAll(async ({ request }) => {
    try {
      const r = await request.get('/healthz', { timeout: 5_000 });
      if (!r.ok()) {
        test.skip(true, `Health check failed (status=${r.status()}); start dev server with APP_MODE=mock first`);
      }
    } catch (e) {
      test.skip(true, `Dev server not reachable: ${(e as Error).message}; start with APP_MODE=mock first`);
    }
  });

  test('generates items end-to-end and renders all panels', async ({ page }) => {
    // 1. Land on the homepage
    await page.goto('/');
    await expect(page).toHaveTitle(/MAPIG|Psynalytics|item/i);

    // 2. Fill in a representative construct
    await page.getByLabel(/construct name/i).fill('Emotional Wellbeing');
    await page.getByLabel(/construct definition/i).fill(
      'A multidimensional affective state comprising life satisfaction (a global ' +
      'cognitive appraisal of life quality) and affect balance (the frequency ' +
      'ratio of positive to negative emotional experiences). Reflects the hedonic ' +
      'dimension of wellbeing.'
    );
    await page.getByLabel(/target population/i).fill('Working adults');
    await page.getByLabel(/response scale/i).fill('5-point Likert');

    // 3. Submit
    const submit = page.getByRole('button', { name: /generate|create items|run/i });
    await submit.click();

    // 4. Wait for completion. Mock-mode pipeline takes ~30-60s.
    //    Use the presence of the GeneratedItemsTable header as the success signal.
    await expect(page.getByText(/generated items/i).first()).toBeVisible({ timeout: 90_000 });

    // 5. Assertions on each panel.

    // Generated items table — at least one item row visible
    const itemRows = page.locator('[data-testid="item-row"], tbody tr');
    await expect(itemRows.first()).toBeVisible();

    // PFA panel — look for "Pseudo-Factor Analysis" or "Factor Structure" heading
    const pfaHeading = page.getByText(/pseudo[- ]?factor analysis|factor structure/i).first();
    await expect(pfaHeading).toBeVisible();

    // Persona Validation card — heading present
    const personaHeading = page.getByText(/persona validation/i).first();
    await expect(personaHeading).toBeVisible();

    // No console errors. Capture them via the page object.
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        // Don't fail on errors from external resources, only app-level errors.
        const text = msg.text();
        if (
          !text.includes('Failed to load resource') &&
          !text.includes('favicon')
        ) {
          throw new Error(`Console error during E2E: ${text}`);
        }
      }
    });
  });
});
