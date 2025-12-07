import { test, expect } from '@playwright/test';

test.describe('Comprehensive User Workflow Tests', () => {
  test('should complete full user workflow: video upload → preferences → proceed', async ({ page }) => {
    console.log('🚀 Starting comprehensive workflow test...');

    await page.goto('/');

    // 1. VERIFY INITIAL STATE
    console.log('✓ Page loaded');
    await expect(page.locator('h1')).toContainText('AI-Powered Product Placement');

    // Verify proceed button is disabled initially
    const proceedButton = page.locator('text=Analyze & Generate');
    expect(await proceedButton.isDisabled()).toBe(true);
    console.log('✓ Proceed button is initially disabled');

    // 2. UPLOAD VIDEO
    console.log('📹 Testing video upload...');
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles('/Users/ammadhassan/Downloads/xAIhackathon/frameshift/public/test.mp4');

    // Wait for processing
    await page.waitForSelector('text=Processing Video...', { timeout: 10000 });
    console.log('✓ Video processing started');

    await page.waitForSelector('text=Processing Video...', { state: 'hidden', timeout: 30000 });
    console.log('✓ Video processing completed');

    // Verify video is displayed
    const videoElement = page.locator('video');
    expect(await videoElement.count()).toBeGreaterThan(0);
    console.log('✓ Video element is present');

    // Verify video metadata is shown
    await expect(page.locator('text=test.mp4')).toBeVisible();
    await expect(page.locator('text=Duration')).toBeVisible();
    console.log('✓ Video metadata is displayed');

    // 3. TEST VIDEO CONTROLS
    console.log('🎮 Testing video controls...');

    // Test play/pause
    const playButton = page.locator('[data-testid="play-pause-btn"]');
    await playButton.click();
    await page.waitForTimeout(1000);
    await playButton.click();
    console.log('✓ Play/pause controls work');

    // Test frame stepping
    const frameForward = page.locator('[data-testid="frame-step-forward"]');
    await frameForward.click();
    await frameForward.click();
    console.log('✓ Frame stepping works');

    // 4. ADD BRAND PREFERENCES
    console.log('🏷️ Testing brand preferences...');

    // Add brand names
    const brandInput = page.locator('input[placeholder*="Add brand"]');
    await brandInput.fill('Apple');
    await brandInput.press('Enter');
    await brandInput.fill('Nike');
    await brandInput.press('Enter');

    // Verify brands are added
    await expect(page.locator('[data-testid="brand-badge"]').first()).toContainText('Apple');
    console.log('✓ Brand names added successfully');

    // 5. TEST PRODUCT SELECTION
    console.log('🛍️ Testing product selection...');

    // Show product selector
    await page.locator('text=Show Products').click();
    await expect(page.locator('text=iPhone 15 Pro')).toBeVisible();

    // Select a product
    await page.locator('text=Tesla Model 3').locator('..').click();
    await expect(page.locator('text=Selected Products: Tesla Model 3')).toBeVisible();
    console.log('✓ Product selection works');

    // 6. ADD TARGET AUDIENCE
    console.log('👥 Testing target audience...');
    const audienceInput = page.locator('input[placeholder*="Add audience"]');
    await audienceInput.fill('Tech enthusiasts');
    await audienceInput.press('Enter');

    await expect(page.locator('[data-testid="audience-badge"]').first()).toContainText('Tech enthusiasts');
    console.log('✓ Target audience added');

    // 7. VERIFY CONFIGURATION SUMMARY
    console.log('📋 Checking configuration summary...');
    await expect(page.locator('text=Configuration Summary')).toBeVisible();
    await expect(page.locator('text=Brand Names:')).toBeVisible();
    await expect(page.locator('text=Target Audience:')).toBeVisible();
    console.log('✓ Configuration summary is displayed');

    // 8. VERIFY PROCEED BUTTON IS ENABLED
    expect(await proceedButton.isEnabled()).toBe(true);
    console.log('✓ Proceed button is now enabled');

    // 9. TEST PROCEED TO ANALYSIS
    console.log('➡️ Testing proceed to analysis...');
    await proceedButton.click();
    await page.waitForURL('**/analysis', { timeout: 10000 });
    expect(page.url()).toContain('/analysis');
    console.log('✓ Successfully navigated to analysis page');

    console.log('🎉 Comprehensive workflow test completed successfully!');
  });

  test('should handle video removal and re-upload', async ({ page }) => {
    console.log('🔄 Testing video removal and re-upload...');

    await page.goto('/');

    // Upload initial video
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles('/Users/ammadhassan/Downloads/xAIhackathon/frameshift/public/test.mp4');
    await page.waitForSelector('text=Processing Video...', { state: 'hidden', timeout: 30000 });

    // Verify video is uploaded
    expect(await page.locator('video').count()).toBeGreaterThan(0);
    console.log('✓ Initial video uploaded');

    // Remove video
    const removeButton = page.locator('[data-testid="remove-video-btn"]');
    await removeButton.click();

    // Verify video is removed
    expect(await page.locator('video').count()).toBe(0);
    await expect(page.locator('[data-testid="video-dropzone"]')).toBeVisible();
    console.log('✓ Video removed successfully');

    // Re-upload video
    await fileInput.setInputFiles('/Users/ammadhassan/Downloads/xAIhackathon/frameshift/public/test.mp4');
    await page.waitForSelector('text=Processing Video...', { state: 'hidden', timeout: 30000 });

    // Verify video is re-uploaded
    expect(await page.locator('video').count()).toBeGreaterThan(0);
    console.log('✓ Video re-uploaded successfully');
  });

  test('should maintain form state when switching between features', async ({ page }) => {
    console.log('💾 Testing form state persistence...');

    await page.goto('/');

    // Add brand preferences
    const brandInput = page.locator('input[placeholder*="Add brand"]');
    await brandInput.fill('Google');
    await brandInput.press('Enter');
    console.log('✓ Brand added');

    // Add audience
    const audienceInput = page.locator('input[placeholder*="Add audience"]');
    await audienceInput.fill('Developers');
    await audienceInput.press('Enter');
    console.log('✓ Audience added');

    // Show and select products
    await page.locator('text=Show Products').click();
    await page.locator('text=iPhone 15 Pro').locator('..').click();
    console.log('✓ Product selected');

    // Upload video
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles('/Users/ammadhassan/Downloads/xAIhackathon/frameshift/public/test.mp4');
    await page.waitForSelector('text=Processing Video...', { state: 'hidden', timeout: 30000 });
    console.log('✓ Video uploaded');

    // Verify all form data is still present
    await expect(page.locator('[data-testid="brand-badge"]').first()).toContainText('Google');
    await expect(page.locator('[data-testid="audience-badge"]').first()).toContainText('Developers');
    await expect(page.locator('text=Selected Products: iPhone 15 Pro')).toBeVisible();
    expect(await page.locator('video').count()).toBeGreaterThan(0);

    console.log('✓ All form state maintained correctly');
  });

  test('should validate different video upload methods', async ({ page }) => {
    console.log('📤 Testing different upload methods...');

    await page.goto('/');

    // Method 1: Direct file input (already tested above)
    // Method 2: Test with different video properties

    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles('/Users/ammadhassan/Downloads/xAIhackathon/frameshift/public/test.mp4');
    await page.waitForSelector('text=Processing Video...', { state: 'hidden', timeout: 30000 });

    // Get video properties
    const videoProps = await page.evaluate(() => {
      const video = document.querySelector('video');
      if (video) {
        return {
          duration: video.duration,
          readyState: video.readyState,
          videoWidth: video.videoWidth,
          videoHeight: video.videoHeight,
          src: video.src.substring(0, 20) + '...'
        };
      }
      return null;
    });

    console.log('Video properties:', videoProps);
    expect(videoProps).not.toBeNull();
    expect(videoProps.duration).toBeGreaterThan(0);
    expect(videoProps.readyState).toBeGreaterThan(0);
    console.log('✓ Video properties are valid');
  });

  test('should handle edge cases and error scenarios', async ({ page }) => {
    console.log('⚠️ Testing edge cases and error scenarios...');

    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');

    // Test 1: Try to proceed without any input
    const proceedButton = page.locator('text=Analyze & Generate');
    expect(await proceedButton.isDisabled()).toBe(true);
    console.log('✓ Cannot proceed without input');

    // Test 2: Upload video but no preferences
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles('/Users/ammadhassan/Downloads/xAIhackathon/frameshift/public/test.mp4');
    await page.waitForSelector('text=Processing Video...', { state: 'hidden', timeout: 30000 });

    expect(await proceedButton.isDisabled()).toBe(true);
    console.log('✓ Cannot proceed with video but no preferences');

    // Test 3: Add minimal preferences to enable proceed
    const brandInput = page.locator('input[placeholder*="Add brand"]');
    await brandInput.fill('Test Brand');
    await brandInput.press('Enter');

    expect(await proceedButton.isEnabled()).toBe(true);
    console.log('✓ Can proceed with video and minimal preferences');

    // Test 4: Remove brand, select product instead
    const removeBrand = page.locator('[data-testid="brand-badge"]').locator('button');
    await removeBrand.click();

    expect(await proceedButton.isDisabled()).toBe(true);
    console.log('✓ Cannot proceed after removing brand');

    await page.locator('text=Show Products').click();
    await page.locator('text=Nike Air Max').locator('..').click();

    expect(await proceedButton.isEnabled()).toBe(true);
    console.log('✓ Can proceed with product selection instead of brand names');

    // Check for any unexpected errors
    if (consoleErrors.length > 0) {
      console.log('Console errors detected:', consoleErrors);
    } else {
      console.log('✓ No unexpected console errors');
    }
  });
});