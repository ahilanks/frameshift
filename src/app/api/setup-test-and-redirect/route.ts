import { NextRequest, NextResponse } from 'next/server';

export async function GET() {
  // Return an HTML page that sets up sessionStorage and redirects
  const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Setting up Veo 3.1 Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #000;
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            max-width: 600px;
            padding: 40px;
            background: rgba(30, 30, 30, 0.8);
            border-radius: 12px;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #333;
            border-top: 4px solid #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .progress {
            margin: 10px 0;
            padding: 10px;
            background: rgba(59, 130, 246, 0.1);
            border-radius: 5px;
            border-left: 4px solid #3b82f6;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Setting up Veo 3.1 Test</h1>
        <div class="spinner"></div>
        <div id="status">Preparing test data...</div>
        <div id="progress"></div>
    </div>

    <script>
        const updateStatus = (message) => {
            document.getElementById('status').textContent = message;
        };

        const addProgress = (message) => {
            const progress = document.getElementById('progress');
            const div = document.createElement('div');
            div.className = 'progress';
            div.textContent = message;
            progress.appendChild(div);
        };

        const setupTest = async () => {
            try {
                updateStatus('🧪 Creating test project data...');

                // Create comprehensive test data
                const testData = {
                    video: {
                        name: 'test_video_for_veo.mp4',
                        size: 1024000,
                        duration: 15.5,
                        url: '/api/mock-video-blob',
                        fileType: 'video/mp4'
                    },
                    preferences: {
                        likes: ['Apple', 'Technology', 'iPhone'],
                        audience: ['tech-enthusiasts', 'young-adults'],
                        selectedProducts: [{
                            name: 'iPhone 15 Pro',
                            description: 'Latest iPhone with titanium design and advanced camera system',
                            category: 'Technology',
                            brand: 'Apple',
                            targetAudience: ['tech-enthusiasts', 'young-adults']
                        }],
                        targetDemographic: 'tech-savvy young adults',
                        brandCategories: ['Technology', 'Premium Devices']
                    }
                };

                addProgress('✅ Test data created');
                updateStatus('💾 Setting up sessionStorage...');

                // Clear any existing data
                sessionStorage.clear();

                // Set the test data
                sessionStorage.setItem('frameshift-project', JSON.stringify(testData));
                sessionStorage.setItem('frameshift-video-file', testData.video.url);

                addProgress('✅ SessionStorage configured');
                updateStatus('🔍 Verifying test setup...');

                // Verify the data was stored correctly
                const storedProject = sessionStorage.getItem('frameshift-project');
                const storedVideo = sessionStorage.getItem('frameshift-video-file');

                if (!storedProject || !storedVideo) {
                    throw new Error('Failed to store test data in sessionStorage');
                }

                const parsedData = JSON.parse(storedProject);
                if (!parsedData.video || !parsedData.preferences) {
                    throw new Error('Invalid test data structure');
                }

                addProgress('✅ Test data verified');
                updateStatus('🚀 Redirecting to Veo 3.1 analysis...');

                addProgress('🎯 Ready to test real Veo 3.1 API calls!');
                addProgress('📊 Watch browser console for detailed logs');

                // Redirect after a short delay
                setTimeout(() => {
                    window.location.href = '/analysis';
                }, 2000);

            } catch (error) {
                updateStatus('❌ Setup failed: ' + error.message);
                addProgress('🔄 Try refreshing the page');
                console.error('Test setup error:', error);
            }
        };

        // Start setup immediately
        setupTest();
    </script>
</body>
</html>
  `;

  return new NextResponse(html, {
    headers: { 'Content-Type': 'text/html' },
  });
}