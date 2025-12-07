"use client";

import { useCallback, useState, useRef, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, Video, X, CheckCircle, Play, Pause, SkipBack, SkipForward, Volume2, VolumeX } from "lucide-react";
import { cn, formatFileSize, formatDuration } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { VideoTimeline } from "@/components/ui/video-timeline";
import { VideoFile } from "@/types";

interface VideoDropzoneProps {
  onVideoSelect: (video: VideoFile | null) => void;
  selectedVideo: VideoFile | null;
}

// Helper function to map video error codes to human-readable messages
function getVideoErrorMeaning(errorCode: number | undefined): string {
  switch (errorCode) {
    case 1:
      return 'MEDIA_ERR_ABORTED: Video loading was aborted';
    case 2:
      return 'MEDIA_ERR_NETWORK: Network error while loading video';
    case 3:
      return 'MEDIA_ERR_DECODE: Video format/codec not supported';
    case 4:
      return 'MEDIA_ERR_SRC_NOT_SUPPORTED: Video source not supported';
    default:
      return `Unknown error code: ${errorCode}`;
  }
}

export function VideoDropzone({ onVideoSelect, selectedVideo }: VideoDropzoneProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setIsProcessing(true);
    setError(null);

    try {
      // Enhanced file validation
      console.log('Processing video file:', {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: new Date(file.lastModified).toISOString()
      });

      // Check file size (very small files are likely corrupted)
      if (file.size < 10000) { // Less than 10KB
        throw new Error(`Video file "${file.name}" appears to be too small (${Math.round(file.size / 1024)}KB). This may indicate a corrupted or incomplete file.`);
      }

      // Create video element to get duration and frame count
      const video = document.createElement('video');
      video.preload = 'metadata';
      video.muted = true;
      // Remove crossOrigin as it can cause issues with local files

      // Enhanced codec and format checking
      const supportedFormats = [
        'video/mp4',
        'video/webm',
        'video/ogg',
        'video/quicktime'
      ];

      // Check if browser supports the format
      const canPlayType = video.canPlayType(file.type);
      console.log(`Browser support for ${file.type}: ${canPlayType}`);

      if (!canPlayType && !supportedFormats.includes(file.type)) {
        console.warn(`Unsupported video type: ${file.type}. Attempting anyway...`);
      }

      const duration = await new Promise<number>((resolve, reject) => {
        const timeout = setTimeout(() => {
          console.error('Video metadata loading timeout after 15 seconds');
          reject(new Error(`Video "${file.name}" took too long to load. The file may be corrupted or in an unsupported format.`));
        }, 15000); // Increased timeout for problematic files

        video.onloadedmetadata = () => {
          clearTimeout(timeout);
          const videoDuration = video.duration;

          console.log('Video metadata loaded:', {
            duration: videoDuration,
            videoWidth: video.videoWidth,
            videoHeight: video.videoHeight,
            readyState: video.readyState,
            networkState: video.networkState
          });

          URL.revokeObjectURL(video.src);
          video.remove();

          if (isNaN(videoDuration) || videoDuration === 0) {
            console.warn('Invalid duration detected, using fallback');
            resolve(30); // Default fallback duration
          } else {
            resolve(videoDuration);
          }
        };

        video.onerror = (error) => {
          clearTimeout(timeout);
          URL.revokeObjectURL(video.src);
          video.remove();

          // Enhanced error logging with codec detection
          const videoError = video.error;
          const errorDetails = {
            errorType: error.type,
            target: error.target?.tagName,
            errorCode: videoError?.code || 'Unknown',
            errorMessage: videoError?.message || 'No specific error message',
            networkState: video.networkState,
            readyState: video.readyState,
            fileName: file.name,
            fileSize: file.size,
            fileType: file.type,
            canPlayType: video.canPlayType(file.type),
            timestamp: new Date().toISOString(),
            // Map error codes to human readable messages
            errorMeaning: getVideoErrorMeaning(videoError?.code)
          };

          console.error('Enhanced video loading error:', errorDetails);

          // Provide specific error message based on error code
          let errorMessage = `Unable to load video "${file.name}".`;

          if (videoError?.code === 3) {
            errorMessage += ' The video format or codec is not supported by your browser.';
          } else if (videoError?.code === 4) {
            errorMessage += ' The video file appears to be corrupted or incomplete.';
          } else if (file.size < 50000) {
            errorMessage += ' The file is very small and may be corrupted.';
          } else {
            errorMessage += ' Please check the file format and try again.';
          }

          setError(errorMessage);
          reject(new Error(errorMessage));
        };

        // Enhanced load start detection
        video.onloadstart = () => {
          console.log('Video load started');
        };

        video.onprogress = () => {
          console.log('Video loading progress...');
        };

        // Create a proper object URL for the video
        const metadataUrl = URL.createObjectURL(file);
        console.log('🎥 Creating video URL for metadata:', metadataUrl, 'Type:', file.type);
        video.src = metadataUrl;
      });

      // Create a fresh URL for the actual video playback
      const playbackUrl = URL.createObjectURL(file);
      console.log('✅ Video processed successfully:', {
        name: file.name,
        size: file.size,
        type: file.type || 'video/mp4',
        duration: duration,
        url: playbackUrl
      });

      const videoFile: VideoFile = {
        file,
        duration,
        size: file.size,
        url: playbackUrl,
        frameCount: Math.floor(duration * 30), // Estimate 30fps
        currentFrame: 0
      };

      onVideoSelect(videoFile);
    } catch (error) {
      console.error('Error processing video:', error);

      // Fallback: Try to create video file with estimated values for very problematic files
      if (file.size > 10000) { // Only for files that aren't too small
        console.log('Attempting fallback processing...');

        try {
          const fallbackUrl = URL.createObjectURL(file);
          const fallbackDuration = Math.max(10, Math.min(300, file.size / 100000)); // Estimate duration based on file size

          console.log('⚠️ Using fallback for problematic video:', {
            name: file.name,
            url: fallbackUrl,
            estimatedDuration: fallbackDuration
          });

          const videoFile: VideoFile = {
            file,
            duration: fallbackDuration,
            size: file.size,
            url: fallbackUrl,
            frameCount: Math.floor(fallbackDuration * 30),
            currentFrame: 0
          };

          onVideoSelect(videoFile);

          setError(`Video loaded with estimated duration (${Math.round(fallbackDuration)}s). Some features may not work correctly due to file format issues.`);
        } catch (fallbackError) {
          console.error('Fallback processing also failed:', fallbackError);
          setError(error instanceof Error ? error.message : 'Error processing video. Please try with a different file.');
        }
      } else {
        setError(error instanceof Error ? error.message : 'Error processing video. Please try with a different file.');
      }
    } finally {
      setIsProcessing(false);
    }
  }, [onVideoSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.webm', '.mov', '.avi']
    },
    multiple: false,
    disabled: isProcessing
  });

  const handlePlayPause = async () => {
    if (!videoRef.current) {
      console.log('❌ Video ref not found');
      return;
    }

    console.log('🎬 Play/Pause clicked. Current state:', isPlaying);

    try {
      if (isPlaying) {
        videoRef.current.pause();
        setIsPlaying(false);
        console.log('⏸️ Video paused');
      } else {
        // Try to play the video
        await videoRef.current.play();
        setIsPlaying(true);
        console.log('▶️ Video playing');
      }
    } catch (error) {
      console.error('❌ Playback error:', error);
      setError('Unable to play video. Try clicking again or check browser permissions.');
      setIsPlaying(false);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleSeek = (newTime: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const handleFrameStep = (direction: 'forward' | 'backward') => {
    if (!videoRef.current || !selectedVideo) return;

    const frameRate = 30; // Assume 30fps
    const timeStep = 1 / frameRate;
    const newTime = direction === 'forward'
      ? Math.min(currentTime + timeStep, duration)
      : Math.max(currentTime - timeStep, 0);

    handleSeek(newTime);
  };

  const handleRemove = () => {
    if (selectedVideo?.url) {
      URL.revokeObjectURL(selectedVideo.url);
    }
    onVideoSelect(null);
    setCurrentTime(0);
    setDuration(0);
    setIsPlaying(false);
    setError(null);
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !selectedVideo) return;

    const onTimeUpdate = () => handleTimeUpdate();
    const onLoadedMetadata = () => {
      handleLoadedMetadata();
      console.log('📊 Video metadata loaded in player:', {
        duration: video.duration,
        videoWidth: video.videoWidth,
        videoHeight: video.videoHeight
      });
    };

    const onCanPlay = () => {
      console.log('✅ Video can play');
      setError(null); // Clear any previous errors
    };

    const onError = (e: Event) => {
      const videoError = video.error;
      console.error('❌ Video playback error:', {
        error: videoError,
        code: videoError?.code,
        message: videoError?.message,
        src: video.src
      });

      // Only show error for actual playback issues, not initial load
      if (video.readyState > 0 || videoError?.code === 4) {
        setError('Video format not supported. Please try a different file.');
      }
    };

    video.addEventListener('timeupdate', onTimeUpdate);
    video.addEventListener('loadedmetadata', onLoadedMetadata);
    video.addEventListener('canplay', onCanPlay);
    video.addEventListener('error', onError);

    // Set initial duration if available
    if (video.duration && !isNaN(video.duration)) {
      setDuration(video.duration);
    }

    return () => {
      video.removeEventListener('timeupdate', onTimeUpdate);
      video.removeEventListener('loadedmetadata', onLoadedMetadata);
      video.removeEventListener('canplay', onCanPlay);
      video.removeEventListener('error', onError);
    };
  }, [selectedVideo]);

  if (selectedVideo) {
    return (
      <div className="space-y-6 prevent-scroll">
        {/* Video Preview with X.AI Effects */}
        <Card className="overflow-hidden xai-card">
          <CardContent className="p-0">
            {/* Video Container */}
            <div className="relative bg-black rounded-lg overflow-hidden" style={{ isolation: 'isolate' }}>
              <video
                ref={videoRef}
                src={selectedVideo.url}
                className="w-full h-64 object-contain cursor-pointer"
                controls={false}
                playsInline
                muted={false}
                autoPlay={false}
                preload="metadata"
                onEnded={() => {
                  console.log('📼 Video ended');
                  setIsPlaying(false);
                }}
                onPlay={() => {
                  console.log('▶️ Video started playing');
                  setIsPlaying(true);
                }}
                onPause={() => {
                  console.log('⏸️ Video paused');
                  setIsPlaying(false);
                }}
                onError={(e) => {
                  console.error('❌ Video error:', e);
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  handlePlayPause();
                }}
              />

              {/* Gradient Overlay - MUST NOT BLOCK CLICKS */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent pointer-events-none z-0" />

              {/* Quick Controls Overlay */}
              <div className="absolute top-4 right-4 flex space-x-2 z-30">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (videoRef.current) {
                      videoRef.current.muted = !videoRef.current.muted;
                      setIsMuted(videoRef.current.muted);
                      console.log(`🔊 Sound ${videoRef.current.muted ? 'muted' : 'unmuted'}`);
                    }
                  }}
                  className="bg-blue-500/80 hover:bg-blue-500 text-white"
                  title={isMuted ? "Unmute" : "Mute"}
                >
                  {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemove();
                  }}
                  className="bg-red-500/80 hover:bg-red-500 text-white"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {/* Center Play/Pause Button */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-20">
                <Button
                  size="lg"
                  data-testid="play-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    handlePlayPause();
                  }}
                  className={cn(
                    "bg-white/90 hover:bg-white text-black rounded-full p-4 pointer-events-auto transition-all",
                    "hover:scale-110 shadow-lg",
                    isPlaying && "opacity-0 hover:opacity-100"
                  )}
                >
                  {isPlaying ? <Pause className="w-8 h-8" /> : <Play className="w-8 h-8" />}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Cool Video Timeline */}
        <VideoTimeline
          videoRef={videoRef}
          duration={duration}
          currentTime={currentTime}
          isPlaying={isPlaying}
          onSeek={handleSeek}
          onPlayPause={handlePlayPause}
          onFrameStep={handleFrameStep}
        />

        {/* File Information */}
        <Card className="xai-card">
          <CardContent className="pt-6">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm font-medium xai-text-primary">{selectedVideo.file.name}</p>
                <p className="text-xs xai-text-muted">Filename</p>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium xai-text-primary">{formatFileSize(selectedVideo.size)}</p>
                <p className="text-xs xai-text-muted">File Size</p>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium xai-text-primary">{formatDuration(selectedVideo.duration)}</p>
                <p className="text-xs xai-text-muted">Duration</p>
              </div>
            </div>

            {/* Enhanced Frame Info with X.AI styling */}
            <div className="mt-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg p-4 border border-blue-500/20 xai-card">
              <div className="flex justify-between items-center text-sm">
                <div className="text-blue-400">
                  <span className="font-medium">Current Frame:</span> {Math.floor(currentTime * 30)}
                </div>
                <div className="text-purple-400">
                  <span className="font-medium">Total Frames:</span> ~{selectedVideo.frameCount || 'Unknown'}
                </div>
                <div className="text-cyan-400">
                  <span className="font-medium">Frame Rate:</span> ~30fps
                </div>
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg xai-card">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      data-testid="video-dropzone"
      className={cn(
        "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-300 prevent-scroll",
        isDragActive
          ? "border-blue-400 bg-blue-500/10 scale-105"
          : "border-white/30 hover:border-blue-400 hover:bg-blue-500/5 hover:scale-105",
        isProcessing && "pointer-events-none opacity-50"
      )}
    >
      <input {...getInputProps()} />

      <div className="space-y-4">
        {isProcessing ? (
          <>
            <div className="w-12 h-12 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto timeline-glow" />
            <div>
              <h3 className="text-lg font-medium xai-text-primary">Processing Video...</h3>
              <p className="text-sm xai-text-secondary">
                Extracting metadata and preparing cool preview
              </p>
            </div>
          </>
        ) : (
          <>
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mx-auto timeline-glow">
              {isDragActive ? (
                <Upload className="w-6 h-6 text-white animate-bounce" />
              ) : (
                <Video className="w-6 h-6 text-white" />
              )}
            </div>
            <div>
              <h3 className="text-lg font-medium xai-text-primary">
                {isDragActive ? "Drop your video here! 🎬" : "Upload Video"}
              </h3>
              <p className="text-sm xai-text-secondary">
                Drop a video file here, or click to select
              </p>
              <p className="text-xs xai-text-muted mt-1">
                Supports MP4, WebM, MOV, AVI (max 100MB)
              </p>
            </div>
          </>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg xai-card">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}