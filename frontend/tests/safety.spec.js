import { test, expect } from '@playwright/test';

const baseURL = 'http://127.0.0.1:8765';
const headers = { Origin: baseURL };

async function login(page, path, email, password) {
  await page.goto(path);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Sign out', exact: true })).toBeVisible();
}

test('Block closes chat for both Members and the Admin can resolve a post-Block Report', async ({ page, browser }) => {
  const partner = await browser.newPage({ baseURL });
  const admin = await browser.newPage({ baseURL });
  let release, started;
  const held = new Promise(resolve => { release = resolve; });
  const sending = new Promise(resolve => { started = resolve; });
  await page.route('**/api/conversations/safety-conversation/messages', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    started();
    await held;
    await route.fulfill({ status: 409, json: { reason: 'conversation_closed' } });
  });
  try {
    await login(page, '/?conversation=safety-conversation', 'safety-a@example.invalid', 'Fictional chat password');
    await login(partner, '/?conversation=safety-conversation', 'safety-b@example.invalid', 'Fictional chat password');
    const chat = page.getByRole('region', { name: 'Conversation', exact: true });
    const other = partner.getByRole('region', { name: 'Conversation', exact: true });
    const block = chat.getByRole('button', { name: 'Block Conversation', exact: true });
    await block.click({ timeout: 3500 });
    await chat.getByRole('button', { name: 'Cancel Block', exact: true }).click();
    await expect(chat.getByRole('button', { name: 'Send Message' })).toBeVisible();
    await chat.getByLabel('Message', { exact: true }).fill('An in-flight fictional Message.');
    await chat.getByRole('button', { name: 'Send Message' }).click();
    await sending;
    await expect(block).toBeEnabled({ timeout: 2500 });
    await block.click();
    await chat.getByRole('button', { name: 'Confirm Block' }).click();
    release();
    await expect(chat.getByText('This Conversation is closed.', { exact: true })).toBeVisible();
    await expect(chat.getByRole('log')).toHaveCount(0);
    await other.getByRole('button', { name: 'Refresh Reveal' }).click();
    await expect(other.getByText('This Conversation is closed.', { exact: true })).toBeVisible();
    await expect(other.getByRole('button', { name: 'Send Message' })).toHaveCount(0);
    const receipt = await partner.request.post('/api/conversations/safety-conversation/reports', { headers, data: { reason: 'identity_pressure' } });
    expect(receipt.status()).toBe(201);
    await login(admin, '/', 'browser.admin@example.invalid', 'Fictional admin password');
    const reports = admin.getByRole('region', { name: 'Reports', exact: true });
    const entry = reports.getByRole('listitem').filter({ hasText: 'Identity pressure' });
    await expect(entry).toBeVisible();
    await expect(entry.getByText('Report ' + (await receipt.json()).report_id, { exact: true })).toBeVisible();
    await expect(entry).not.toContainText(/safety-[ab]@|FictionalHarbor|FictionalDune|2000-01-01/);
    await entry.getByRole('button', { name: 'Reject', exact: true }).click();
    await expect(reports.getByText('No Reports awaiting review.')).toBeVisible();
    await expect(other.getByText('This Conversation is closed.', { exact: true })).toBeVisible();
  } finally { release(); await partner.close(); await admin.close(); }
});

test('a late Block-session error does not sign out the next Member', async ({ page }) => {
  let release, intercepted;
  const held = new Promise(resolve => { release = resolve; });
  const started = new Promise(resolve => { intercepted = resolve; });
  await page.addInitScript(() => {
    const fetch = window.fetch.bind(window);
    window.fetch = async (path, options) => {
      if (path !== '/api/conversations/browser-conversation/block') return fetch(path, options);
      const response = await fetch(path, { ...options, signal: undefined });
      setTimeout(() => { document.body.dataset.oldBlockStatus = String(response.status); }, 0);
      return response;
    };
  });
  await page.route('**/api/conversations/browser-conversation/block', async route => {
    intercepted();
    await held;
    await route.fulfill({ status: 401, json: { reason: 'invalid_credentials' } });
  });
  try {
    await login(page, '/?conversation=browser-conversation', 'browser-a@example.invalid', 'Fictional chat password');
    const chat = page.getByRole('region', { name: 'Conversation', exact: true });
    await chat.getByRole('button', { name: 'Block Conversation' }).click();
    await chat.getByRole('button', { name: 'Confirm Block' }).click();
    await started;
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByLabel('Email', { exact: true }).fill('browser-b@example.invalid');
    await page.getByLabel('Password', { exact: true }).fill('Fictional chat password');
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    await expect(chat.getByRole('button', { name: 'Send Message' })).toBeVisible();
    release();
    await expect(page.locator('body')).toHaveAttribute('data-old-block-status', '401');
    await expect(chat.getByRole('button', { name: 'Send Message' })).toBeVisible();
    await expect(page.getByText('Your session has expired. Please sign in again.')).toHaveCount(0);
  } finally { release(); }
});
