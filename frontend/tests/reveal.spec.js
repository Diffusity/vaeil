import { test, expect } from '@playwright/test';

async function signIn(page, who, pair = 'reveal-conversation') {
  await page.goto('/?conversation=' + pair);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).fill(who + '@example.invalid');
  await page.getByLabel('Password', { exact: true }).fill('Fictional chat password');
  const signedIn = page.waitForResponse(response => response.url().endsWith('/api/sessions') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  const response = await signedIn;
  expect(response.status()).toBe(200);
  await expect(page.getByRole('button', { name: 'Sign out', exact: true })).toBeVisible();
  return page.getByRole('region', { name: 'Reveal', exact: true });
}

test('real bilateral ceremony, withdrawal, failure refusal and refresh preserve pair-scoped disclosure', async ({ page, browser }) => {
  const context = await browser.newContext({ baseURL: 'http://127.0.0.1:8765' });
  const partner = await context.newPage();
  try {
    const a = await signIn(page, 'reveal-a');
    const b = await signIn(partner, 'reveal-b');
    await expect(a.getByText('Pseudonym: Meadow', { exact: true })).toBeVisible();
    await expect(partner.getByRole('button', { name: 'Sign out', exact: true })).toBeVisible();
    await expect(b.getByText('Pseudonym: River', { exact: true })).toBeVisible();
    await expect(a).not.toContainText('reveal-b@example.invalid');
    await a.getByRole('button', { name: 'Consent to Reveal', exact: true }).click();
    await expect(a.getByRole('button', { name: 'Withdraw consent', exact: true })).toBeVisible();
    await expect(a).not.toContainText('reveal-b@example.invalid');
    await a.getByRole('button', { name: 'Withdraw consent', exact: true }).click();
    await expect(a.getByRole('button', { name: 'Consent to Reveal', exact: true })).toBeVisible();
    await page.route('**/reveal/consent', route => route.fulfill({ status: 503, contentType: 'application/json', body: '{"reason":"unavailable"}' }), { times: 1 });
    await a.getByRole('button', { name: 'Consent to Reveal', exact: true }).click();
    await expect(a.getByRole('alert')).toBeVisible();
    await expect(a).not.toContainText('reveal-b@example.invalid');
    await a.getByRole('button', { name: 'Consent to Reveal', exact: true }).click();
    await expect(a.getByRole('button', { name: 'Withdraw consent', exact: true })).toBeVisible();
    await b.getByRole('button', { name: 'Consent to Reveal', exact: true }).click();
    await expect(b.getByText('Reveal complete.', { exact: true })).toBeVisible();
    await a.getByRole('button', { name: 'Refresh Reveal', exact: true }).click();
    await expect(a.getByText('reveal-b@example.invalid', { exact: true })).toBeVisible();
    await expect(a.getByText('FictionalMeadow', { exact: true })).toBeVisible();
    await expect(a.getByRole('button', { name: 'Withdraw consent', exact: true })).toHaveCount(0);
    await expect(a).not.toContainText('2000-01-01');
    await page.reload();
    await expect(page.getByRole('region', { name: 'Reveal', exact: true }).getByText('Reveal complete.', { exact: true })).toBeVisible();
  } finally { await context.close(); }
});

test('ineligible Conversation has no consent action', async ({ page }) => {
  const reveal = await signIn(page, 'browser-a', 'browser-conversation');
  await expect(reveal.getByText('Reveal is not yet available.', { exact: true })).toBeVisible();
  await expect(reveal.getByRole('button', { name: 'Consent to Reveal', exact: true })).toHaveCount(0);
});
