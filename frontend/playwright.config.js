import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:8765', browserName: 'chromium', channel: process.env.CI ? undefined : 'msedge' },
  webServer: {
    command: '..\\.venv\\Scripts\\python.exe -m uvicorn vaeil.web:create_app --factory --host 127.0.0.1 --port 8765',
    url: 'http://127.0.0.1:8765/api/health',
    reuseExistingServer: false,
    timeout: 30000,
  },
});
