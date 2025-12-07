import { test, expect } from '@playwright/test';

test.describe('Video Loading Error Reproduction', () => {
  test('should reproduce the video loading error with invalid file', async ({ page }) => {
    const consoleErrors = [];

    // Listen for console errors specifically
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`Console error: ${msg.text()}`);
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');

    // Try to trigger the video onerror event by creating an invalid video file
    const errorTestResult = await page.evaluate(async () => {
      try {
        // Create an invalid video file (corrupt/empty)
        const invalidVideoData = new Uint8Array([0, 0, 0, 0]); // Invalid video data
        const invalidFile = new File([invalidVideoData], 'corrupt.mp4', { type: 'video/mp4' });

        // Simulate the video loading process that would trigger the error
        const video = document.createElement('video');
        video.preload = 'metadata';
        video.muted = true;

        return new Promise((resolve) => {
          const timeout = setTimeout(() => {
            resolve({ result: 'timeout', error: 'No error triggered within timeout' });
          }, 5000);

          video.onloadedmetadata = () => {
            clearTimeout(timeout);
            resolve({ result: 'success', duration: video.duration });
          };

          video.onerror = (error) => {
            clearTimeout(timeout);

            // This is the problematic line from the component
            console.error('Video loading error:', error);

            resolve({
              result: 'error',
              errorType: typeof error,
              errorConstructor: error.constructor.name,
              errorMessage: error.message || 'No message property',
              errorToString: error.toString(),
              errorKeys: Object.keys(error),
              // Try to extract meaningful information
              errorTarget: error.target ? error.target.tagName : 'No target',
              errorEventType: error.type || 'No type'
            });
          };

          video.src = URL.createObjectURL(invalidFile);
        });
      } catch (e) {
        return { result: 'exception', error: e.message };
      }
    });

    console.log('Error reproduction result:', errorTestResult);

    // Check if we captured the problematic console.error
    const videoErrorLogs = consoleErrors.filter(error =>
      error.includes('Video loading error:')
    );

    if (videoErrorLogs.length > 0) {
      console.log('SUCCESS: Reproduced the video loading error!');
      console.log('Error logs:', videoErrorLogs);
    } else {
      console.log('No video loading errors captured in this test run');
    }

    // Verify the error result
    if (errorTestResult.result === 'error') {
      console.log('ERROR DETAILS:');
      console.log('- Error Type:', errorTestResult.errorType);
      console.log('- Error Constructor:', errorTestResult.errorConstructor);
      console.log('- Error Message:', errorTestResult.errorMessage);
      console.log('- Error toString():', errorTestResult.errorToString);
      console.log('- Error Keys:', errorTestResult.errorKeys);
      console.log('- Error Target:', errorTestResult.errorTarget);
      console.log('- Error Event Type:', errorTestResult.errorEventType);
    }
  });

  test('should test improved error logging approach', async ({ page }) => {
    await page.goto('/');

    const improvedLoggingResult = await page.evaluate(async () => {
      try {
        // Create an invalid video file
        const invalidVideoData = new Uint8Array([0, 0, 0, 0]);
        const invalidFile = new File([invalidVideoData], 'corrupt.mp4', { type: 'video/mp4' });

        const video = document.createElement('video');
        video.preload = 'metadata';
        video.muted = true;

        return new Promise((resolve) => {
          const timeout = setTimeout(() => {
            resolve({ result: 'timeout' });
          }, 5000);

          video.onloadedmetadata = () => {
            clearTimeout(timeout);
            resolve({ result: 'success', duration: video.duration });
          };

          video.onerror = (error) => {
            clearTimeout(timeout);

            // IMPROVED ERROR LOGGING (the fix we'll implement)
            console.error('Video loading error details:', {
              errorType: error.type,
              target: error.target?.tagName,
              message: error.message || 'No message available',
              code: error.target?.error?.code,
              networkState: error.target?.networkState,
              readyState: error.target?.readyState,
              src: error.target?.src?.substring(0, 100) + '...',
              fileSize: invalidFile.size,
              fileName: invalidFile.name,
              fileType: invalidFile.type
            });

            resolve({
              result: 'improved_error_logged',
              details: 'Improved error logging implemented'
            });
          };

          video.src = URL.createObjectURL(invalidFile);
        });
      } catch (e) {
        return { result: 'exception', error: e.message };
      }
    });

    console.log('Improved logging result:', improvedLoggingResult);
  });

  test('should test various video error scenarios', async ({ page }) => {
    const allErrors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        allErrors.push(msg.text());
      }
    });

    await page.goto('/');

    const errorScenarios = await page.evaluate(async () => {
      const scenarios = [
        {
          name: 'Empty file',
          data: new Uint8Array([]),
          filename: 'empty.mp4'
        },
        {
          name: 'Invalid header',
          data: new Uint8Array([0xFF, 0xFF, 0xFF, 0xFF]),
          filename: 'invalid.mp4'
        },
        {
          name: 'Non-video file as video',
          data: new TextEncoder().encode('This is not a video file'),
          filename: 'fake.mp4'
        }
      ];

      const results = [];

      for (const scenario of scenarios) {
        try {
          const file = new File([scenario.data], scenario.filename, { type: 'video/mp4' });
          const video = document.createElement('video');
          video.preload = 'metadata';
          video.muted = true;

          const result = await new Promise((resolve) => {
            const timeout = setTimeout(() => {
              resolve({ scenario: scenario.name, result: 'timeout' });
            }, 3000);

            video.onloadedmetadata = () => {
              clearTimeout(timeout);
              resolve({ scenario: scenario.name, result: 'success', duration: video.duration });
            };

            video.onerror = (error) => {
              clearTimeout(timeout);
              resolve({
                scenario: scenario.name,
                result: 'error',
                errorInfo: {
                  type: error.type,
                  target: error.target?.tagName,
                  errorCode: error.target?.error?.code,
                  networkState: error.target?.networkState,
                  readyState: error.target?.readyState
                }
              });
            };

            video.src = URL.createObjectURL(file);
          });

          results.push(result);
        } catch (e) {
          results.push({ scenario: scenario.name, result: 'exception', error: e.message });
        }
      }

      return results;
    });

    console.log('Error scenario results:');
    errorScenarios.forEach((result, index) => {
      console.log(`${index + 1}. ${result.scenario}: ${result.result}`);
      if (result.errorInfo) {
        console.log(`   Error details:`, result.errorInfo);
      }
    });

    console.log('Total console errors captured:', allErrors.length);
    allErrors.forEach((error, index) => {
      console.log(`${index + 1}. ${error}`);
    });
  });
});