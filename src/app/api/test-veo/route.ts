import { NextRequest, NextResponse } from 'next/server';
import { veoClient } from '@/lib/veoClient';
import { apiLogger } from '@/lib/apiLogger';

export async function GET(request: NextRequest) {
  console.log('\n🧪 ===== VEO 3.1 API TEST ENDPOINT =====');
  console.log('Testing Veo 3.1 integration and API calls...');

  try {
    // Test data for API verification
    const testRequest = {
      originalVideo: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4',
      product: {
        id: 'test-iphone',
        name: 'iPhone 15 Pro',
        description: 'Latest flagship smartphone with titanium design',
        category: 'Technology',
        imageUrl: 'https://via.placeholder.com/100x100?text=iPhone'
      },
      timeRange: {
        start: 2.0,
        end: 5.0
      },
      preferences: {
        likes: ['Apple', 'Technology'],
        audience: ['Tech enthusiasts'],
        selectedProducts: []
      },
      grokContext: 'Test context for Veo 3.1 API verification'
    };

    console.log('📋 Test Request Data:', {
      product: testRequest.product.name,
      timeRange: testRequest.timeRange,
      hasGrokContext: !!testRequest.grokContext
    });

    // Make the actual Veo 3.1 API call
    const result = await veoClient.processVideoPlacement(testRequest);

    // Get API call statistics
    const stats = apiLogger.getStats();
    const recentLogs = apiLogger.getVeoLogs().slice(-3); // Last 3 calls

    console.log('✅ VEO 3.1 Test completed!');
    console.log('📊 API Call Statistics:', stats);

    return NextResponse.json({
      success: true,
      testResult: result,
      apiStats: stats,
      recentLogs: recentLogs.map(log => ({
        timestamp: log.timestamp,
        model: log.model,
        status: log.status,
        duration: log.duration,
        hasVideoUrl: !!(log.response && apiLogger['hasVideoUrl'](log.response))
      })),
      verification: {
        veoClientInitialized: !!veoClient,
        apiKeyConfigured: !!(process.env.GOOGLE_API_KEY || process.env.VEO_API_KEY),
        modelUsed: 'veo-3.1-generate-preview',
        loggingActive: true
      },
      message: 'Veo 3.1 API test completed - check console for detailed logs'
    });

  } catch (error) {
    console.error('❌ VEO 3.1 Test failed:', error);

    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      verification: {
        veoClientInitialized: !!veoClient,
        apiKeyConfigured: !!(process.env.GOOGLE_API_KEY || process.env.VEO_API_KEY),
        modelUsed: 'veo-3.1-generate-preview',
        loggingActive: true
      },
      apiStats: apiLogger.getStats()
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  console.log('\n🔧 ===== CUSTOM VEO 3.1 TEST =====');

  try {
    const body = await request.json();
    const { prompt, productName, timeStart, timeEnd } = body;

    if (!prompt || !productName) {
      return NextResponse.json({
        error: 'Missing required fields: prompt, productName'
      }, { status: 400 });
    }

    const customRequest = {
      originalVideo: 'test-video-placeholder',
      product: {
        id: `test-${Date.now()}`,
        name: productName,
        description: `Test product: ${productName}`,
        category: 'Test',
        imageUrl: 'https://via.placeholder.com/100x100'
      },
      timeRange: {
        start: timeStart || 0,
        end: timeEnd || 10
      },
      preferences: {
        likes: [productName],
        audience: ['Test users'],
        selectedProducts: []
      },
      grokContext: `Custom test for ${productName}`
    };

    console.log('🎯 Custom Veo 3.1 test with:', {
      product: customRequest.product.name,
      customPrompt: prompt.substring(0, 100) + '...'
    });

    const result = await veoClient.processVideoPlacement(customRequest);

    return NextResponse.json({
      success: true,
      customTest: true,
      result,
      prompt: prompt,
      verification: {
        apiCalled: true,
        model: 'veo-3.1-generate-preview',
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('❌ Custom VEO 3.1 Test failed:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Custom test failed'
    }, { status: 500 });
  }
}