import { test, expect } from '@playwright/test';

test('renders the real anonymous endpoint without private canaries', async ({ page }) => {
  const response = page.waitForResponse('**/api/demo/member');
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Comet' })).toBeVisible();
  const payload = await (await response).text();
  await expect(page.getByText('Honesty', { exact: true })).toBeVisible();
  await expect(page.getByText(/demo only.*don.t enter real personal details/i)).toBeVisible();
  const visible = await page.locator('body').innerText();
  for (const canary of ['DemoPrivateNameZXQ', 'demo-private-zxq@example.invalid', '+919876543210', '1987-03-14']) {
    expect(payload + visible).not.toContain(canary);
  }
});

test('shows loading, then the actual endpoint result', async ({ page }) => {
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  await page.route('**/api/demo/member', async route => { await gate; await route.continue(); });
  await page.goto('/');
  try {
    await expect(page.getByRole('status')).toHaveText('Loading the fictional Values Profile…');
  } finally { release(); }
  await expect(page.getByRole('heading', { name: 'Comet' })).toBeVisible();
});

test('shows a retry-friendly HTTP failure and recovers', async ({ page }) => {
  await page.route('**/api/demo/member', route => route.fulfill({ status: 503, body: 'unavailable' }));
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('Could not load the demo');
  await page.unroute('**/api/demo/member');
  await page.getByRole('button', { name: 'Try again' }).click();
  await expect(page.getByRole('heading', { name: 'Comet' })).toBeVisible();
});
