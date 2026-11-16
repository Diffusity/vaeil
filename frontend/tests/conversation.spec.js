import { test, expect } from '@playwright/test';

async function signIn(page, identifier) {
  await page.goto('/?conversation=browser-conversation');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).fill(identifier + '@example.invalid');
  await page.getByLabel('Password', { exact: true }).fill('Fictional chat password');
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Sign out', exact: true })).toBeVisible();
}

test('no recipient delivery before explicit human review; release delivers exactly once through real APIs', async ({ page, browser, request }) => {
  const context = await browser.newContext({ baseURL: 'http://127.0.0.1:8765' });
  const recipient = await context.newPage();
  try {
    await signIn(page, 'browser-a');
    await signIn(recipient, 'browser-b');
    const chat = page.getByRole('region', { name: 'Conversation', exact: true });
    await chat.getByLabel('Message', { exact: true }).fill('BrowserMessageCanaryZXQ hello.');
    await chat.getByRole('button', { name: 'Send Message', exact: true }).click();
    await expect(chat.getByText('Withheld — technical failure. Retry or submit for review.', { exact: true })).toBeVisible();
    await recipient.getByRole('button', { name: 'Refresh Conversation', exact: true }).click();
    await expect(recipient.locator('body')).not.toContainText('BrowserMessageCanaryZXQ');
    await chat.getByRole('button', { name: 'Submit for review', exact: true }).click();
    await expect(chat.getByText('Under review. Not delivered.', { exact: true })).toBeVisible();
    await expect(chat.getByRole('button', { name: 'Retry Message', exact: true })).toHaveCount(0);
    const headers = { Origin: 'http://127.0.0.1:8765' };
    expect((await request.post('/api/sessions', { headers, data: {
      email: 'browser.admin@example.invalid', password: 'Fictional admin password',
    } })).status()).toBe(200);
    const queue = (await (await request.get('/api/admin/messages')).json()).messages;
    const message = queue.find(item => item.text === 'BrowserMessageCanaryZXQ hello.');
    expect(message).toBeTruthy();
    expect((await request.post(`/api/admin/messages/${message.message_id}/decision`, { headers, data: { decision: 'release' } })).status()).toBe(204);
    await recipient.getByRole('button', { name: 'Refresh Conversation', exact: true }).click();
    const history = recipient.getByRole('log', { name: 'Delivered Messages', exact: true });
    await expect(history.getByText('BrowserMessageCanaryZXQ hello.', { exact: true })).toHaveCount(1);
    await recipient.getByRole('button', { name: 'Refresh Conversation', exact: true }).click();
    await expect(history.getByText('BrowserMessageCanaryZXQ hello.', { exact: true })).toHaveCount(1);
  } finally { await context.close(); }
});

test('checking disables duplicate sends; a technical retry uses a fresh request key', async ({ page }) => {
  await signIn(page, 'browser-a');
  const chat = page.getByRole('region', { name: 'Conversation', exact: true });
  await chat.getByLabel('Message', { exact: true }).fill('RetryMessageCanaryZXQ');
  let release;
  const held = new Promise(resolve => { release = resolve; });
  const keys = [];
  await page.route('**/api/conversations/browser-conversation/messages', async route => {
    if (route.request().method() !== 'POST') { await route.continue(); return; }
    keys.push(route.request().postDataJSON().request_id);
    const response = await route.fetch();
    if (keys.length === 1) await held;
    await route.fulfill({ response });
  });
  try {
    await chat.getByRole('button', { name: 'Send Message', exact: true }).click();
    await expect(chat.getByRole('status')).toHaveText('Checking…');
    await expect(chat.getByRole('button', { name: 'Send Message', exact: true })).toBeDisabled();
    release();
    await expect(chat.getByRole('button', { name: 'Retry Message', exact: true })).toBeVisible();
    const retried = page.waitForResponse(response => response.url().endsWith('/messages') && response.request().method() === 'POST');
    await chat.getByRole('button', { name: 'Retry Message', exact: true }).click();
    await retried;
    await expect(chat.getByRole('button', { name: 'Retry Message', exact: true })).toBeEnabled();
    expect(keys).toHaveLength(2);
    expect(keys[0]).not.toBe(keys[1]);
  } finally { release(); }
});

test('inconsistent review-required retry flags are rejected and draft is retained', async ({ page }) => {
  await signIn(page, 'browser-a');
  const chat = page.getByRole('region', { name: 'Conversation', exact: true });
  await chat.getByLabel('Message', { exact: true }).fill('MalformedReceiptCanaryZXQ');
  await page.route('**/api/conversations/browser-conversation/messages', async route => {
    if (route.request().method() !== 'POST') { await route.continue(); return; }
    await route.fulfill({ status: 202, contentType: 'application/json', body: JSON.stringify({
      message_id: 'invalid-receipt', conversation_id: 'browser-conversation', outcome: 'Withheld',
      reason: 'review_required', review_state: 'pending', retry_allowed: true, can_submit_for_review: true,
    }) });
  });
  await chat.getByRole('button', { name: 'Send Message', exact: true }).click();
  await expect(chat.getByRole('alert')).toHaveText('Could not confirm your Message. Retry to check the same request.');
  await expect(chat.getByLabel('Message', { exact: true })).toHaveValue('MalformedReceiptCanaryZXQ');
});

test('submitting an older withheld attempt preserves a different unsent draft', async ({ page }) => {
  await signIn(page, 'browser-a');
  const chat = page.getByRole('region', { name: 'Conversation', exact: true });
  await chat.getByLabel('Message', { exact: true }).fill('OldReviewAttemptCanaryZXQ');
  await chat.getByRole('button', { name: 'Send Message', exact: true }).click();
  await expect(chat.getByRole('button', { name: 'Retry Message', exact: true })).toBeVisible();
  await chat.getByLabel('Message', { exact: true }).fill('A different unsent draft remains here.');
  const attempt = chat.getByRole('list', { name: 'Your Message status', exact: true }).getByRole('listitem').last();
  await attempt.getByRole('button', { name: 'Submit for review', exact: true }).click();
  await expect(attempt.getByText('Under review. Not delivered.', { exact: true })).toBeVisible();
  await expect(chat.getByLabel('Message', { exact: true })).toHaveValue('A different unsent draft remains here.');
});

test('withheld status never promises actions disallowed by the server', async ({ page }) => {
  await page.route('**/api/conversations/browser-conversation/messages', async route => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({
      conversation_id: 'browser-conversation', delivered: [], attempts: [{
        message_id: 'closed-attempt', conversation_id: 'browser-conversation', outcome: 'Withheld',
        reason: 'busy', review_state: 'not_submitted', retry_allowed: false, can_submit_for_review: false,
        provenance: 'none', identifier_reasons: [], created_at: '2026-11-16T12:00:00+00:00', delivered_at: null,
      }],
    }) });
  });
  await signIn(page, 'browser-a');
  const chat = page.getByRole('region', { name: 'Conversation', exact: true });
  await expect(chat.getByText('Withheld. Retry and review submission are unavailable.', { exact: true })).toBeVisible();
  await expect(chat.getByRole('button', { name: 'Submit for review', exact: true })).toHaveCount(0);
  await expect(chat.getByRole('button', { name: 'Retry Message', exact: true })).toHaveCount(0);
});

test('ambiguous network retry reuses its request key without creating a second attempt', async ({ page }) => {
  await signIn(page, 'browser-a');
  const chat = page.getByRole('region', { name: 'Conversation', exact: true });
  await chat.getByLabel('Message', { exact: true }).fill('AmbiguousRequestCanaryZXQ');
  const before = (await (await page.request.get('/api/conversations/browser-conversation/messages')).json()).attempts.length;
  const keys = [];
  await page.route('**/api/conversations/browser-conversation/messages', async route => {
    if (route.request().method() !== 'POST') { await route.continue(); return; }
    keys.push(route.request().postDataJSON().request_id);
    const response = await route.fetch();
    if (keys.length === 1) await route.abort('failed');
    else await route.fulfill({ response });
  });
  await chat.getByRole('button', { name: 'Send Message', exact: true }).click();
  await expect(chat.getByRole('alert')).toHaveText('Could not confirm your Message. Retry to check the same request.');
  await chat.getByRole('button', { name: 'Send Message', exact: true }).click();
  await expect(chat.getByRole('button', { name: 'Retry Message', exact: true })).toBeVisible();
  expect(keys).toHaveLength(2);
  expect(keys[0]).toBe(keys[1]);
  expect((await (await page.request.get('/api/conversations/browser-conversation/messages')).json()).attempts).toHaveLength(before + 1);
});

test('released HTML-like text stays inert in the recipient history', async ({ page, browser, request }) => {
  const body = '<img src=x onerror="window.messageExecuted=true"> Synthetic text.';
  await signIn(page, 'browser-a');
  const chat = page.getByRole('region', { name: 'Conversation', exact: true });
  await chat.getByLabel('Message', { exact: true }).fill(body);
  const sent = page.waitForResponse(response => response.url().endsWith('/messages') && response.request().method() === 'POST');
  await chat.getByRole('button', { name: 'Send Message', exact: true }).click();
  await sent;
  await expect(chat.getByRole('button', { name: 'Retry Message', exact: true })).toBeEnabled();
  const attempt = chat.getByRole('list', { name: 'Your Message status', exact: true }).getByRole('listitem').last();
  await attempt.getByRole('button', { name: 'Submit for review', exact: true }).click();
  await expect(attempt.getByText('Under review. Not delivered.', { exact: true })).toBeVisible();
  const headers = { Origin: 'http://127.0.0.1:8765' };
  expect((await request.post('/api/sessions', { headers, data: {
    email: 'browser.admin@example.invalid', password: 'Fictional admin password',
  } })).status()).toBe(200);
  const queue = (await (await request.get('/api/admin/messages')).json()).messages;
  const message = queue.find(item => item.text === body);
  expect(message).toBeTruthy();
  expect((await request.post(`/api/admin/messages/${message.message_id}/decision`, { headers, data: { decision: 'release' } })).status()).toBe(204);
  const context = await browser.newContext({ baseURL: 'http://127.0.0.1:8765' });
  try {
    const recipient = await context.newPage();
    await signIn(recipient, 'browser-b');
    const history = recipient.getByRole('log', { name: 'Delivered Messages', exact: true });
    await expect(history.getByText(body, { exact: true })).toBeVisible();
    await expect(history.locator('img')).toHaveCount(0);
    expect(await recipient.evaluate(() => window.messageExecuted)).toBeUndefined();
  } finally { await context.close(); }
});
