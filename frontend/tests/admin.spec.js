import { test, expect } from '@playwright/test';

test('Admin issues an Invite and approves the resulting pending application', async ({ page }) => {
  const note = 'I seek a thoughtful long term relationship with shared goals.';
  async function signIn() {
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByLabel('Email', { exact: true }).fill('browser.admin@example.invalid');
    await page.getByLabel('Password', { exact: true }).fill('Fictional admin password');
    await page.getByRole('button', { name: 'Continue' }).click();
  }

  await page.goto('/');
  await signIn();
  const consolePanel = page.getByRole('region', { name: 'Admin console' });
  await expect(consolePanel).toBeVisible({ timeout: 3000 });
  await consolePanel.getByRole('button', { name: 'Issue Invite' }).click();
  const code = consolePanel.getByLabel('Issued Invite code');
  await expect(code).toHaveValue(/^[A-Za-z0-9_-]{40,}$/);
  const invite = await code.inputValue();
  await expect(consolePanel.getByRole('button', { name: 'Copy Invite' })).toBeEnabled();
  await expect(consolePanel.getByText('No Reports awaiting review.')).toBeVisible();

  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(code).toHaveCount(0);
  await page.getByRole('button', { name: 'Apply with an Invite' }).click();
  await page.getByLabel('Legal name', { exact: true }).fill('FictionalConsole');
  await page.getByLabel('Email', { exact: true }).fill('console.persona@example.invalid');
  await page.getByLabel('Date of birth', { exact: true }).fill('2000-01-01');
  await page.getByLabel('Invite code', { exact: true }).fill(invite);
  await page.getByLabel('Password', { exact: true }).fill('Fictional console password');
  await page.getByLabel('Application note', { exact: true }).fill(note);
  await page.getByRole('button', { name: 'Submit application' }).click();
  await expect(page.getByText('Application received. Your application is under review.')).toBeVisible();

  await signIn();
  const pending = consolePanel.getByRole('listitem').filter({ hasText: note });
  await expect(pending).toBeVisible();
  await pending.getByRole('button', { name: 'Approve' }).click();
  await expect(pending).toHaveCount(0);
  await expect(consolePanel.getByText('No applications awaiting review.')).toBeVisible();
});

test('queue decisions wait for both initial responses before refreshing', async ({ page }) => {
  let release;
  const held = new Promise(resolve => { release = resolve; });
  await page.route('**/api/admin/messages', async route => {
    await held;
    await route.fulfill({ json: { messages: [] } });
  });
  await page.route('**/api/admin/applications', route => route.fulfill({
    json: { applications: [{ applicant_id: 'fixture', application_note: 'A queued application.' }] },
  }));
  try {
    await page.goto('/');
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByLabel('Email', { exact: true }).fill('browser.admin@example.invalid');
    await page.getByLabel('Password', { exact: true }).fill('Fictional admin password');
    await page.getByRole('button', { name: 'Continue' }).click();
    const approve = page.getByRole('button', { name: 'Approve', exact: true });
    await expect(approve).toBeVisible();
    await expect(approve).toBeDisabled({ timeout: 2000 });
    release();
    await expect(approve).toBeEnabled();
  } finally {
    release();
  }
});

const origin = 'http://127.0.0.1:8765';
const headers = { Origin: origin };
const adminEmail = 'browser.admin@example.invalid';
const adminPassword = 'Fictional admin password';

async function signInAs(page, email, password) {
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Sign out', exact: true })).toBeVisible();
}

test('Admin console Reject, Release, Discard and Escalated decisions work against the real API', async ({ page, request }) => {
  await page.goto('/');
  await signInAs(page, adminEmail, adminPassword);
  const panel = page.getByRole('region', { name: 'Admin console' });
  const note = 'I hope to meet someone who enjoys a calm routine.';
  const email = 'admin-reject.persona@example.invalid';
  const password = 'Fictional rejected password';
  const invite = await page.request.post('/api/admin/invites', { headers });
  expect(invite.status()).toBe(201);
  expect((await page.request.post('/api/applications', { headers, data: {
    legal_name: 'FictionalRejected', date_of_birth: '2000-01-01', email, password, application_note: note,
    invite_code: (await invite.json()).invite_code,
  } })).status()).toBe(202);

  async function apiSignIn(identifier, secret = 'Fictional chat password') {
    expect((await request.post('/api/sessions', { headers, data: { email: identifier, password: secret } })).status()).toBe(200);
  }
  const releaseText = 'AdminReleaseCanary <b>literal markup</b>.';
  const discardText = 'AdminDiscardCanary remains private.';
  const approveEscalated = 'AdminEscalatedApprove 98765.43210.';
  const rejectEscalated = 'AdminEscalatedReject 98765.43211.';
  await apiSignIn('browser-a@example.invalid');
  for (const text of [releaseText, discardText, approveEscalated, rejectEscalated]) {
    const sent = await request.post('/api/conversations/browser-conversation/messages', {
      headers, data: { request_id: crypto.randomUUID(), text },
    });
    expect(sent.status()).toBe(202);
    const payload = await sent.json();
    expect(payload.outcome).toBe('Withheld');
    const review = await request.post('/api/messages/' + payload.message_id + '/review', { headers });
    expect(review.status()).toBe(202);
  }
  await apiSignIn('browser-b@example.invalid');
  async function history() {
    const result = await request.get('/api/conversations/browser-conversation/messages');
    expect(result.status()).toBe(200);
    return (await result.json()).delivered.map(item => item.text);
  }
  expect(await history()).not.toContain(releaseText);
  expect(await history()).not.toContain(discardText);
  await panel.getByRole('button', { name: 'Refresh queues' }).click();
  async function decide(text, label) {
    const item = panel.getByRole('listitem').filter({ has: page.getByText(text, { exact: true }) });
    await item.getByRole('button', { name: label, exact: true }).click();
  }
  await decide(note, 'Reject');
  await expect(panel.getByText('No applications awaiting review.')).toBeVisible();
  await expect(panel.getByText(releaseText, { exact: true })).toBeVisible();
  await expect(panel.locator('b')).toHaveCount(0);
  await decide(releaseText, 'Release');
  await decide(discardText, 'Discard');
  await decide(approveEscalated, 'Release');
  await decide(rejectEscalated, 'Release');
  await expect(panel.getByRole('listitem').filter({ hasText: rejectEscalated }).getByRole('button', { name: 'Reject' })).toBeVisible();
  await expect.poll(history).toEqual(expect.arrayContaining([releaseText, approveEscalated, rejectEscalated]));
  expect(await history()).not.toContain(discardText);
  await decide(approveEscalated, 'Approve');
  await decide(rejectEscalated, 'Reject');
  await expect(panel.getByText(rejectEscalated, { exact: true })).toHaveCount(0);
  const result = await page.request.get('/api/admin/messages');
  expect(result.status()).toBe(200);
  const remaining = (await result.json()).messages.map(item => item.text);
  expect(remaining).not.toContain(approveEscalated);
  expect(remaining).not.toContain(rejectEscalated);
  expect(await history()).toEqual(expect.arrayContaining([releaseText, approveEscalated, rejectEscalated]));
  expect(await history()).not.toContain(discardText);
  await apiSignIn(email, password);
  expect((await (await request.get('/api/session')).json()).admission).toBe('Rejected');
});

test('an old Admin 401 cannot end a newer Member session', async ({ page }) => {
  // Simulate a response already in flight that arrives despite cancellation.
  await page.addInitScript(() => {
    const fetch = window.fetch.bind(window);
    window.fetch = async (path, options) => {
      if (path !== '/api/admin/applications') return fetch(path, options);
      const response = await fetch(path, { ...options, signal: undefined });
      setTimeout(() => { document.body.dataset.oldAdminResponse = String(response.status); }, 0);
      return response;
    };
  });
  let release;
  const hold = new Promise(resolve => { release = resolve; });
  let intercepted;
  const started = new Promise(resolve => { intercepted = resolve; });
  await page.route('**/api/admin/applications', async route => {
    intercepted();
    await hold;
    await route.fulfill({ status: 401, json: { reason: 'invalid_credentials' } });
  });
  try {
    await page.goto('/');
    await signInAs(page, adminEmail, adminPassword);
    await started;
    await page.getByRole('button', { name: 'Sign out' }).click();
    await signInAs(page, 'browser-a@example.invalid', 'Fictional chat password');
    release();
    await expect(page.locator('body')).toHaveAttribute('data-old-admin-response', '401');
    await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible();
    await expect(page.getByText('Your session has expired. Please sign in again.')).toHaveCount(0);
    await expect(page.getByRole('region', { name: 'Admin console' })).toHaveCount(0);
  } finally {
    release();
  }
});
