import { test, expect } from '@playwright/test';

test('fictional applicant registers, signs in restricted, then logs out through the real API', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Apply with an Invite', exact: true }).click();
  await expect(page.getByText(/demo only.*fictional details/i)).toBeVisible();
  await page.getByLabel('Legal name', { exact: true }).fill('FictionalBrowser');
  await page.getByLabel('Email', { exact: true }).fill('browser.persona@example.invalid');
  await page.getByLabel('Date of birth', { exact: true }).fill('2000-01-01');
  await page.getByLabel('Invite code', { exact: true }).fill('browser-invite');
  await page.getByLabel('Password', { exact: true }).fill('Fictional browser password');
  await page.getByLabel('Application note', { exact: true }).fill('I seek a thoughtful long term relationship.');
  const applied = page.waitForResponse(response => response.url().endsWith('/api/applications') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Submit application', exact: true }).click();
  expect((await applied).status()).toBe(202);
  await expect(page.getByText('Application received. Your application is under review.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByLabel('Email', { exact: true }).fill('browser.persona@example.invalid');
  await page.getByLabel('Password', { exact: true }).fill('Fictional browser password');
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByText('Your application is under review.', { exact: true })).toBeVisible();
  const restricted = await page.request.get('/api/me/profile');
  expect(restricted.status()).toBe(403);
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByText('You are signed out.', { exact: true })).toBeVisible();
});

test('registration failure shows a rephrase message and permits retry', async ({ page }) => {
  await page.route('**/api/applications', route => route.fulfill({ status: 400, contentType: 'application/json', body: '{"reason":"invalid_note"}' }));
  await page.goto('/');
  await page.getByRole('button', { name: 'Apply with an Invite', exact: true }).click();
  await page.getByLabel('Legal name', { exact: true }).fill('FictionalBrowser');
  await page.getByLabel('Email', { exact: true }).fill('fiction@example.invalid');
  await page.getByLabel('Date of birth', { exact: true }).fill('2000-01-01');
  await page.getByLabel('Invite code', { exact: true }).fill('fictional');
  await page.getByLabel('Password', { exact: true }).fill('Fictional browser password');
  await page.getByLabel('Application note', { exact: true }).fill('I seek a thoughtful long term relationship.');
  await page.getByRole('button', { name: 'Submit application', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveText('Remove contact details or rephrase your application note.');
  await expect(page.getByRole('button', { name: 'Submit application', exact: true })).toBeEnabled();
});
