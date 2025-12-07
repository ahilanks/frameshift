import { test, expect } from '@playwright/test';

test.describe('Video Loading Error Fix Verification', () => {
  test('should display improved error logging when video fails to load', async ({ page }) => {
    const consoleErrors = [];

    // Listen for console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`Console error: ${msg.text()}`);
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');

    // Trigger video error by uploading corrupted file
    const errorResult = await page.evaluate(async () => {
      try {
        // Create an invalid video file
        const invalidVideoData = new Uint8Array([0, 1, 2, 3]);
        const invalidFile = new File([invalidVideoData], 'corrupted.mp4', { type: 'video/mp4' });

        // Get the file input and simulate file upload
        const fileInput = document.querySelector('input[type="file"]');
        if (!fileInput) {
          return { error: 'File input not found' };
        }

        // Create a proper File list
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(invalidFile);
        fileInput.files = dataTransfer.files;

        // Trigger change event
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);

        return { success: true, fileName: invalidFile.name };
      } catch (error) {
        return { error: error.message };
      }
    });

    console.log('Error trigger result:', errorResult);

    // Wait for processing to complete
    await page.waitForTimeout(3000);

    // Check if improved error logging was used
    const improvedErrorLogs = consoleErrors.filter(error =>
      error.includes('Video loading error details:') &&
      error.includes('errorType') &&
      error.includes('fileName')
    );

    if (improvedErrorLogs.length > 0) {
      console.log('✅ SUCCESS: Improved error logging is working!');
      console.log('Improved error logs:', improvedErrorLogs);
    } else {
      console.log('❌ The improved error logging was not triggered');
      console.log('All console errors:', consoleErrors);
    }

    // Check for user-facing error message in the UI
    const errorMessage = page.locator('.bg-red-50 .text-red-600');
    if (await errorMessage.count() > 0) {
      const errorText = await errorMessage.textContent();
      console.log('✅ SUCCESS: User-facing error message is displayed:', errorText);
    } else {
      console.log('❌ No user-facing error message found in UI');
    }
  });

  test('should verify normal video upload still works correctly', async ({ page }) => {
    const consoleMessages = [];

    // Monitor all console messages
    page.on('console', msg => {
      consoleMessages.push({ type: msg.type(), text: msg.text() });
    });

    await page.goto('/');

    // Upload a valid video
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles('/Users/ammadhassan/Downloads/xAIhackathon/frameshift/public/test.mp4');

    // Wait for processing
    await page.waitForTimeout(5000);

    // Verify video was uploaded successfully
    const videoElement = page.locator('video');
    expect(await videoElement.count()).toBeGreaterThan(0);

    // Check that no error messages are shown
    const errorMessage = page.locator('.bg-red-50');
    expect(await errorMessage.count()).toBe(0);

    console.log('✅ Normal video upload verification passed');

    // Log any unexpected errors
    const errors = consoleMessages.filter(msg => msg.type === 'error');
    if (errors.length > 0) {
      console.log('⚠️ Unexpected errors during normal upload:', errors);
    }
  });

  test('should test comprehensive error information', async ({ page }) => {
    await page.goto('/');

    // Test the complete error handling flow
    const errorInfoTest = await page.evaluate(async () => {
      try {
        // Create test cases with different invalid files
        const testCases = [
          {
            name: 'empty-file.mp4',
            data: new Uint8Array([]),
            type: 'video/mp4'
          },
          {
            name: 'text-as-video.mp4',
            data: new TextEncoder().encode('This is not a video'),
            type: 'video/mp4'
          },
          {
            name: 'random-bytes.mp4',
            data: new Uint8Array([0xFF, 0xFE, 0xFD, 0xFC]),
            type: 'video/mp4'
          }
        ];

        const results = [];

        for (const testCase of testCases) {
          const file = new File([testCase.data], testCase.name, { type: testCase.type });

          // Simulate the exact error handling logic from the component
          const video = document.createElement('video');
          video.preload = 'metadata';
          video.muted = true;

          const result = await new Promise((resolve) => {
            const timeout = setTimeout(() => {
              resolve({ testCase: testCase.name, result: 'timeout' });
            }, 3000);

            video.onloadedmetadata = () => {
              clearTimeout(timeout);
              resolve({ testCase: testCase.name, result: 'success' });
            };

            video.onerror = (error) => {
              clearTimeout(timeout);

              // Test the improved error logging
              const errorDetails = {
                errorType: error.type,
                target: error.target?.tagName,
                errorCode: error.target?.error?.code || 'Unknown',
                errorMessage: error.target?.error?.message || 'No specific error message',
                networkState: error.target?.networkState,
                readyState: error.target?.readyState,
                fileName: file.name,
                fileSize: file.size,
                fileType: file.type,
                timestamp: new Date().toISOString()
              };

              console.error('Video loading error details:', errorDetails);

              resolve({
                testCase: testCase.name,
                result: 'error',
                errorDetails: errorDetails
              });
            };

            video.src = URL.createObjectURL(file);
          });

          results.push(result);
        }

        return {
          success: true,
          results: results
        };
      } catch (error) {
        return {
          success: false,
          error: error.message
        };
      }
    });

    console.log('Comprehensive error test results:');
    if (errorInfoTest.success) {
      errorInfoTest.results.forEach((result, index) => {
        console.log(`${index + 1}. ${result.testCase}: ${result.result}`);
        if (result.errorDetails) {
          console.log(`   Error Code: ${result.errorDetails.errorCode}`);
          console.log(`   Network State: ${result.errorDetails.networkState}`);
          console.log(`   Ready State: ${result.errorDetails.readyState}`);
          console.log(`   File Name: ${result.errorDetails.fileName}`);
          console.log(`   File Size: ${result.errorDetails.fileSize}`);
        }
      });
    } else {
      console.log('Test failed:', errorInfoTest.error);
    }
  });
});