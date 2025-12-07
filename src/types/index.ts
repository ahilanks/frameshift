export interface UserPreferences {
  likes: string[];
  audience: string[];
  targetDemographic?: string;
  brandCategories?: string[];
  brandImage?: File;
  brandImageUrl?: string;
  selectedProducts?: ProductPlacement[];
}

export interface ProductPlacement {
  id: string;
  name: string;
  description: string;
  category: string;
  imageUrl?: string;
}

export interface VideoFile {
  file: File;
  duration: number;
  size: number;
  url: string;
  frameCount?: number;
  currentFrame?: number;
}

export interface TimeRange {
  start: number;
  end: number;
}

export interface AnalysisResult {
  grokContext?: string;
  suggestedTimeRanges: TimeRange[];
  sceneDescription: string;
  confidence: number;
}

export interface ProcessingJob {
  id: string;
  status: 'processing' | 'completed' | 'failed';
  originalVideo: string;
  editedVideo?: string;
  product: ProductPlacement;
  timeRange: TimeRange;
  preferences: UserPreferences;
  metrics?: VideoMetrics;
  createdAt: Date;
}

export interface VideoMetrics {
  exposureDuration: number;
  visibilityPercentage: number;
  sceneModified: string;
  totalDuration: number;
}