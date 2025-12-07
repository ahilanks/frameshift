import { NextRequest, NextResponse } from 'next/server';
import { grokClient } from '@/lib/grokClient';
import { veoClient } from '@/lib/veoClient';
import { ProductPlacement, UserPreferences, TimeRange } from '@/types';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const videoFile = formData.get('video') as File;
    const productData = formData.get('product') as string;
    const preferencesData = formData.get('preferences') as string;
    const timeRangeData = formData.get('timeRange') as string;

    if (!videoFile || !productData) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    const product: ProductPlacement = JSON.parse(productData);
    const preferences: UserPreferences = JSON.parse(preferencesData || '{"likes":[],"audience":[]}');
    const timeRange: TimeRange = JSON.parse(timeRangeData || '{"start":0,"end":10}');

    // Step 1: Optional Grok context extraction
    let grokContext: string | null = null;
    try {
      grokContext = await grokClient.extractContext({
        sceneDescription: `Video file: ${videoFile.name}, Product: ${product.name}`,
        text: `Placing ${product.description} in video content`
      });
    } catch (error) {
      console.warn('Grok context extraction failed:', error);
      // Continue without context - Veo will handle everything
    }

    // Step 2: Process with Veo 3.1 (the main engine)
    const veoResult = await veoClient.processVideoPlacement({
      originalVideo: videoFile,
      product,
      timeRange,
      preferences,
      grokContext: grokContext || undefined
    });

    if (veoResult.status === 'error') {
      return NextResponse.json(
        { error: veoResult.error || 'Video processing failed' },
        { status: 500 }
      );
    }

    // Calculate metrics
    const metrics = {
      exposureDuration: timeRange.end - timeRange.start,
      visibilityPercentage: ((timeRange.end - timeRange.start) / 30) * 100, // Assuming 30s max
      sceneModified: `${timeRange.start.toFixed(1)}s → ${timeRange.end.toFixed(1)}s`,
      totalDuration: 30 // This would come from actual video analysis
    };

    return NextResponse.json({
      success: true,
      editedVideoUrl: veoResult.editedVideoUrl,
      grokContext,
      metrics,
      processing: {
        product: product.name,
        timeRange,
        preferences
      }
    });

  } catch (error) {
    console.error('Processing error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}