import { test, expect } from '@playwright/test';

const origin = { Origin: 'http://127.0.0.1:8765' };
const password = 'Fictional profile password';

async function member(page, index, decision = 'approve') {
  const email = `profile${index}@example.invalid`;
  const applied = await page.request.post('/api/applications', { headers: origin, data: {
    legal_name: `FictionalProfile${index}`, email, date_of_birth: '2000-01-01',
    invite_code: `h1-invite-${index}`, password,
    application_note: 'I seek a thoughtful long term relationship.',
  } });
  expect(applied.status()).toBe(202);
  if (decision) {
    expect((await page.request.post('/api/sessions', { headers: origin, data: {
      email: 'browser.admin@example.invalid', password: 'Fictional admin password',
    } })).status()).toBe(200);
    const id = (await applied.json()).applicant_id;
    expect((await page.request.post(`/api/admin/applications/${id}/decision`, {
      headers: origin, data: { decision },
    })).status()).toBe(204);
    expect((await page.request.delete('/api/session', { headers: origin })).status()).toBe(204);
  }
  await page.goto('/');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Sign out', exact: true })).toBeVisible();
  return email;
}

test('admitted Member saves and reloads a private partial draft through the real API', async ({ page }) => {
  await member(page, 0);
  const form = page.getByRole('form', { name: 'Your Values Profile', exact: true });
  await expect(form).toBeVisible();
  await form.getByLabel('About (optional)', { exact: true }).fill('I enjoy quiet walks.');
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('status')).toHaveText('Draft saved. Complete all choices and choose a Pseudonym when you are ready.');
  const saved = await page.request.get('/api/me/profile');
  expect((await saved.json()).complete).toBe(false);
  await page.reload();
  await expect(form.getByLabel('About (optional)', { exact: true })).toHaveValue('I enjoy quiet walks.');
  await expect(form.getByLabel('Relationship intent', { exact: true })).toHaveValue('');
});

async function complete(form, pseudonym) {
  await form.getByLabel('Pseudonym', { exact: true }).fill(pseudonym);
  await form.getByLabel('Relationship intent', { exact: true }).selectOption('long_term');
  await form.getByLabel('Life stage', { exact: true }).selectOption('undergraduate');
  await form.getByLabel('Communication style', { exact: true }).selectOption('direct');
  await form.getByLabel('Pace and lifestyle', { exact: true }).selectOption('quiet_and_routine');
  await form.getByRole('checkbox', { name: 'Reading', exact: true }).check();
  await form.getByRole('checkbox', { name: 'Honesty', exact: true }).check();
}

test('complete and update without reclaiming name; unsafe About keeps unsaved text with safe rephrase guidance', async ({ page }) => {
  await member(page, 1);
  const form = page.getByRole('form', { name: 'Your Values Profile', exact: true });
  await complete(form, 'Orbit');
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('status')).toHaveText('Profile saved.');
  await expect(form.getByLabel('Pseudonym', { exact: true })).toHaveCount(0);
  await expect(form.getByText('Pseudonym: Orbit (fixed)', { exact: true })).toBeVisible();
  await form.getByLabel('About (optional)', { exact: true }).fill('I enjoy quiet reading.');
  const request = page.waitForRequest(r => r.url().endsWith('/api/me/profile') && r.method() === 'PUT');
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  expect((await request).postDataJSON()).not.toHaveProperty('pseudonym');
  await expect(form.getByRole('status')).toHaveText('Profile saved.');
  const unsafe = 'Contact contactcanary@example.invalid';
  await form.getByLabel('About (optional)', { exact: true }).fill(unsafe);
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('alert')).toHaveText('About: Rephrase without contact details or your own name.');
  await expect(form.getByLabel('About (optional)', { exact: true })).toHaveValue(unsafe);
  expect((await (await page.request.get('/api/me/profile')).json()).values_profile.about).toBe('I enjoy quiet reading.');
  await form.getByLabel('About (optional)', { exact: true }).fill('I enjoy music too.');
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('status')).toHaveText('Profile saved.');
});

const empty = { complete: false, values_profile: { pseudonym: null, relationship_intent: null,
  life_stage: null, interests: [], values: [], communication_style: null, pace_and_lifestyle: null, about: '' } };
for (const [name, payload, index] of [
  ['missing profile', { complete: false }, 2],
  ['unknown code', { ...empty, values_profile: { ...empty.values_profile, communication_style: 'unknown' } }, 3],
  ['duplicate selections', { ...empty, values_profile: { ...empty.values_profile, interests: ['reading', 'reading'] } }, 4],
  ['invalid complete response', { ...empty, complete: true, pseudonym: 'Star' }, 5],
]) {
  test(`malformed ${name} is refused with a retry to the real API`, async ({ page }) => {
    await page.route('**/api/me/profile', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) }), { times: 1 });
    await member(page, index);
    await expect(page.getByRole('alert')).toHaveText('Could not load your profile. Please retry.');
    await expect(page.getByRole('form', { name: 'Your Values Profile', exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: 'Retry profile', exact: true }).click();
    await expect(page.getByRole('form', { name: 'Your Values Profile', exact: true })).toBeVisible();
  });
}

for (const [decision, index, message] of [
  [null, 6, 'Your application is under review.'],
  ['reject', 7, 'An Admin has declined your application.'],
]) {
  test(`${decision || 'pending'} admission never exposes the profile editor`, async ({ page }) => {
    await member(page, index, decision);
    await expect(page.getByText(message, { exact: true })).toBeVisible();
    await expect(page.getByRole('form', { name: 'Your Values Profile', exact: true })).toHaveCount(0);
    expect((await page.request.get('/api/me/profile')).status()).toBe(403);
    await page.reload();
    await expect(page.getByText(message, { exact: true })).toBeVisible();
    await expect(page.getByRole('form', { name: 'Your Values Profile', exact: true })).toHaveCount(0);
  });
}

test('a revoked session cannot save and returns the Member to sign in', async ({ page }) => {
  await member(page, 8);
  const form = page.getByRole('form', { name: 'Your Values Profile', exact: true });
  await form.getByLabel('About (optional)', { exact: true }).fill('Unsaved draft.');
  expect((await page.request.delete('/api/session', { headers: origin })).status()).toBe(204);
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(page.getByText('Your session has expired. Please sign in again.', { exact: true })).toBeVisible();
  await expect(form).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible();
});

test('taken Pseudonym can be corrected without losing the completed choices', async ({ page }) => {
  await member(page, 9);
  expect((await page.request.put('/api/me/profile', { headers: origin, data: {
    pseudonym: 'H1Owned', relationship_intent: 'long_term', life_stage: 'undergraduate',
    interests: ['reading'], values: ['honesty'], communication_style: 'direct',
    pace_and_lifestyle: 'quiet_and_routine', about: '',
  } })).status()).toBe(200);
  await member(page, 10);
  const form = page.getByRole('form', { name: 'Your Values Profile', exact: true });
  await complete(form, 'H1Owned');
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('alert')).toHaveText('Pseudonym: This name is taken. Choose another and retry.');
  await expect(form.getByLabel('Relationship intent', { exact: true })).toHaveValue('long_term');
  await form.getByLabel('Pseudonym', { exact: true }).fill('H1Retry');
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('status')).toHaveText('Profile saved.');
});

test('storage failure retains text and selections, retries, and does not copy identity into browser storage or logs', async ({ page }) => {
  const logs = [];
  page.on('console', message => logs.push(message.text()));
  page.on('pageerror', error => logs.push(error.message));
  const email = await member(page, 11);
  const form = page.getByRole('form', { name: 'Your Values Profile', exact: true });
  await form.getByLabel('About (optional)', { exact: true }).fill('I enjoy gentle walks.');
  await form.getByRole('checkbox', { name: 'Music', exact: true }).check();
  await page.route('**/api/me/profile', async route => {
    if (route.request().method() === 'PUT') await route.fulfill({ status: 503, contentType: 'application/json', body: '{"reason":"PrivateErrorCanary"}' });
    else await route.continue();
  }, { times: 1 });
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('alert')).toHaveText('Could not save your profile. Your changes are still here; please retry.');
  await expect(form.getByLabel('About (optional)', { exact: true })).toHaveValue('I enjoy gentle walks.');
  await expect(form.getByRole('checkbox', { name: 'Music', exact: true })).toBeChecked();
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('status')).toContainText('Draft saved.');
  for (const canary of [email, 'FictionalProfile11', 'PrivateErrorCanary', password]) {
    expect(logs.join('\n')).not.toContain(canary);
    await expect(page.locator('body')).not.toContainText(canary);
  }
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual([]);
});

test('server normalization and code-point limits remain authoritative without truncation', async ({ page }) => {
  await member(page, 12);
  const form = page.getByRole('form', { name: 'Your Values Profile', exact: true });
  const about = form.getByLabel('About (optional)', { exact: true });
  await about.fill('🙂'.repeat(280));
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('status')).toContainText('Draft saved.');
  await expect(about).toHaveValue('🙂'.repeat(280));
  await about.fill('🙂'.repeat(281));
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('alert')).toBeVisible();
  await expect(about).toHaveValue('🙂'.repeat(281));
  expect((await (await page.request.get('/api/me/profile')).json()).values_profile.about).toBe('🙂'.repeat(280));
  await about.fill('  Ｈｅｌｌｏ walks.  ');
  await form.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(form.getByRole('status')).toContainText('Draft saved.');
  await expect(about).toHaveValue('Hello walks.');
});
