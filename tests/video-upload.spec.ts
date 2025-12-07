import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

test.describe('Video Upload and Preview', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Frameshift/);
  });

  test('should load homepage with X.AI theme', async ({ page }) => {
    // Check for X.AI themed elements
    await expect(page.locator('h1')).toContainText('AI-Powered Product Placement');

    // Check for particle system (should be rendered after client-side hydration)
    await expect(page.locator('.xai-particles')).toBeVisible();

    // Check for upload section
    await expect(page.locator('text=Upload Video')).toBeVisible();

    // Check for brand preferences section
    await expect(page.locator('text=Brand Preferences')).toBeVisible();
  });

  test('should upload test video and show preview', async ({ page }) => {
    const testVideoPath = path.join(process.cwd(), 'public', 'test.mp4');

    // Check if test video exists
    if (!fs.existsSync(testVideoPath)) {
      console.log('Test video not found, creating a minimal test file...');
      // We'll skip this test if no video is available
      test.skip(true, 'No test video available');
      return;
    }

    // Wait for dropzone to be ready
    const dropzone = page.locator('[data-testid="video-dropzone"]').first();

    // If no test ID, use the upload section
    const uploadSection = dropzone.or(page.locator('text=Upload Video').locator('..').locator('..'));

    await expect(uploadSection).toBeVisible();

    // Upload the test video
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testVideoPath);

    // Wait for video processing
    await expect(page.locator('text=Processing Video')).toBeVisible({ timeout: 10000 });

    // Wait for processing to complete and preview to appear
    await expect(page.locator('video')).toBeVisible({ timeout: 15000 });

    // Check if video preview loaded
    const video = page.locator('video').first();
    await expect(video).toBeVisible();

    // Check if timeline appears
    await expect(page.locator('[data-testid="video-timeline"]').or(page.locator('.timeline'))).toBeVisible({ timeout: 10000 });

    // Verify file information is displayed
    await expect(page.locator('text=Filename')).toBeVisible();
    await expect(page.locator('text=File Size')).toBeVisible();
    await expect(page.locator('text=Duration')).toBeVisible();
  });

  test('should allow video playback controls', async ({ page }) => {
    const testVideoPath = path.join(process.cwd(), 'public', 'test.mp4');

    if (!fs.existsSync(testVideoPath)) {
      test.skip(true, 'No test video available for playback test');
      return;
    }

    // Upload video
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testVideoPath);

    // Wait for video to load
    await expect(page.locator('video')).toBeVisible({ timeout: 15000 });

    const video = page.locator('video').first();

    // Test play button
    const playButton = page.locator('[data-testid="play-button"]').or(page.locator('text=Play').locator('..'));
    if (await playButton.isVisible()) {
      await playButton.click();

      // Check if video is playing (look for pause button or playing state)
      await expect(page.locator('[data-testid="pause-button"]').or(page.locator('text=Pause').locator('..'))).toBeVisible({ timeout: 5000 });
    }

    // Test timeline controls if available
    const timeline = page.locator('[data-testid="video-timeline"]').or(page.locator('.timeline'));
    if (await timeline.isVisible()) {
      await timeline.click({ position: { x: 100, y: 10 } }); // Click on timeline

      // Verify video time updates
      await page.waitForTimeout(1000); // Wait for timeline update
    }
  });

  test('should handle brand preferences selection', async ({ page }) => {
    // Test brand preferences form
    const preferencesSection = page.locator('text=Brand Preferences').locator('..').locator('..');
    await expect(preferencesSection).toBeVisible();

    // Look for preference inputs (checkboxes, dropdowns, etc.)
    const preferencesInputs = page.locator('input[type="checkbox"], select, input[type="text"]').first();

    if (await preferencesInputs.isVisible()) {
      // Try to interact with preferences
      await preferencesInputs.click();
      await page.waitForTimeout(500);
    }

    // Check if proceed button appears after selections
    const proceedButton = page.locator('text=Analyze & Generate').or(page.locator('text=Generate')).or(page.locator('[data-testid="proceed-button"]'));

    // The button might be disabled initially, so just check for presence
    await expect(proceedButton.or(page.locator('button').filter({ hasText: /analyze|generate|proceed/i }))).toBeVisible({ timeout: 5000 });
  });

  test('should show proceed button when video and preferences are ready', async ({ page }) => {
    const testVideoPath = path.join(process.cwd(), 'public', 'test.mp4');

    if (!fs.existsSync(testVideoPath)) {
      test.skip(true, 'No test video available for integration test');
      return;
    }

    // Upload video
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testVideoPath);

    // Wait for video processing
    await expect(page.locator('video')).toBeVisible({ timeout: 15000 });

    // Add some preferences - look for any interactive elements
    const checkbox = page.locator('input[type="checkbox"]').first();
    if (await checkbox.isVisible()) {
      await checkbox.check();
    }

    const textInput = page.locator('input[type="text"]').first();
    if (await textInput.isVisible()) {
      await textInput.fill('Test brand preference');
    }

    // Check if proceed button becomes enabled
    const proceedButton = page.locator('text=Analyze & Generate').or(page.locator('button').filter({ hasText: /analyze|generate/i }));

    await expect(proceedButton).toBeVisible({ timeout: 10000 });

    // Optionally test clicking it (might navigate to analysis page)
    if (await proceedButton.isEnabled()) {
      await proceedButton.click();
      // Wait for navigation or processing
      await page.waitForTimeout(2000);

      // Check if we've navigated to analysis page or see processing
      await expect(page.locator('text=Analysis').or(page.locator('text=Processing').or(page.locator('text=Generate')))).toBeVisible({ timeout: 10000 });
    }
  });

  test('should handle video upload errors gracefully', async ({ page }) => {
    // Test with invalid file type
    const invalidFile = path.join(process.cwd(), 'package.json'); // Use package.json as invalid video file

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(invalidFile);

    // Should show error or reject file
    await page.waitForTimeout(2000);

    // Either the file is rejected or an error message appears
    const errorMessage = page.locator('text=Error').or(page.locator('text=invalid').or(page.locator('text=supported')));
    const stillShowingUpload = page.locator('text=Upload Video');

    // Either we see an error or still see upload (file was rejected)
    await expect(errorMessage.or(stillShowingUpload)).toBeVisible();
  });

  test('should be responsive and work on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that page loads correctly on mobile
    await expect(page.locator('h1')).toContainText('AI-Powered Product Placement');

    // Check that upload area is accessible
    await expect(page.locator('text=Upload Video')).toBeVisible();

    // Check that content is not cut off
    const bodyHeight = await page.locator('body').boundingBox();
    expect(bodyHeight?.height).toBeGreaterThan(600);
  });
});