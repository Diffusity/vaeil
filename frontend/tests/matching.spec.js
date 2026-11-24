import { test, expect } from '@playwright/test';

async function login(page, name, password) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).fill(name + '@example.invalid');
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Sign out', exact: true })).toBeVisible();
}

test('Admin proposes one Match, and only mutual acceptance opens a Conversation', async ({ page, browser }) => {
  const left = await browser.newPage({ baseURL: 'http://127.0.0.1:8765' });
  const right = await browser.newPage({ baseURL: 'http://127.0.0.1:8765' });
  try {
    await login(page, 'browser.admin', 'Fictional admin password');
    await page.getByRole('button', { name: 'Propose Matches', exact: true }).click({ timeout: 3500 });
    await expect(page.getByText('1 Match proposed.', { exact: true })).toBeVisible();
    await login(left, 'matching-a', 'Fictional chat password');
    await login(right, 'matching-b', 'Fictional chat password');
    const leftMatches = left.getByRole('region', { name: 'Matches', exact: true });
    const rightMatches = right.getByRole('region', { name: 'Matches', exact: true });
    await expect(leftMatches.getByText('Watchtower', { exact: true })).toBeVisible();
    await expect(leftMatches.getByText('<b>Quiet afternoons.</b>', { exact: true })).toBeVisible();
    await expect(leftMatches.locator('b')).toHaveCount(0);
    await expect(leftMatches).not.toContainText(/FictionalOrchard|matching-b@example\.invalid|2000-01-01/);
    await leftMatches.getByRole('button', { name: 'Accept Match' }).click();
    await expect(leftMatches.getByText('Waiting for the other Member.')).toBeVisible();
    await expect(leftMatches.getByRole('link', { name: 'Open Conversation' })).toHaveCount(0);
    await rightMatches.getByRole('button', { name: 'Accept Match' }).click();
    const rightLink = rightMatches.getByRole('link', { name: 'Open Conversation' });
    await expect(rightLink).toBeVisible();
    await leftMatches.getByRole('button', { name: 'Refresh Matches' }).click();
    const leftLink = leftMatches.getByRole('link', { name: 'Open Conversation' });
    await expect(leftLink).toHaveAttribute('href', await rightLink.getAttribute('href'));
    await leftLink.click();
    await expect(left.getByRole('region', { name: 'Conversation', exact: true })).toBeVisible();
  } finally { await left.close(); await right.close(); }
});

test('a delayed Matches session error cannot sign out a newer Member', async ({ page }) => {
  await page.addInitScript(() => {
    const original = window.fetch.bind(window);
    let first = true;
    window.fetch = async (path, options) => {
      if (path !== '/api/me/matches' || !first) return original(path, options);
      first = false;
      const response = await original(path, { ...options, signal: undefined });
      setTimeout(() => { document.body.dataset.oldMatchResponse = String(response.status); }, 0);
      return response;
    };
  });
  let release;
  const hold = new Promise(resolve => { release = resolve; });
  let intercept;
  const started = new Promise(resolve => { intercept = resolve; });
  let first = true;
  await page.route('**/api/me/matches', async route => {
    if (!first) return route.continue();
    first = false;
    intercept();
    await hold;
    await route.fulfill({ status: 401, json: { reason: 'invalid_credentials' } });
  });
  const signInOnCurrentPage = async name => {
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByLabel('Email', { exact: true }).fill(name + '@example.invalid');
    await page.getByLabel('Password', { exact: true }).fill('Fictional chat password');
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Sign out', exact: true })).toBeVisible();
  };
  try {
    await page.goto('/');
    await signInOnCurrentPage('browser-a');
    await started;
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await signInOnCurrentPage('browser-b');
    release();
    await expect(page.locator('body')).toHaveAttribute('data-old-match-response', '401');
    await expect(page.getByRole('region', { name: 'Matches', exact: true })).toBeVisible();
    await expect(page.getByText('Your session has expired. Please sign in again.')).toHaveCount(0);
  } finally { release(); }
});
