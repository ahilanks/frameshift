"use client";

import { useState, useRef, useEffect } from "react";
import { Play, Pause, SkipBack, SkipForward, Zap, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface AdMarker {
  id: string;
  name: string;
  startTime: number;
  endTime: number;
  type: 'placement' | 'overlay' | 'integration';
  color: string;
}

interface VideoTimelineProps {
  videoRef: React.RefObject<HTMLVideoElement>;
  duration: number;
  currentTime: number;
  isPlaying: boolean;
  onSeek: (time: number) => void;
  onPlayPause: () => void;
  onFrameStep: (direction: 'forward' | 'backward') => void;
  adMarkers?: AdMarker[];
  className?: string;
}

const DEFAULT_AD_MARKERS: AdMarker[] = [
  {
    id: '1',
    name: 'iPhone 15 Pro Placement',
    startTime: 2.1,
    endTime: 5.6,
    type: 'placement',
    color: '#3B82F6'
  },
  {
    id: '2',
    name: 'Brand Overlay',
    startTime: 8.2,
    endTime: 10.5,
    type: 'overlay',
    color: '#10B981'
  },
  {
    id: '3',
    name: 'Product Integration',
    startTime: 12.0,
    endTime: 14.8,
    type: 'integration',
    color: '#8B5CF6'
  }
];

export function VideoTimeline({
  videoRef,
  duration,
  currentTime,
  isPlaying,
  onSeek,
  onPlayPause,
  onFrameStep,
  adMarkers = DEFAULT_AD_MARKERS,
  className
}: VideoTimelineProps) {
  const timelineRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [hoveredMarker, setHoveredMarker] = useState<AdMarker | null>(null);

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    const milliseconds = Math.floor((time % 1) * 100);
    return `${minutes}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(2, '0')}`;
  };

  const handleTimelineClick = (event: React.MouseEvent) => {
    if (!timelineRef.current || duration === 0) {
      console.log('❌ Timeline not ready:', { ref: !!timelineRef.current, duration });
      return;
    }

    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, clickX / rect.width));
    const newTime = percentage * duration;

    // Snap to nearest frame for precision (assuming 30fps)
    const frameRate = 30;
    const frameTime = 1 / frameRate;
    const snappedTime = Math.round(newTime / frameTime) * frameTime;
    const finalTime = Math.max(0, Math.min(duration, snappedTime));

    console.log('🎯 Timeline seek:', {
      clickX,
      percentage: (percentage * 100).toFixed(1) + '%',
      newTime: newTime.toFixed(2) + 's',
      finalTime: finalTime.toFixed(2) + 's'
    });

    onSeek(finalTime);
  };

  const handleMouseDown = (event: React.MouseEvent) => {
    setIsDragging(true);
    handleTimelineClick(event);
  };

  const handleMouseMove = (event: React.MouseEvent) => {
    if (isDragging) {
      handleTimelineClick(event);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    const handleGlobalMouseUp = () => setIsDragging(false);
    if (isDragging) {
      document.addEventListener('mouseup', handleGlobalMouseUp);
      return () => document.removeEventListener('mouseup', handleGlobalMouseUp);
    }
  }, [isDragging]);

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className={cn("space-y-4", className)}>
      {/* X.AI Style Background Effects */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-black via-gray-900 to-black p-6">
        {/* Animated Wave Background */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/30 via-purple-600/30 to-cyan-600/30 animate-pulse" />
          <div className="absolute inset-0">
            <svg className="w-full h-full" viewBox="0 0 1000 400" preserveAspectRatio="none">
              <path
                d="M0,200 Q250,100 500,200 T1000,200 L1000,400 L0,400 Z"
                fill="url(#waveGradient1)"
                className="animate-[wave_6s_ease-in-out_infinite]"
              />
              <path
                d="M0,250 Q250,150 500,250 T1000,250 L1000,400 L0,400 Z"
                fill="url(#waveGradient2)"
                className="animate-[wave_8s_ease-in-out_infinite_reverse]"
              />
              <defs>
                <linearGradient id="waveGradient1" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.3" />
                  <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.3" />
                </linearGradient>
                <linearGradient id="waveGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#10B981" stopOpacity="0.2" />
                  <stop offset="50%" stopColor="#F59E0B" stopOpacity="0.1" />
                  <stop offset="100%" stopColor="#EF4444" stopOpacity="0.2" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          {/* Floating Orbs */}
          <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-blue-500/10 rounded-full blur-xl animate-[float_4s_ease-in-out_infinite]" />
          <div className="absolute top-3/4 right-1/4 w-24 h-24 bg-purple-500/10 rounded-full blur-xl animate-[float_6s_ease-in-out_infinite_reverse]" />
          <div className="absolute top-1/2 left-3/4 w-20 h-20 bg-cyan-500/10 rounded-full blur-xl animate-[float_5s_ease-in-out_infinite]" />
        </div>

        {/* Control Bar */}
        <div className="relative z-10 flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation();
                console.log('⏪ Frame step backward');
                onFrameStep('backward');
              }}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20 transition-all duration-300 hover:scale-110 z-20"
            >
              <SkipBack className="w-4 h-4" />
            </Button>

            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation();
                console.log('🎮 Timeline play/pause clicked');
                onPlayPause();
              }}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20 transition-all duration-300 hover:scale-110 z-20"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </Button>

            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation();
                console.log('⏩ Frame step forward');
                onFrameStep('forward');
              }}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20 transition-all duration-300 hover:scale-110 z-20"
            >
              <SkipForward className="w-4 h-4" />
            </Button>
          </div>

          <div className="text-white text-sm font-mono bg-black/30 px-3 py-1 rounded-lg backdrop-blur-sm">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>

        {/* Professional Timeline */}
        <div className="relative z-10">
          <div className="text-white text-sm font-medium mb-3 flex items-center">
            <Target className="w-4 h-4 mr-2 text-blue-400" />
            Video Timeline & Ad Placements
          </div>

          {/* Timeline Container */}
          <div
            ref={timelineRef}
            data-testid="video-timeline"
            className="relative h-16 bg-black/40 rounded-lg overflow-hidden cursor-pointer border border-white/20 backdrop-blur-sm hover:border-white/30 transition-all duration-300"
            onMouseDown={(e) => {
              e.preventDefault();
              handleMouseDown(e);
            }}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={() => setIsDragging(false)}
            style={{ userSelect: 'none', touchAction: 'none' }}
          >
            {/* Timeline Background Grid */}
            <div className="absolute inset-0 opacity-30">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className="absolute top-0 bottom-0 w-px bg-white/20"
                  style={{ left: `${(i / 19) * 100}%` }}
                />
              ))}
            </div>

            {/* Ad Markers */}
            {adMarkers.map((marker) => {
              if (duration === 0) return null;

              const startPercent = (marker.startTime / duration) * 100;
              const widthPercent = ((marker.endTime - marker.startTime) / duration) * 100;

              return (
                <div
                  key={marker.id}
                  className="absolute top-2 bottom-2 rounded transition-all duration-300 hover:scale-105 cursor-pointer group"
                  style={{
                    left: `${startPercent}%`,
                    width: `${widthPercent}%`,
                    backgroundColor: marker.color + '80',
                    border: `2px solid ${marker.color}`,
                  }}
                  onMouseEnter={() => setHoveredMarker(marker)}
                  onMouseLeave={() => setHoveredMarker(null)}
                >
                  {/* Marker Icon */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    {marker.type === 'placement' && <Target className="w-3 h-3 text-white" />}
                    {marker.type === 'overlay' && <Zap className="w-3 h-3 text-white" />}
                    {marker.type === 'integration' && <Target className="w-3 h-3 text-white" />}
                  </div>

                  {/* Hover Glow Effect */}
                  <div
                    className="absolute inset-0 rounded opacity-0 group-hover:opacity-50 transition-opacity duration-300"
                    style={{
                      backgroundColor: marker.color,
                      boxShadow: `0 0 20px ${marker.color}80`,
                    }}
                  />
                </div>
              );
            })}

            {/* Progress Bar - BELOW MARKERS */}
            <div
              className="absolute top-0 bottom-0 bg-gradient-to-r from-blue-500 to-purple-500 opacity-80 transition-all duration-100 pointer-events-none z-10"
              style={{ width: `${progressPercentage}%` }}
            />

            {/* Current Time Indicator - MUST BE ON TOP */}
            <div
              className="absolute top-0 bottom-0 w-1 bg-white shadow-lg transition-all duration-100 pointer-events-none z-30"
              style={{ left: `${progressPercentage}%` }}
            >
              <div className="absolute -top-1 -left-1 w-3 h-3 bg-white rounded-full shadow-lg" />
              <div className="absolute -bottom-1 -left-1 w-3 h-3 bg-white rounded-full shadow-lg" />
              {isDragging && (
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-black/90 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                  {formatTime(currentTime)}
                </div>
              )}
            </div>
          </div>

          {/* Frame Information */}
          <div className="mt-3 flex justify-between items-center text-xs text-white/70">
            <span>Frame: {Math.floor(currentTime * 30 + 1)}/{Math.floor(duration * 30)}</span>
            <span>Timecode: {formatTime(currentTime)}</span>
            <span>Frame Rate: 30fps</span>
          </div>

          {/* Precise Frame Scrubbing Controls */}
          <div className="mt-2 flex items-center space-x-2 text-xs">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                const frameTime = 1/30;
                onSeek(Math.max(0, currentTime - frameTime));
              }}
              className="h-6 px-2 bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-xs"
            >
              -1f
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                const frameTime = 1/30;
                onSeek(Math.max(0, currentTime - frameTime * 10));
              }}
              className="h-6 px-2 bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-xs"
            >
              -10f
            </Button>
            <span className="text-white/50 px-2">Frame Precision</span>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                const frameTime = 1/30;
                onSeek(Math.min(duration, currentTime + frameTime * 10));
              }}
              className="h-6 px-2 bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-xs"
            >
              +10f
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                const frameTime = 1/30;
                onSeek(Math.min(duration, currentTime + frameTime));
              }}
              className="h-6 px-2 bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-xs"
            >
              +1f
            </Button>
          </div>
        </div>

        {/* Ad Marker Tooltip */}
        {hoveredMarker && (
          <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-black/90 text-white px-3 py-2 rounded-lg text-xs backdrop-blur-sm border border-white/20">
            <div className="font-medium">{hoveredMarker.name}</div>
            <div className="text-white/70">
              {formatTime(hoveredMarker.startTime)} - {formatTime(hoveredMarker.endTime)}
            </div>
            <div className="capitalize text-white/60">{hoveredMarker.type}</div>
          </div>
        )}
      </div>
    </div>
  );
}

// Add these animations to your global CSS
const animations = `
  @keyframes wave {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-20px); }
  }

  @keyframes float {
    0%, 100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-10px) scale(1.05); }
  }
`;