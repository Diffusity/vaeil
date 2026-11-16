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
