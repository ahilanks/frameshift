import { NextResponse } from 'next/server';

export async function POST() {
  try {
    console.log('🧪 TEST VIDEO FLOW: Creating test project data...');

    // Create mock project data as if a user uploaded a video
    const testProjectData = {
      video: {
        name: 'test_video.mp4',
        size: 1024000,
        duration: 15.5,
        url: '/api/mock-video-blob',
        fileType: 'video/mp4'
      },
      preferences: {
        likes: ['Apple', 'Technology'],
        audience: ['tech-enthusiasts', 'young-adults'],
        selectedProducts: [{
          name: 'iPhone 15 Pro',
          description: 'Latest iPhone with titanium design',
          category: 'Technology'
        }]
      }
    };

    console.log('📊 Test project data created:', testProjectData);

    return NextResponse.json({
      success: true,
      message: 'Test project data created',
      data: testProjectData,
      instructions: {
        step1: 'Copy this data to sessionStorage with key "frameshift-project"',
        step2: 'Navigate to /analysis to test the flow',
        step3: 'Check browser console for detailed logging'
      }
    });
  } catch (error) {
    console.error('❌ Test flow creation failed:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

export async function GET() {
  return NextResponse.json({
    message: 'POST to this endpoint to create test data',
    usage: 'curl -X POST http://localhost:5001/api/test-video-flow'
  });
}