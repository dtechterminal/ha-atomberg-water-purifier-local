import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/browser',
  use: { baseURL: 'http://127.0.0.1:8766', headless: true },
  webServer: { command: 'python3 -m http.server 8766 --bind 127.0.0.1 --directory ..', url: 'http://127.0.0.1:8766/frontend/demo/', reuseExistingServer: true },
});
