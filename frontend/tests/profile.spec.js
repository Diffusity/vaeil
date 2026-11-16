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
