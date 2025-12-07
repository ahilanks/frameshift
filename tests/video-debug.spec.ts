import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Video Loading Debug Tests', () => {
  test('should detect video loading errors with detailed monitoring', async ({ page }) => {
    const consoleMessages = [];
    const errors = [];
    const warnings = [];

    // Listen for all console events
    page.on('console', msg => {
      const message = {
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      };
      consoleMessages.push(message);

      if (msg.type() === 'error') {
        errors.push(message);
      } else if (msg.type() === 'warning') {
        warnings.push(message);
      }
    });

    // Listen for unhandled errors
    page.on('pageerror', err => {
      errors.push({
        type: 'pageerror',
        text: err.message,
        stack: err.stack
      });
    });

    // Navigate to the page
    await page.goto('/');

    console.log('Page loaded, starting video upload test...');

    // Test various video upload scenarios
    const testVideoPath = '/Users/ammadhassan/Downloads/xAIhackathon/frameshift/public/test.mp4';

    // Method 1: Direct file input
    try {
      const fileInput = page.locator('input[type="file"]').first();
      await fileInput.setInputFiles(testVideoPath);
      console.log('File uploaded via direct input');

      // Wait for processing
      await page.waitForSelector('text=Processing Video...', { timeout: 5000 });
      console.log('Processing started');

      await page.waitForSelector('text=Processing Video...', { state: 'hidden', timeout: 30000 });
      console.log('Processing completed');

      // Check if video element exists
      const videoElement = page.locator('video');
      if (await videoElement.count() > 0) {
        console.log('Video element found');

        // Try to get video properties
        const videoProps = await page.evaluate(() => {
          const video = document.querySelector('video');
          if (video) {
            return {
              src: video.src,
              duration: video.duration,
              readyState: video.readyState,
              networkState: video.networkState,
              error: video.error ? {
                code: video.error.code,
                message: video.error.message
              } : null
            };
          }
          return null;
        });

        console.log('Video properties:', videoProps);
      }

    } catch (error) {
      console.log('Error during video upload test:', error.message);
    }

    // Wait a bit more to catch any delayed errors
    await page.waitForTimeout(3000);

    // Log all findings
    console.log('\n=== CONSOLE MESSAGES ===');
    consoleMessages.forEach((msg, index) => {
      console.log(`${index + 1}. [${msg.type}] ${msg.text}`);
      if (msg.location) {
        console.log(`   Location: ${msg.location.url}:${msg.location.lineNumber}`);
      }
    });

    console.log('\n=== ERRORS ===');
    errors.forEach((error, index) => {
      console.log(`${index + 1}. [${error.type}] ${error.text}`);
      if (error.stack) {
        console.log(`   Stack: ${error.stack}`);
      }
    });

    console.log('\n=== WARNINGS ===');
    warnings.forEach((warning, index) => {
      console.log(`${index + 1}. ${warning.text}`);
    });

    // Check for specific video-related errors
    const videoErrors = [...errors, ...warnings].filter(msg =>
      msg.text.toLowerCase().includes('video') ||
      msg.text.toLowerCase().includes('metadata') ||
      msg.text.toLowerCase().includes('loading') ||
      msg.text.includes('Video loading error') ||
      msg.text.includes('{}')
    );

    console.log('\n=== VIDEO-RELATED ISSUES ===');
    videoErrors.forEach((error, index) => {
      console.log(`${index + 1}. [${error.type}] ${error.text}`);
    });

    if (videoErrors.length === 0) {
      console.log('No video-related errors detected in this test run');
    }

    // Final check of the DOM state
    const domState = await page.evaluate(() => {
      return {
        videoElements: document.querySelectorAll('video').length,
        fileInputs: document.querySelectorAll('input[type="file"]').length,
        processingIndicators: document.querySelectorAll('text=Processing Video...').length,
        videoDropzones: document.querySelectorAll('[data-testid="video-dropzone"]').length
      };
    });

    console.log('\n=== FINAL DOM STATE ===');
    console.log(domState);
  });

  test('should test video metadata extraction directly', async ({ page }) => {
    await page.goto('/');

    // Inject test code to simulate the video loading process
    const testResult = await page.evaluate(async () => {
      try {
        // Create test file (simulate what happens in the component)
        const response = await fetch('/test.mp4');
        const blob = await response.blob();
        const file = new File([blob], 'test.mp4', { type: 'video/mp4' });

        // Simulate the video metadata extraction logic from the component
        const video = document.createElement('video');
        video.preload = 'metadata';
        video.muted = true;

        const duration = await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('Video metadata loading timeout'));
          }, 10000);

          video.onloadedmetadata = () => {
            clearTimeout(timeout);
            const videoDuration = video.duration;
            URL.revokeObjectURL(video.src);
            video.remove();
            if (isNaN(videoDuration) || videoDuration === 0) {
              resolve(30); // Default fallback duration
            } else {
              resolve(videoDuration);
            }
          };

          video.onerror = (error) => {
            clearTimeout(timeout);
            URL.revokeObjectURL(video.src);
            video.remove();
            console.error('Video loading error:', error);
            resolve(30); // Fallback duration
          };

          video.src = URL.createObjectURL(file);
        });

        return {
          success: true,
          duration: duration,
          message: 'Video metadata extracted successfully'
        };
      } catch (error) {
        return {
          success: false,
          error: error.message,
          message: 'Video metadata extraction failed'
        };
      }
    });

    console.log('Direct video metadata test result:', testResult);

    if (!testResult.success) {
      console.log('ERROR: Video metadata extraction failed');
      console.log('Error message:', testResult.error);
    } else {
      console.log('SUCCESS: Video metadata extracted');
      console.log('Duration:', testResult.duration);
    }
  });

  test('should test different video file scenarios', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');

    // Test with the actual video file
    console.log('Testing with real video file...');

    // Test the onDrop function directly
    const dropTestResult = await page.evaluate(() => {
      // Access the video dropzone component's onDrop function
      const dropzone = document.querySelector('[data-testid="video-dropzone"]');

      if (!dropzone) {
        return { error: 'Dropzone not found' };
      }

      // Simulate what happens in the actual onDrop function
      return new Promise(async (resolve) => {
        try {
          // Fetch the test video
          const response = await fetch('/test.mp4');
          const blob = await response.blob();
          const file = new File([blob], 'test.mp4', { type: 'video/mp4' });

          // Create video element to get duration and frame count
          const video = document.createElement('video');
          video.preload = 'metadata';
          video.muted = true;

          const duration = await new Promise((resolveDuration, rejectDuration) => {
            const timeout = setTimeout(() => {
              rejectDuration(new Error('Video metadata loading timeout'));
            }, 10000);

            video.onloadedmetadata = () => {
              clearTimeout(timeout);
              const videoDuration = video.duration;
              URL.revokeObjectURL(video.src);
              video.remove();
              if (isNaN(videoDuration) || videoDuration === 0) {
                resolveDuration(30); // Default fallback duration
              } else {
                resolveDuration(videoDuration);
              }
            };

            video.onerror = (error) => {
              clearTimeout(timeout);
              URL.revokeObjectURL(video.src);
              video.remove();
              console.error('Video loading error:', error);
              resolveDuration(30); // Fallback duration
            };

            video.src = URL.createObjectURL(file);
          });

          resolve({
            success: true,
            duration: duration,
            fileSize: file.size,
            fileName: file.name,
            fileType: file.type
          });
        } catch (error) {
          resolve({
            success: false,
            error: error.message
          });
        }
      });
    });

    console.log('Drop test result:', dropTestResult);

    if (errors.length > 0) {
      console.log('Console errors detected:');
      errors.forEach((error, index) => {
        console.log(`${index + 1}. ${error}`);
      });
    }
  });
});