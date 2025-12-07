"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles, Zap } from "lucide-react";
import { VideoDropzone } from "@/components/upload/video-dropzone";
import { PreferencesForm } from "@/components/upload/preferences-form";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { VideoFile, UserPreferences } from "@/types";

interface Particle {
  left: string;
  top: string;
  animationDelay: string;
}

export default function HomePage() {
  const router = useRouter();
  const [selectedVideo, setSelectedVideo] = useState<VideoFile | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences>({
    likes: [],
    audience: [],
    selectedProducts: []
  });
  const [particles, setParticles] = useState<Particle[]>([]);

  const canProceed = selectedVideo && (preferences.likes.length > 0 || (preferences.selectedProducts && preferences.selectedProducts.length > 0));

  // Generate particles client-side only to prevent hydration errors
  useEffect(() => {
    const generatedParticles: Particle[] = [];
    for (let i = 0; i < 50; i++) {
      generatedParticles.push({
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        animationDelay: `${Math.random() * 15}s`,
      });
    }
    setParticles(generatedParticles);
  }, []);

  const handleProceed = () => {
    if (!canProceed) return;

    console.log('📤 Starting analysis with:', { selectedVideo, preferences });

    // Validate data before proceeding
    if (!selectedVideo) {
      console.error('❌ No video selected');
      alert('Please select a video first.');
      return;
    }

    if (!selectedVideo.file) {
      console.error('❌ No video file found in selectedVideo');
      alert('Video file is missing. Please upload again.');
      return;
    }

    if (!selectedVideo.url) {
      console.error('❌ No video URL found');
      alert('Video URL is missing. Please upload again.');
      return;
    }

    // Store data in sessionStorage for the next page
    const projectData = {
      video: {
        name: selectedVideo.file.name || 'uploaded_video.mp4',
        size: selectedVideo.size || selectedVideo.file.size,
        duration: selectedVideo.duration || 10,
        url: selectedVideo.url,
        fileType: selectedVideo.file.type
      },
      preferences: {
        ...preferences,
        // Ensure we have at least some data
        likes: preferences.likes || [],
        audience: preferences.audience || [],
        selectedProducts: preferences.selectedProducts || []
      }
    };

    console.log('💾 Storing project data:', projectData);
    sessionStorage.setItem('frameshift-project', JSON.stringify(projectData));
    sessionStorage.setItem('frameshift-video-file', selectedVideo.url);

    console.log('🔄 Navigating to analysis...');
    router.push('/analysis');
  };

  return (
    <div className="relative min-h-screen bg-black">
      {/* X.AI Particle System */}
      <div className="xai-particles">
        {particles.map((particle, i) => (
          <div
            key={i}
            className="xai-particle"
            style={{
              left: particle.left,
              top: particle.top,
              animationDelay: particle.animationDelay,
            }}
          />
        ))}
      </div>

      {/* X.AI Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Deep gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-900 to-black" />

        {/* Subtle blue glow */}
        <div className="absolute inset-0 bg-gradient-radial from-blue-500/5 via-transparent to-transparent" />

        {/* Floating orbs */}
        <div className="absolute top-1/4 left-1/6 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-[xai-wave_15s_ease-in-out_infinite]" />
        <div className="absolute top-3/4 right-1/6 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl animate-[xai-wave_20s_ease-in-out_infinite_reverse]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
        <div className="inline-flex items-center px-6 py-3 rounded-full xai-card xai-hover xai-timeline-glow mb-8">
          <Sparkles className="w-5 h-5 mr-3 text-blue-400" />
          <span className="xai-text-gradient text-sm font-semibold tracking-wide">
            Powered by Veo 3.1 & Grok AI
          </span>
        </div>
        <h1 className="text-5xl font-bold xai-text-primary mb-6 tracking-tight">
          AI-Powered Product Placement
        </h1>
        <p className="text-xl xai-text-secondary max-w-4xl mx-auto leading-relaxed">
          Transform your videos with seamless, natural product placement.
          Upload your content, select products, and let our AI create compelling branded content.
        </p>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column */}
        <div className="space-y-8">
          {/* Video Upload */}
          <div className="xai-card xai-hover">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full flex items-center justify-center text-sm font-bold mr-4 xai-timeline-glow">
                  1
                </div>
                <h3 className="text-lg font-semibold xai-text-primary">Upload Video</h3>
              </div>
              <VideoDropzone
                selectedVideo={selectedVideo}
                onVideoSelect={setSelectedVideo}
              />
            </div>
          </div>

          {/* Brand Preferences */}
          <div className="xai-card xai-hover">
            <div className="p-6">
              <div className="flex items-center mb-6">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-cyan-600 text-white rounded-full flex items-center justify-center text-sm font-bold mr-4 xai-timeline-glow">
                  2
                </div>
                <h3 className="text-lg font-semibold xai-text-primary">Brand Preferences</h3>
                <span className="ml-3 text-sm text-red-400 bg-red-500/10 px-2 py-1 rounded-full">*Required</span>
              </div>
              <PreferencesForm
                preferences={preferences}
                onChange={setPreferences}
              />
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-8">
          {/* AI Generation Info */}
          <div className="xai-card xai-hover border-2 border-purple-500/20">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <Zap className="w-6 h-6 mr-3 text-purple-400 xai-timeline-glow" />
                <h3 className="text-xl font-semibold xai-text-gradient">
                  AI-Powered Product Placement
                </h3>
              </div>
              <div className="space-y-4">
                <p className="xai-text-secondary text-sm">
                  Our AI will automatically analyze your video and brand preferences to:
                </p>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full mr-3" />
                    <span className="xai-text-secondary">Select the perfect product for your scene</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-full mr-3" />
                    <span className="xai-text-secondary">Find optimal placement timing and position</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-gradient-to-r from-cyan-400 to-green-400 rounded-full mr-3" />
                    <span className="xai-text-secondary">Generate natural, seamless integration</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-gradient-to-r from-green-400 to-purple-400 rounded-full mr-3" />
                    <span className="xai-text-secondary">Match your target audience preferences</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Process Summary */}
          {canProceed && (
            <div className="xai-card xai-hover border-2 border-green-500/20">
              <div className="p-6">
                <h3 className="text-xl font-semibold mb-4 flex items-center">
                  <span className="xai-text-gradient">Ready to Process</span>
                  <div className="ml-3 w-3 h-3 bg-gradient-to-r from-green-400 to-blue-400 rounded-full animate-pulse" />
                </h3>
                <div className="space-y-4 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="xai-text-muted">Video:</span>
                    <span className="xai-text-secondary font-medium">{selectedVideo?.file?.name || 'Unknown video'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="xai-text-muted">Brand Preferences:</span>
                    <span className="xai-text-secondary font-medium text-right">
                      {preferences.selectedProducts && preferences.selectedProducts.length > 0
                        ? preferences.selectedProducts.map(p => p.name).join(', ')
                        : preferences.likes.length > 0
                          ? preferences.likes.join(', ')
                          : 'Auto-generate from AI'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="xai-text-muted">Duration:</span>
                    <span className="xai-text-secondary font-medium">{(selectedVideo?.duration || 0).toFixed(1)}s</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="xai-text-muted">AI Generation:</span>
                    <span className="xai-text-secondary font-medium">Automatic Product Selection</span>
                  </div>
                </div>
                <button
                  onClick={handleProceed}
                  className="xai-button w-full mt-6 py-4 px-6 rounded-xl text-white font-semibold text-lg flex items-center justify-center transition-all duration-300"
                >
                  Analyze & Generate
                  <ArrowRight className="w-5 h-5 ml-2" />
                </button>
              </div>
            </div>
          )}

          {/* Help Text */}
          <div className="xai-card xai-hover">
            <div className="p-6">
              <h3 className="font-semibold xai-text-primary mb-4 text-lg">How it works:</h3>
              <ol className="text-sm space-y-4">
                <li className="flex items-start">
                  <div className="w-6 h-6 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-full flex items-center justify-center text-xs font-bold mr-4 mt-0.5 flex-shrink-0 xai-timeline-glow">
                    1
                  </div>
                  <span className="xai-text-secondary">Upload your video (MP4, WebM, or MOV)</span>
                </li>
                <li className="flex items-start">
                  <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-cyan-500 text-white rounded-full flex items-center justify-center text-xs font-bold mr-4 mt-0.5 flex-shrink-0 xai-timeline-glow">
                    2
                  </div>
                  <span className="xai-text-secondary">Grok AI analyzes scene context (optional)</span>
                </li>
                <li className="flex items-start">
                  <div className="w-6 h-6 bg-gradient-to-r from-cyan-500 to-green-500 text-white rounded-full flex items-center justify-center text-xs font-bold mr-4 mt-0.5 flex-shrink-0 xai-timeline-glow">
                    3
                  </div>
                  <span className="xai-text-secondary">Veo 3.1 seamlessly integrates your product</span>
                </li>
                <li className="flex items-start">
                  <div className="w-6 h-6 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold mr-4 mt-0.5 flex-shrink-0 xai-timeline-glow">
                    4
                  </div>
                  <span className="xai-text-secondary">Download your enhanced video</span>
                </li>
              </ol>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}