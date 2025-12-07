import { test, expect } from '@playwright/test';

test.describe('Frameshift Basic Tests', () => {
  test('should load homepage', async ({ page }) => {
    await page.goto('/');

    // Check if the page loads
    await expect(page.locator('h1')).toContainText('AI-Powered Product Placement');

    // Check for main sections
    await expect(page.locator('text=Upload Video')).toBeVisible();
    await expect(page.locator('text=Brand Preferences')).toBeVisible();

    console.log('Page loaded successfully');
  });

  test('should display video dropzone', async ({ page }) => {
    await page.goto('/');

    // Check for video dropzone
    await expect(page.locator('[data-testid="video-dropzone"]')).toBeVisible();
    await expect(page.locator('text=Drop a video file here, or click to select')).toBeVisible();

    console.log('Video dropzone is visible');
  });

  test('should check video loading errors in console', async ({ page }) => {
    const consoleMessages = [];
    const errors = [];

    // Listen for console messages
    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text()
      });

      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Navigate to the page
    await page.goto('/');

    // Try to upload a video by setting files directly on the input
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles('/Users/ammadhassan/Downloads/xAIhackathon/frameshift/public/test.mp4');

    // Wait for potential processing
    await page.waitForTimeout(5000);

    // Log all console messages
    console.log('Console messages:', consoleMessages);
    console.log('Errors:', errors);

    // Check for specific video loading errors
    const videoErrors = errors.filter(error =>
      error.includes('Video loading error') ||
      error.includes('video') ||
      error.toLowerCase().includes('metadata')
    );

    console.log('Video-related errors:', videoErrors);

    if (videoErrors.length > 0) {
      console.log('FOUND VIDEO LOADING ERRORS:');
      videoErrors.forEach(error => console.log(`  - ${error}`));
    }
  });

  test('should test brand preferences form', async ({ page }) => {
    await page.goto('/');

    // Add a brand name
    const brandInput = page.locator('input[placeholder*="Add brand"]');
    await brandInput.fill('Apple');
    await brandInput.press('Enter');

    // Check if brand badge appears
    await expect(page.locator('[data-testid="brand-badge"]').first()).toContainText('Apple');

    console.log('Brand preferences work correctly');
  });

  test('should test product selector', async ({ page }) => {
    await page.goto('/');

    // Show product selector
    await page.locator('text=Show Products').click();

    // Check if products are visible
    await expect(page.locator('text=iPhone 15 Pro')).toBeVisible();
    await expect(page.locator('text=Nike Air Max')).toBeVisible();

    // Click on a product
    await page.locator('text=iPhone 15 Pro').locator('..').click();

    // Check if product is selected
    await expect(page.locator('text=Selected Products: iPhone 15 Pro')).toBeVisible();

    console.log('Product selector works correctly');
  });
});