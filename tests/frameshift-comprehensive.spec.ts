import { test, expect, Page } from '@playwright/test';
import path from 'path';

// Test utilities
const testVideoPath = path.join(process.cwd(), 'public', 'test.mp4');
const testImagePath = path.join(process.cwd(), 'public', 'globe.svg');

class FrameshiftPage {
  constructor(private page: Page) {}

  // Navigation
  async goto() {
    await this.page.goto('/');
  }

  // Video Upload Section
  async uploadVideo(filePath: string) {
    const fileChooserPromise = this.page.waitForEvent('filechooser');
    await this.page.locator('input[type="file"]').first().click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(filePath);
  }

  async dragAndDropVideo(filePath: string) {
    const dropZone = this.page.locator('[data-testid="video-dropzone"]').first();

    // Create file data transfer
    const buffer = require('fs').readFileSync(filePath);
    const dataTransfer = await this.page.evaluateHandle((buffer) => {
      const dt = new DataTransfer();
      const file = new File([new Uint8Array(buffer)], 'test.mp4', { type: 'video/mp4' });
      dt.items.add(file);
      return dt;
    }, Array.from(buffer));

    await dropZone.dispatchEvent('drop', { dataTransfer });
  }

  async waitForVideoProcessing() {
    await this.page.waitForSelector('text=Processing Video...', { state: 'hidden', timeout: 30000 });
  }

  async isVideoUploaded() {
    return await this.page.locator('video').count() > 0;
  }

  // Video Preview Controls
  async clickPlayPause() {
    await this.page.locator('[data-testid="play-pause-btn"]').click();
  }

  async clickFrameStep(direction: 'forward' | 'backward') {
    const selector = direction === 'forward'
      ? '[data-testid="frame-step-forward"]'
      : '[data-testid="frame-step-backward"]';
    await this.page.locator(selector).click();
  }

  async seekToTime(time: number) {
    const progressBar = this.page.locator('input[type="range"]').first();
    await progressBar.fill(time.toString());
  }

  async removeVideo() {
    await this.page.locator('[data-testid="remove-video-btn"]').click();
  }

  async getVideoCurrentTime() {
    return await this.page.evaluate(() => {
      const video = document.querySelector('video');
      return video?.currentTime || 0;
    });
  }

  async getVideoDuration() {
    return await this.page.evaluate(() => {
      const video = document.querySelector('video');
      return video?.duration || 0;
    });
  }

  // Brand Preferences
  async addBrandName(brandName: string) {
    await this.page.locator('input[placeholder*="Add brand"]').fill(brandName);
    await this.page.locator('input[placeholder*="Add brand"]').press('Enter');
  }

  async removeBrandName(brandName: string) {
    await this.page.locator(`text=${brandName}`).locator('..').locator('button').click();
  }

  async getBrandNames() {
    return await this.page.locator('[data-testid="brand-badge"]').allTextContents();
  }

  // Brand Image Upload
  async uploadBrandImage(filePath: string) {
    const fileChooserPromise = this.page.waitForEvent('filechooser');
    await this.page.locator('[data-testid="brand-image-dropzone"] input').click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(filePath);
  }

  async dragAndDropBrandImage(filePath: string) {
    const dropZone = this.page.locator('[data-testid="brand-image-dropzone"]');

    // Read file for drag and drop
    const buffer = require('fs').readFileSync(filePath);
    const fileName = path.basename(filePath);
    const mimeType = fileName.endsWith('.svg') ? 'image/svg+xml' : 'image/png';

    const dataTransfer = await this.page.evaluateHandle(({ buffer, fileName, mimeType }) => {
      const dt = new DataTransfer();
      const file = new File([new Uint8Array(buffer)], fileName, { type: mimeType });
      dt.items.add(file);
      return dt;
    }, { buffer: Array.from(buffer), fileName, mimeType });

    await dropZone.dispatchEvent('drop', { dataTransfer });
  }

  async isBrandImageUploaded() {
    return await this.page.locator('[data-testid="uploaded-brand-image"]').count() > 0;
  }

  async removeBrandImage() {
    await this.page.locator('[data-testid="remove-brand-image-btn"]').click();
  }

  // Product Selection
  async showProductSelector() {
    const button = this.page.locator('text=Show Products');
    if (await button.count() > 0) {
      await button.click();
    }
  }

  async hideProductSelector() {
    const button = this.page.locator('text=Hide Products');
    if (await button.count() > 0) {
      await button.click();
    }
  }

  async selectProduct(productName: string) {
    await this.page.locator(`text=${productName}`).locator('..').click();
  }

  async getSelectedProducts() {
    return await this.page.locator('[data-testid="selected-product"]').allTextContents();
  }

  // Target Audience
  async addAudience(audience: string) {
    await this.page.locator('input[placeholder*="Add audience"]').fill(audience);
    await this.page.locator('input[placeholder*="Add audience"]').press('Enter');
  }

  async removeAudience(audience: string) {
    await this.page.locator(`text=${audience}`).locator('..').locator('button').click();
  }

  async getAudiences() {
    return await this.page.locator('[data-testid="audience-badge"]').allTextContents();
  }

  // Submit/Proceed
  async canProceed() {
    return await this.page.locator('text=Analyze & Generate').isEnabled();
  }

  async proceed() {
    await this.page.locator('text=Analyze & Generate').click();
  }

  // Error checking
  async hasVideoLoadingError() {
    const consoleErrors = [];
    this.page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().includes('Video loading error')) {
        consoleErrors.push(msg.text());
      }
    });
    return consoleErrors.length > 0;
  }

  async getConsoleErrors() {
    const errors = [];
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    return errors;
  }
}

test.describe('Frameshift Application E2E Tests', () => {
  let frameshiftPage: FrameshiftPage;

  test.beforeEach(async ({ page }) => {
    frameshiftPage = new FrameshiftPage(page);
    await frameshiftPage.goto();
  });

  test.describe('Video Upload Functionality', () => {
    test('should display video dropzone on page load', async ({ page }) => {
      await expect(page.locator('text=Upload Video')).toBeVisible();
      await expect(page.locator('text=Drop a video file here, or click to select')).toBeVisible();
    });

    test('should upload video via file input', async ({ page }) => {
      // Monitor console for errors
      const consoleMessages = [];
      page.on('console', msg => consoleMessages.push(msg));

      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();

      expect(await frameshiftPage.isVideoUploaded()).toBe(true);

      // Check for video loading errors
      const videoLoadingErrors = consoleMessages.filter(msg =>
        msg.type() === 'error' && msg.text().includes('Video loading error')
      );

      if (videoLoadingErrors.length > 0) {
        console.log('Video loading errors detected:', videoLoadingErrors.map(m => m.text()));
      }
    });

    test('should show processing state during video upload', async ({ page }) => {
      await frameshiftPage.uploadVideo(testVideoPath);
      await expect(page.locator('text=Processing Video...')).toBeVisible();
      await frameshiftPage.waitForVideoProcessing();
    });

    test('should display video metadata after upload', async ({ page }) => {
      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();

      await expect(page.locator('text=test.mp4')).toBeVisible();
      await expect(page.locator('text=Duration')).toBeVisible();
      await expect(page.locator('text=File Size')).toBeVisible();
    });

    test('should remove video when remove button is clicked', async ({ page }) => {
      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();

      await frameshiftPage.removeVideo();
      expect(await frameshiftPage.isVideoUploaded()).toBe(false);
    });
  });

  test.describe('Video Preview and Frame Scrubbing', () => {
    test.beforeEach(async () => {
      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();
    });

    test('should display video preview with controls', async ({ page }) => {
      await expect(page.locator('video')).toBeVisible();
      await expect(page.locator('[data-testid="play-pause-btn"]')).toBeVisible();
      await expect(page.locator('[data-testid="frame-step-forward"]')).toBeVisible();
      await expect(page.locator('[data-testid="frame-step-backward"]')).toBeVisible();
    });

    test('should play and pause video', async ({ page }) => {
      const initialTime = await frameshiftPage.getVideoCurrentTime();

      await frameshiftPage.clickPlayPause();
      await page.waitForTimeout(1000); // Let video play for 1 second

      const timeAfterPlay = await frameshiftPage.getVideoCurrentTime();
      expect(timeAfterPlay).toBeGreaterThan(initialTime);

      await frameshiftPage.clickPlayPause();
      await page.waitForTimeout(500);

      const timeAfterPause = await frameshiftPage.getVideoCurrentTime();
      expect(Math.abs(timeAfterPause - timeAfterPlay)).toBeLessThan(0.1);
    });

    test('should step frames forward and backward', async ({ page }) => {
      const initialTime = await frameshiftPage.getVideoCurrentTime();

      await frameshiftPage.clickFrameStep('forward');
      const timeAfterForward = await frameshiftPage.getVideoCurrentTime();
      expect(timeAfterForward).toBeGreaterThan(initialTime);

      await frameshiftPage.clickFrameStep('backward');
      const timeAfterBackward = await frameshiftPage.getVideoCurrentTime();
      expect(timeAfterBackward).toBeLessThan(timeAfterForward);
    });

    test('should seek to specific time', async () => {
      const duration = await frameshiftPage.getVideoDuration();
      const targetTime = duration / 2;

      await frameshiftPage.seekToTime(targetTime);
      const currentTime = await frameshiftPage.getVideoCurrentTime();
      expect(Math.abs(currentTime - targetTime)).toBeLessThan(1);
    });

    test('should display current frame and total frame information', async ({ page }) => {
      await expect(page.locator('text=Current Frame:')).toBeVisible();
      await expect(page.locator('text=Total Frames:')).toBeVisible();
      await expect(page.locator('text=Frame Rate:')).toBeVisible();
    });
  });

  test.describe('Brand Preferences', () => {
    test('should add and display brand names', async ({ page }) => {
      await frameshiftPage.addBrandName('Apple');
      await frameshiftPage.addBrandName('Nike');

      const brandNames = await frameshiftPage.getBrandNames();
      expect(brandNames).toContain('Apple');
      expect(brandNames).toContain('Nike');
    });

    test('should remove brand names', async ({ page }) => {
      await frameshiftPage.addBrandName('Tesla');
      await frameshiftPage.removeBrandName('Tesla');

      const brandNames = await frameshiftPage.getBrandNames();
      expect(brandNames).not.toContain('Tesla');
    });

    test('should prevent duplicate brand names', async ({ page }) => {
      await frameshiftPage.addBrandName('Microsoft');
      await frameshiftPage.addBrandName('Microsoft');

      const microsoftBadges = await page.locator('text=Microsoft').count();
      expect(microsoftBadges).toBe(1);
    });
  });

  test.describe('Brand Image Upload', () => {
    test('should upload brand image via file input', async ({ page }) => {
      await frameshiftPage.uploadBrandImage(testImagePath);
      expect(await frameshiftPage.isBrandImageUploaded()).toBe(true);
    });

    test('should display uploaded brand image', async ({ page }) => {
      await frameshiftPage.uploadBrandImage(testImagePath);
      await expect(page.locator('[data-testid="uploaded-brand-image"] img')).toBeVisible();
      await expect(page.locator('text=Brand reference image uploaded')).toBeVisible();
    });

    test('should remove brand image', async ({ page }) => {
      await frameshiftPage.uploadBrandImage(testImagePath);
      await frameshiftPage.removeBrandImage();
      expect(await frameshiftPage.isBrandImageUploaded()).toBe(false);
    });

    test('should show upload dropzone when no image', async ({ page }) => {
      await expect(page.locator('text=Upload brand image')).toBeVisible();
      await expect(page.locator('text=PNG, JPG up to 10MB')).toBeVisible();
    });
  });

  test.describe('Product Selection', () => {
    test('should show and hide product selector', async ({ page }) => {
      await frameshiftPage.showProductSelector();
      await expect(page.locator('text=iPhone 15 Pro')).toBeVisible();

      await frameshiftPage.hideProductSelector();
      await expect(page.locator('text=iPhone 15 Pro')).not.toBeVisible();
    });

    test('should select and deselect products', async ({ page }) => {
      await frameshiftPage.showProductSelector();

      await frameshiftPage.selectProduct('iPhone 15 Pro');
      await expect(page.locator('text=Selected Products: iPhone 15 Pro')).toBeVisible();

      await frameshiftPage.selectProduct('iPhone 15 Pro'); // Deselect
      await expect(page.locator('text=Selected Products:')).not.toBeVisible();
    });

    test('should display product information', async ({ page }) => {
      await frameshiftPage.showProductSelector();

      await expect(page.locator('text=iPhone 15 Pro')).toBeVisible();
      await expect(page.locator('text=Latest flagship smartphone')).toBeVisible();
      await expect(page.locator('text=Technology')).toBeVisible();
    });

    test('should select multiple products', async ({ page }) => {
      await frameshiftPage.showProductSelector();

      await frameshiftPage.selectProduct('iPhone 15 Pro');
      await frameshiftPage.selectProduct('Nike Air Max');

      await expect(page.locator('text=Selected Products: iPhone 15 Pro, Nike Air Max')).toBeVisible();
    });
  });

  test.describe('Target Audience', () => {
    test('should add and display target audiences', async ({ page }) => {
      await frameshiftPage.addAudience('Young professionals');
      await frameshiftPage.addAudience('Tech enthusiasts');

      const audiences = await frameshiftPage.getAudiences();
      expect(audiences).toContain('Young professionals');
      expect(audiences).toContain('Tech enthusiasts');
    });

    test('should remove target audiences', async ({ page }) => {
      await frameshiftPage.addAudience('Gamers');
      await frameshiftPage.removeAudience('Gamers');

      const audiences = await frameshiftPage.getAudiences();
      expect(audiences).not.toContain('Gamers');
    });
  });

  test.describe('Form Validation and Submission', () => {
    test('should enable proceed button when video and preferences are set', async ({ page }) => {
      expect(await frameshiftPage.canProceed()).toBe(false);

      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();
      expect(await frameshiftPage.canProceed()).toBe(false);

      await frameshiftPage.addBrandName('Apple');
      expect(await frameshiftPage.canProceed()).toBe(true);
    });

    test('should enable proceed button with selected products instead of brand names', async ({ page }) => {
      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();

      await frameshiftPage.showProductSelector();
      await frameshiftPage.selectProduct('Tesla Model 3');

      expect(await frameshiftPage.canProceed()).toBe(true);
    });

    test('should display configuration summary', async ({ page }) => {
      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();
      await frameshiftPage.addBrandName('Google');
      await frameshiftPage.addAudience('Developers');

      await expect(page.locator('text=Configuration Summary')).toBeVisible();
      await expect(page.locator('text=Brand Names:')).toBeVisible();
      await expect(page.locator('text=Target Audience:')).toBeVisible();
    });

    test('should navigate to analysis page when proceeding', async ({ page }) => {
      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();
      await frameshiftPage.addBrandName('Amazon');

      await frameshiftPage.proceed();
      await page.waitForURL('**/analysis');
      expect(page.url()).toContain('/analysis');
    });
  });

  test.describe('Error Handling and Edge Cases', () => {
    test('should handle video loading errors gracefully', async ({ page }) => {
      // Monitor console for video loading errors
      const consoleErrors = [];
      page.on('console', msg => {
        if (msg.type() === 'error' && msg.text().includes('Video loading error')) {
          consoleErrors.push(msg.text());
        }
      });

      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();

      // If errors occurred, they should be logged but not break the UI
      if (consoleErrors.length > 0) {
        console.log('Video loading errors detected (this is what we\'re debugging):', consoleErrors);

        // The UI should still function despite the error
        expect(await frameshiftPage.isVideoUploaded()).toBe(true);
      }
    });

    test('should handle empty form submission', async ({ page }) => {
      expect(await frameshiftPage.canProceed()).toBe(false);

      // Button should be disabled
      await expect(page.locator('text=Analyze & Generate')).toBeDisabled();
    });

    test('should handle video removal and re-upload', async ({ page }) => {
      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();
      await frameshiftPage.removeVideo();

      await frameshiftPage.uploadVideo(testVideoPath);
      await frameshiftPage.waitForVideoProcessing();

      expect(await frameshiftPage.isVideoUploaded()).toBe(true);
    });

    test('should handle large file warnings', async ({ page }) => {
      // The UI should show appropriate file size limits
      await expect(page.locator('text=max 100MB')).toBeVisible();
      await expect(page.locator('text=up to 10MB')).toBeVisible();
    });
  });

  test.describe('Accessibility and UX', () => {
    test('should have proper headings and structure', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('AI-Powered Product Placement');
      await expect(page.locator('text=Upload Video')).toBeVisible();
      await expect(page.locator('text=Brand Preferences')).toBeVisible();
    });

    test('should show loading states appropriately', async ({ page }) => {
      await frameshiftPage.uploadVideo(testVideoPath);

      // Should show processing indicator
      await expect(page.locator('text=Processing Video...')).toBeVisible();
      await expect(page.locator('.animate-spin')).toBeVisible();

      await frameshiftPage.waitForVideoProcessing();

      // Processing indicator should disappear
      await expect(page.locator('text=Processing Video...')).not.toBeVisible();
    });

    test('should provide helpful instructions', async ({ page }) => {
      await expect(page.locator('text=How it works:')).toBeVisible();
      await expect(page.locator('text=Upload your video')).toBeVisible();
      await expect(page.locator('text=Grok AI analyzes scene context')).toBeVisible();
    });
  });
});