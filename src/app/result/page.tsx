"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Download,
  Share,
  RotateCcw,
  Play,
  Pause,
  Eye,
  Clock,
  Target,
  CheckCircle
} from "lucide-react";
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

// Mock result data - in real app this would come from the API
const MOCK_RESULT = {
  editedVideoUrl: "/api/placeholder-video.mp4", // Placeholder
  metrics: {
    exposureDuration: 3.5,
    visibilityPercentage: 23.3,
    sceneModified: "2.1s → 5.6s",
    totalDuration: 15.0
  },
  grokContext: "Urban environment with excellent lighting conditions. Modern cityscape setting with young demographic appeal. Ideal for technology product placement with natural integration opportunities.",
  processing: {
    completedAt: new Date().toISOString(),
    processingTime: "14.2s"
  }
};

export default function ResultPage() {
  const router = useRouter();
  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [originalVideoUrl, setOriginalVideoUrl] = useState<string>('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeVideo, setActiveVideo] = useState<'original' | 'edited'>('edited');
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);
  const [generatedProduct, setGeneratedProduct] = useState<string>('');

  useEffect(() => {
    const data = sessionStorage.getItem('frameshift-project');
    const videoUrl = sessionStorage.getItem('frameshift-video-file');

    if (!data) {
      router.push('/');
      return;
    }

    try {
      const parsed = JSON.parse(data);
      setProjectData(parsed);
      setOriginalVideoUrl(videoUrl || '');

      // Generate a product based on brand preferences
      if (parsed.preferences.likes.length > 0) {
        const brands = parsed.preferences.likes;
        // Simple logic to pick a product based on brand
        if (brands.some((b: string) => b.toLowerCase().includes('apple'))) {
          setGeneratedProduct('iPhone 15 Pro');
        } else if (brands.some((b: string) => b.toLowerCase().includes('nike'))) {
          setGeneratedProduct('Nike Air Max');
        } else if (brands.some((b: string) => b.toLowerCase().includes('coca'))) {
          setGeneratedProduct('Coca-Cola Classic');
        } else {
          setGeneratedProduct(brands[0]); // Use the first brand as product
        }
      }
    } catch (error) {
      console.error('Error parsing project data:', error);
      router.push('/');
    }
  }, [router]);

  const handleDownload = async () => {
    if (!originalVideoUrl) {
      alert('No video available for download');
      return;
    }

    setIsDownloading(true);
    setDownloadProgress(0);

    // Simulate download progress
    const interval = setInterval(() => {
      setDownloadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsDownloading(false);

          // Create download for the original video (as enhanced version)
          try {
            const link = document.createElement('a');
            link.href = originalVideoUrl;
            link.download = `${generatedProduct.toLowerCase().replace(/\s+/g, '-')}-enhanced.mp4`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          } catch (error) {
            console.error('Download failed:', error);
            alert('Download failed. Please try again.');
          }
          return 100;
        }
        return prev + 10;
      });
    }, 150);
  };

  const handleStartOver = () => {
    sessionStorage.removeItem('frameshift-project');
    router.push('/');
  };

  if (!projectData) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">Loading results...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="icon"
            onClick={() => router.push('/analysis')}
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Video Processing Complete</h1>
            <p className="text-gray-600">Your enhanced video is ready</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Badge variant="default" className="bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3 mr-1" />
            Complete
          </Badge>
        </div>
      </div>

      {/* Video Comparison */}
      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Before & After Comparison</CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant={activeVideo === 'original' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveVideo('original')}
              >
                Original
              </Button>
              <Button
                variant={activeVideo === 'edited' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveVideo('edited')}
              >
                Enhanced
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Original Video */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-gray-700">Original Video</h4>
              <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
                {originalVideoUrl ? (
                  <video
                    src={originalVideoUrl}
                    controls
                    className="w-full h-full object-cover"
                    preload="metadata"
                  >
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                    <div className="text-center text-white">
                      <Play className="w-12 h-12 mx-auto mb-2 opacity-70" />
                      <p className="text-sm opacity-70">Original Video Preview</p>
                      <p className="text-xs opacity-50">{projectData?.video.name}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Enhanced Video */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-700">
                  Enhanced Video
                  <Badge variant="outline" className="ml-2 text-xs">
                    {generatedProduct} Placed
                  </Badge>
                </h4>
              </div>
              <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
                {originalVideoUrl ? (
                  <>
                    <video
                      src={originalVideoUrl}
                      controls
                      className="w-full h-full object-cover"
                      preload="metadata"
                    >
                      Your browser does not support the video tag.
                    </video>
                    <div className="absolute top-4 left-4 bg-blue-600 text-white px-3 py-1 rounded-full text-xs font-medium">
                      Enhanced with {generatedProduct}
                    </div>
                    <div className="absolute bottom-4 right-4 bg-black bg-opacity-75 text-white px-2 py-1 rounded text-xs">
                      AI Enhanced
                    </div>
                  </>
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-900 to-purple-900">
                    <div className="text-center text-white">
                      <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
                        <CheckCircle className="w-8 h-8" />
                      </div>
                      <p className="text-sm font-medium">Enhanced with {generatedProduct}</p>
                      <p className="text-xs opacity-70 mt-1">Generated by Veo 3.1</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Metrics */}
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Eye className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-blue-900">
                  {MOCK_RESULT.metrics.visibilityPercentage.toFixed(1)}%
                </div>
                <div className="text-sm text-blue-700">Visibility</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <Clock className="w-6 h-6 text-green-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-green-900">
                  {MOCK_RESULT.metrics.exposureDuration.toFixed(1)}s
                </div>
                <div className="text-sm text-green-700">Exposure Time</div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Scene Modified:</span>
                <span className="font-medium">{MOCK_RESULT.metrics.sceneModified}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Duration:</span>
                <span className="font-medium">{MOCK_RESULT.metrics.totalDuration.toFixed(1)}s</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Processing Time:</span>
                <span className="font-medium">{MOCK_RESULT.processing.processingTime}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Analysis */}
        <Card>
          <CardHeader>
            <CardTitle>AI Analysis Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Grok Context Analysis</h4>
              <p className="text-sm text-gray-600 bg-purple-50 border border-purple-200 rounded-lg p-3">
                {MOCK_RESULT.grokContext}
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Veo 3.1 Processing</h4>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span>Natural product integration</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span>Lighting consistency maintained</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span>Temporal continuity preserved</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span>Target audience alignment</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <Card className="mt-8">
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={handleDownload}
              size="lg"
              disabled={isDownloading}
              className="min-w-[200px]"
            >
              {isDownloading ? (
                <>
                  <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                  Downloading... {downloadProgress}%
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Download Enhanced Video
                </>
              )}
            </Button>

            <Button
              variant="outline"
              size="lg"
              onClick={() => alert('Share functionality would be implemented here')}
            >
              <Share className="w-4 h-4 mr-2" />
              Share Result
            </Button>

            <Button
              variant="outline"
              size="lg"
              onClick={handleStartOver}
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Start Over
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Project Details */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Project Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Product Placed</h4>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Target className="w-4 h-4 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">{generatedProduct}</p>
                  <p className="text-xs text-gray-500">AI-Generated Product</p>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Target Audience</h4>
              <div className="flex flex-wrap gap-1">
                {projectData.preferences.audience.length > 0 ? (
                  projectData.preferences.audience.map((audience) => (
                    <Badge key={audience} variant="outline" className="text-xs">
                      {audience}
                    </Badge>
                  ))
                ) : (
                  <span className="text-xs text-gray-500">General audience</span>
                )}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Brand Preferences</h4>
              <div className="flex flex-wrap gap-1">
                {projectData.preferences.likes.length > 0 ? (
                  projectData.preferences.likes.slice(0, 3).map((like) => (
                    <Badge key={like} variant="secondary" className="text-xs">
                      {like}
                    </Badge>
                  ))
                ) : (
                  <span className="text-xs text-gray-500">No specific preferences</span>
                )}
                {projectData.preferences.likes.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{projectData.preferences.likes.length - 3} more
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}