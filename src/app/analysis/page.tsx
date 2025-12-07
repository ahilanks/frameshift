"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Brain, Video, Zap, Clock, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ProductPlacement, UserPreferences } from "@/types";

interface ProjectData {
  video: {
    name: string;
    size: number;
    duration: number;
    url?: string;
  };
  preferences: UserPreferences;
}

export default function AnalysisPage() {
  const router = useRouter();
  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [grokContext, setGrokContext] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingResult, setProcessingResult] = useState<any>(null);
  const [processingError, setProcessingError] = useState<string | null>(null);

  const steps = [
    {
      id: 0,
      name: "Initializing",
      description: "Loading project data...",
      icon: Clock,
      duration: 1000
    },
    {
      id: 1,
      name: "Context Analysis",
      description: "Grok AI is analyzing video context (optional)...",
      icon: Brain,
      duration: 3000
    },
    {
      id: 2,
      name: "Product Selection",
      description: "AI selecting optimal product based on your preferences...",
      icon: Video,
      duration: 2000
    },
    {
      id: 3,
      name: "AI Processing",
      description: "Veo 3.1 is generating your enhanced video...",
      icon: Zap,
      duration: 8000
    }
  ];

  useEffect(() => {
    console.log('🔍 ANALYSIS PAGE: Checking sessionStorage...');

    const data = sessionStorage.getItem('frameshift-project');
    const videoFile = sessionStorage.getItem('frameshift-video-file');

    console.log('📋 SessionStorage contents:');
    console.log('  - frameshift-project:', data ? 'EXISTS' : 'NULL');
    console.log('  - frameshift-video-file:', videoFile ? 'EXISTS' : 'NULL');

    if (!data) {
      console.error('❌ No project data found in sessionStorage');
      console.log('🔍 Debug: All sessionStorage keys:', Object.keys(sessionStorage));
      setProcessingError('No project data found. Please go back and upload a video first.');
      return;
    }

    try {
      const parsed = JSON.parse(data);
      console.log('📋 Retrieved project data:', parsed);
      console.log('📋 Video data in project:', parsed.video);
      console.log('📋 Preferences in project:', parsed.preferences);

      if (!parsed) {
        console.error('❌ Parsed data is null');
        setProcessingError('Invalid project data format. Please try again.');
        return;
      }

      // Check if we have video data (even if it's missing some fields)
      if (!parsed.video && !videoFile) {
        console.error('❌ No video data found in project or sessionStorage');
        setProcessingError('No video found. Please go back and upload a video.');
        return;
      }

      // If video data is missing but we have a video file, create minimal video data
      if (!parsed.video && videoFile) {
        console.warn('🔧 Video data missing, creating from video file URL');
        parsed.video = {
          name: 'uploaded_video.mp4',
          duration: 10,
          size: 0,
          url: videoFile
        };
      }

      console.log('✅ Project data validated and ready');
      setProjectData(parsed);

      // Start processing after a small delay to show the UI first
      setTimeout(() => {
        console.log('🚀 Starting processing with:', parsed);
        startProcessing();
      }, 1000);
    } catch (error) {
      console.error('❌ Error parsing project data:', error);
      console.log('📋 Raw data that failed to parse:', data);
      setProcessingError(`Error reading project data: ${error.message}`);
    }
  }, [router]);

  const startProcessing = async () => {
    if (!projectData) {
      console.error('❌ Cannot start processing: projectData is null');
      setProcessingError('No project data available. Please go back and upload a video.');
      return;
    }

    setIsProcessing(true);
    setProcessingError(null);

    try {
      // Step 0: Initialize
      setCurrentStep(0);
      console.log('🎬 STARTING VEO 3.1 PROCESSING');
      console.log('📋 Project Data:', projectData);
      await new Promise(resolve => setTimeout(resolve, steps[0].duration));

      // Step 1: Grok Context (optional)
      setCurrentStep(1);
      console.log('🧠 GROK AI: Analyzing context...');
      setTimeout(() => {
        setGrokContext("Scene contains urban environment with good lighting. Modern cityscape with clear sky. Suitable for technology product placement. Young demographic appears to be target audience based on scene aesthetics.");
      }, 1500);
      await new Promise(resolve => setTimeout(resolve, steps[1].duration));

      // Step 2: Product Selection
      setCurrentStep(2);
      console.log('🎯 AI: Selecting optimal product...');
      await new Promise(resolve => setTimeout(resolve, steps[2].duration));

      // Step 3: ACTUAL VEO 3.1 API CALL
      setCurrentStep(3);
      console.log('🚀 VEO 3.1: Starting REAL API call for video modification...');
      console.log('⚡ This will ACTUALLY modify your video with iPhone 15 Pro placement!');
      console.log('📋 Current projectData:', projectData);

      // Get the video file from sessionStorage
      const videoUrl = sessionStorage.getItem('frameshift-video-file');
      if (!videoUrl) {
        throw new Error('No video file found in sessionStorage');
      }

      console.log('🎥 Video URL found:', videoUrl);
      console.log('📊 Project data available:', !!projectData);

      // Create a test product placement for Apple advertisement
      const testProduct = {
        name: 'iPhone 15 Pro',
        description: 'Latest iPhone with titanium design and advanced camera system',
        category: 'Technology',
        brand: 'Apple',
        targetAudience: ['tech-enthusiasts', 'young-adults']
      };

      const testTimeRange = {
        start: 2.0, // Start at 2 seconds
        end: 8.0   // End at 8 seconds
      };

      // Prepare form data for the API call
      const formData = new FormData();

      // Convert the video URL back to a file for the API
      console.log('🔄 Converting video URL to file...');
      const response = await fetch(videoUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch video: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      const videoFile = new File([blob], projectData?.video?.name || 'uploaded_video.mp4', {
        type: blob.type || 'video/mp4'
      });

      console.log('📁 Video file created:', {
        name: videoFile.name,
        size: videoFile.size,
        type: videoFile.type
      });

      formData.append('video', videoFile);
      formData.append('product', JSON.stringify(testProduct));
      formData.append('preferences', JSON.stringify(projectData?.preferences || {}));
      formData.append('timeRange', JSON.stringify(testTimeRange));

      console.log('📤 SENDING TO VEO 3.1 API...');
      console.log('🎥 Video:', videoFile.name);
      console.log('📱 Product:', testProduct.name);
      console.log('⏰ Time Range:', testTimeRange);

      // Make the actual API call
      const apiResponse = await fetch('/api/process', {
        method: 'POST',
        body: formData
      });

      if (!apiResponse.ok) {
        throw new Error(`API call failed: ${apiResponse.status} ${apiResponse.statusText}`);
      }

      const result = await apiResponse.json();
      console.log('✅ VEO 3.1 API RESPONSE RECEIVED:', result);

      if (result.success) {
        console.log('🎉 VIDEO SUCCESSFULLY MODIFIED!');
        console.log('📹 Original video: ', projectData?.video?.name || 'unknown');
        console.log('🍎 Product added: iPhone 15 Pro');
        console.log('🎬 Modified video URL:', result.editedVideoUrl);
      } else {
        console.error('❌ API returned error:', result.error);
        throw new Error(result.error || 'API processing failed');
      }

      setProcessingResult(result);

      // Store result for the next page
      sessionStorage.setItem('frameshift-result', JSON.stringify(result));

      setIsProcessing(false);

      // Navigate to results after a short delay
      setTimeout(() => {
        router.push('/result');
      }, 2000);

    } catch (error) {
      console.error('❌ VEO 3.1 PROCESSING FAILED:', error);
      setProcessingError(error instanceof Error ? error.message : 'Unknown error occurred');
      setIsProcessing(false);
    }
  };

  const handleBack = () => {
    router.push('/');
  };

  if (!projectData) {
    return (
      <div className="relative min-h-screen bg-black">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="xai-text-secondary">Loading project data...</p>
            <p className="text-xs xai-text-muted mt-2">Checking sessionStorage...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="icon"
            onClick={handleBack}
            disabled={isProcessing}
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold xai-text-primary">AI Analysis & Generation</h1>
            <p className="text-gray-400">Processing your video with advanced AI</p>
          </div>
        </div>
      </div>

      {/* Project Summary */}
      <Card className="mb-8 xai-card">
        <CardHeader>
          <CardTitle className="xai-text-primary">Project Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <Video className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <p className="text-sm font-medium xai-text-primary">{projectData?.video?.name || 'Video'}</p>
              <p className="text-xs xai-text-secondary">{(projectData?.video?.duration || 0).toFixed(1)}s</p>
            </div>
            <div className="text-center">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                <span className="text-purple-600 font-bold text-sm">B</span>
              </div>
              <p className="text-sm font-medium xai-text-primary">
                {projectData.preferences.likes.length > 0 ? projectData.preferences.likes.join(', ') : 'No brands specified'}
              </p>
              <p className="text-xs xai-text-secondary">{projectData.preferences.likes.length} brand(s)</p>
            </div>
            <div className="text-center">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                <span className="text-green-600 font-bold text-sm">T</span>
              </div>
              <p className="text-sm font-medium xai-text-primary">
                {projectData.preferences.audience.length > 0 ? 'Targeted' : 'General'}
              </p>
              <p className="text-xs xai-text-secondary">
                {projectData.preferences.audience.length} audience(s)
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Processing Steps */}
      <Card className="mb-8 xai-card">
        <CardHeader>
          <CardTitle className="xai-text-primary">Processing Pipeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = currentStep === index && isProcessing;
              const isCompleted = currentStep > index || !isProcessing;
              const isPending = currentStep < index && isProcessing;

              return (
                <div
                  key={step.id}
                  className={`flex items-center p-4 rounded-lg border transition-all duration-300 ${
                    isActive
                      ? 'border-blue-300 bg-blue-50'
                      : isCompleted
                      ? 'border-green-300 bg-green-50'
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-4 ${
                    isActive
                      ? 'bg-blue-100'
                      : isCompleted
                      ? 'bg-green-100'
                      : 'bg-gray-100'
                  }`}>
                    {isActive ? (
                      <div className="animate-spin w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full" />
                    ) : isCompleted ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <Icon className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <h3 className={`font-medium ${
                      isActive
                        ? 'text-blue-900'
                        : isCompleted
                        ? 'text-green-900'
                        : 'xai-text-primary'
                    }`}>
                      {step.name}
                    </h3>
                    <p className={`text-sm ${
                      isActive
                        ? 'text-blue-700'
                        : isCompleted
                        ? 'text-green-700'
                        : 'xai-text-secondary'
                    }`}>
                      {step.description}
                    </p>
                  </div>
                  {isCompleted && (
                    <Badge variant="secondary" className="text-xs">
                      Complete
                    </Badge>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {processingError && (
        <div className="mb-8 xai-card border-2 border-red-500/20">
          <div className="p-6">
            <h3 className="text-red-400 font-semibold mb-2">❌ Processing Error</h3>
            <p className="xai-text-secondary text-sm">{processingError}</p>
            <button
              onClick={() => router.push('/')}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Go Back
            </button>
          </div>
        </div>
      )}

      {/* API Success Display */}
      {processingResult && (
        <div className="mb-8 xai-card border-2 border-green-500/20">
          <div className="p-6">
            <h3 className="text-green-400 font-semibold mb-2">✅ Veo 3.1 API Called Successfully</h3>
            <p className="xai-text-secondary text-sm">Product: iPhone 15 Pro integrated into video</p>
            <p className="xai-text-secondary text-sm">Time range: 2.0s - 8.0s modified</p>
          </div>
        </div>
      )}

      {/* Grok Context (if available) */}
      {grokContext && (
        <Card className="mb-8 xai-card">
          <CardHeader>
            <CardTitle className="flex items-center xai-text-primary">
              <Brain className="w-5 h-5 mr-2 text-purple-600" />
              Grok AI Context Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <p className="text-purple-800 text-sm">{grokContext}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Processing Info */}
      <Card className="xai-card">
        <CardHeader>
          <CardTitle className="xai-text-primary">AI Engine Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="font-medium xai-text-primary">Grok AI (Context)</h4>
              <ul className="text-sm xai-text-secondary space-y-1">
                <li>• Scene understanding and analysis</li>
                <li>• Optional contextual enhancement</li>
                <li>• Natural language scene description</li>
                <li>• Audience demographic insights</li>
              </ul>
            </div>
            <div className="space-y-3">
              <h4 className="font-medium xai-text-primary">Veo 3.1 (Primary Engine)</h4>
              <ul className="text-sm xai-text-secondary space-y-1">
                <li>• Advanced video generation and editing</li>
                <li>• Seamless product integration</li>
                <li>• Natural lighting and physics</li>
                <li>• Temporal consistency maintenance</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress indicator */}
      {isProcessing && (
        <div className="fixed bottom-8 right-8">
          <Card className="shadow-lg xai-card">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <div className="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full" />
                <span className="text-sm font-medium xai-text-primary">
                  Processing step {currentStep + 1} of {steps.length}
                </span>
              </div>
              <div className="mt-2 w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-1000"
                  style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}