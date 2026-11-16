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
