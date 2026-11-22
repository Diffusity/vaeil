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
  await expect(consolePanel.getByText('Report queue is unavailable.')).toBeVisible();

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
