import { defineConfig, devices } from '@playwright/test';

/**
 * Minimal config for exhaustive audit — reuses running server on port 3000.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  timeout: 120000,
  expect: { timeout: 15000 },
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3100',
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    viewport: { width: 1920, height: 1080 },
    actionTimeout: 30000,
    navigationTimeout: 60000,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'],
        },
      },
    },
  ],
  outputDir: 'e2e-audit-evidence',
  // No webServer — reuse running server on :3000
});
