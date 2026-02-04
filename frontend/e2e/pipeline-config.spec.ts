import { test, expect } from '@playwright/test';

// Run tests serially to avoid race conditions with shared pipeline state
test.describe.configure({ mode: 'serial' });

test.describe('Pipeline Config Modal', () => {
  test.beforeEach(async ({ page, request }) => {
    // Stop any running pipeline before each test
    await request.post('http://localhost:8000/api/pipeline/stop');
    await page.goto('/');
    // Wait for page to be fully loaded and idle
    await expect(page.getByText('Idle')).toBeVisible({ timeout: 5000 });
  });

  test('Test 1: Open the Config Modal', async ({ page }) => {
    // Click "Run Pipeline" button
    await page.getByRole('button', { name: 'Run Pipeline' }).click();

    // Verify modal appears with "Configure Pipeline" title
    await expect(page.getByRole('heading', { name: 'Configure Pipeline' })).toBeVisible();
    await expect(page.getByText('Set the parameters for the pipeline run')).toBeVisible();

    // Verify form fields are present
    await expect(page.getByRole('textbox', { name: 'Niche *' })).toBeVisible();
    await expect(page.getByRole('spinbutton', { name: 'Max Sites' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Start Pipeline' })).toBeVisible();
  });

  test('Test 2: Validation - Niche required error', async ({ page }) => {
    // Open the modal
    await page.getByRole('button', { name: 'Run Pipeline' }).click();
    await expect(page.getByRole('heading', { name: 'Configure Pipeline' })).toBeVisible();

    // Click "Start Pipeline" without entering a niche
    await page.getByRole('button', { name: 'Start Pipeline' }).click();

    // Verify error message appears
    await expect(page.getByText('Niche is required')).toBeVisible();

    // Start typing in niche field
    await page.getByRole('textbox', { name: 'Niche *' }).fill('test');

    // Verify error clears
    await expect(page.getByText('Niche is required')).not.toBeVisible();
  });

  test('Test 3: Start Pipeline with Config', async ({ page }) => {
    // Open the modal
    await page.getByRole('button', { name: 'Run Pipeline' }).click();
    await expect(page.getByRole('heading', { name: 'Configure Pipeline' })).toBeVisible();

    // Enter "fitness" in niche field
    await page.getByRole('textbox', { name: 'Niche *' }).fill('fitness');

    // Set max sites to 5
    await page.getByRole('spinbutton', { name: 'Max Sites' }).fill('5');

    // Set up request interception to verify API call
    const requestPromise = page.waitForRequest((request) =>
      request.url().includes('/api/pipeline/run') && request.method() === 'POST'
    );

    // Also wait for the successful response
    const responsePromise = page.waitForResponse((response) =>
      response.url().includes('/api/pipeline/run') && response.status() === 200
    );

    // Click "Start Pipeline"
    await page.getByRole('button', { name: 'Start Pipeline' }).click();

    // Wait for and verify the API request
    const request = await requestPromise;
    const postData = request.postDataJSON();
    expect(postData).toEqual({
      niche: 'fitness',
      max_sites: 5,
    });

    // Wait for successful response
    const response = await responsePromise;
    const responseData = await response.json();
    expect(responseData.success).toBe(true);

    // Verify modal closes
    await expect(page.getByRole('heading', { name: 'Configure Pipeline' })).not.toBeVisible();

    // Wait for pipeline status to change to "Running" via WebSocket
    // Use a longer timeout since WebSocket updates may take time
    await expect(page.getByText('Running')).toBeVisible({ timeout: 10000 });

    // Verify "Stop Pipeline" button appears
    await expect(page.getByRole('button', { name: 'Stop Pipeline' })).toBeVisible({ timeout: 10000 });
  });

  test('Test 4: Cancel closes modal without starting pipeline', async ({ page }) => {
    // Verify initial state is "Idle"
    await expect(page.getByText('Idle')).toBeVisible();

    // Open the modal
    await page.getByRole('button', { name: 'Run Pipeline' }).click();
    await expect(page.getByRole('heading', { name: 'Configure Pipeline' })).toBeVisible();

    // Click "Cancel"
    await page.getByRole('button', { name: 'Cancel' }).click();

    // Verify modal closes
    await expect(page.getByRole('heading', { name: 'Configure Pipeline' })).not.toBeVisible();

    // Verify pipeline doesn't start (status remains "Idle")
    await expect(page.getByText('Idle')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Run Pipeline' })).toBeVisible();
  });

  test('Test 4b: Click outside modal closes it', async ({ page }) => {
    // Verify initial state is "Idle"
    await expect(page.getByText('Idle')).toBeVisible();

    // Open the modal
    await page.getByRole('button', { name: 'Run Pipeline' }).click();
    await expect(page.getByRole('heading', { name: 'Configure Pipeline' })).toBeVisible();

    // Click outside the modal (on the backdrop)
    // The modal has a backdrop that covers the screen
    await page.locator('body').click({ position: { x: 10, y: 10 } });

    // Verify modal closes
    await expect(page.getByRole('heading', { name: 'Configure Pipeline' })).not.toBeVisible();

    // Verify pipeline doesn't start (status remains "Idle")
    await expect(page.getByText('Idle')).toBeVisible();
  });
});
