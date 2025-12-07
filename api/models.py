"""
Data models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from pathlib import Path


class VideoUploadResponse(BaseModel):
    """Response after uploading a video"""
    upload_id: str = Field(..., description="Unique ID for this upload")
    filepath: str = Field(..., description="Server path to the uploaded video")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(default="uploaded", description="Upload status")


class SegmentVideoRequest(BaseModel):
    """Request to segment a video"""
    upload_id: str = Field(..., description="Upload ID from video upload")
    text_prompt: Optional[str] = Field(None, description="Text description of what to segment")
    max_frames: Optional[int] = Field(None, description="Maximum number of frames to process")
    start_frame_idx: Optional[int] = Field(0, description="Starting frame index")
    end_frame_idx: Optional[int] = Field(None, description="Ending frame index")
    output_every_n: int = Field(1, description="Process every N frames")
    save_masks: bool = Field(False, description="Whether to save mask images (default off for bbox workflow)")


class SegmentInfo(BaseModel):
    """Information about a single segment"""
    segment_id: int
    name: str
    bbox: List[float]  # [x1, y1, x2, y2]
    bbox_xywh: List[float]  # [x, y, w, h] convenience for rectangular crops
    area: float
    centroid: List[float]
    score: float
    crop_file: str
    mask_file: Optional[str] = None


class FrameSegmentInfo(BaseModel):
    """Information about segments in a single frame"""
    frame_index: int
    timestamp_ms: float
    num_segments: int
    segments: List[SegmentInfo]


class SegmentVideoResponse(BaseModel):
    """Response after video segmentation"""
    upload_id: str
    run_id: str
    run_dir: str
    video_path: str
    text_prompt: Optional[str]
    total_video_frames: int
    processed_frames: int
    fps: float
    frames: Dict[str, FrameSegmentInfo]
    status: str = "completed"


class EditVideoRequest(BaseModel):
    """Request to edit a segmented video"""
    run_id: str = Field(..., description="Run ID from video segmentation")
    edit_prompt: str = Field(..., description="Edit instruction (e.g., 'add Nike logo')")
    reference_images: Optional[List[str]] = Field(None, description="Paths to reference images")
    start_frame_idx: Optional[int] = Field(None, description="Starting frame index")
    end_frame_idx: Optional[int] = Field(None, description="Ending frame index")
    segment_ids: Optional[List[int]] = Field(None, description="Specific segment IDs to edit")
    model: str = Field("gemini-2.5-flash-image", description="Gemini model to use")
    aspect_ratio: Optional[str] = Field(None, description="Aspect ratio for generated images")
    resolution: str = Field("1K", description="Resolution for generated images")
    reuse_edit_every_n_frames: int = Field(1, description="Reuse edits every N frames")
    max_output_tokens: Optional[int] = Field(
        None, description="Gemini max output tokens for the edit response"
    )
    regenerate_every_n_tokens: Optional[int] = Field(
        None, description="Force regeneration cadence while streaming tokens"
    )
    regenerate_frames: Optional[List[int]] = Field(
        None,
        description="Explicit frame indices that must regenerate a fresh edit (e.g., 0,50 for two keyframes)",
    )


class BoundingBox(BaseModel):
    """User-provided bounding box"""
    x: int = Field(..., description="Top-left X pixel")
    y: int = Field(..., description="Top-left Y pixel")
    w: int = Field(..., description="Box width in pixels")
    h: int = Field(..., description="Box height in pixels")
    segment_id: Optional[int] = Field(None, description="Optional stable ID for the box")
    name: Optional[str] = Field(None, description="Optional label for the box")


class BoundingBoxFrame(BaseModel):
    """Bounding boxes for a specific frame"""
    frame_index: int = Field(..., description="Frame index these boxes belong to")
    boxes: List[BoundingBox] = Field(default_factory=list, description="List of boxes for this frame")


class CreateBoxesRunRequest(BaseModel):
    """Create a run from user-provided bounding boxes (no masks)"""
    upload_id: str = Field(..., description="Upload ID to pull frames from")
    frames: List[BoundingBoxFrame] = Field(..., description="Frames with bounding boxes")
    text_prompt: Optional[str] = Field(None, description="Optional label/intent for the boxes")
    start_frame_idx: Optional[int] = Field(None, description="Optional start frame for interpolation/editing")
    end_frame_idx: Optional[int] = Field(None, description="Optional end frame for interpolation/editing (exclusive)")


class CreateBoxesRunResponse(BaseModel):
    """Response after persisting manual bounding boxes"""
    upload_id: str
    run_id: str
    run_dir: str
    total_video_frames: int
    frames: Dict[str, FrameSegmentInfo]
    status: str = "completed"


class EditVideoResponse(BaseModel):
    """Response after video editing"""
    run_id: str
    upload_id: str
    output_video_path: str
    total_frames: int
    edited_frames: int
    status: str = "completed"


class GetRunInfoRequest(BaseModel):
    """Request to get information about a run"""
    run_id: str = Field(..., description="Run ID to get info for")


class GetRunInfoResponse(BaseModel):
    """Response with run information"""
    run_id: str
    upload_id: str
    run_dir: str
    metadata: Dict[str, Any]
    available_frames: List[int]
    total_segments: int
    status: str


class ListFramesRequest(BaseModel):
    """Request to list frames in a run"""
    run_id: str = Field(..., description="Run ID")
    start_idx: Optional[int] = Field(0, description="Start frame index")
    end_idx: Optional[int] = Field(None, description="End frame index")


class ListFramesResponse(BaseModel):
    """Response with frame listing"""
    run_id: str
    frames: List[FrameSegmentInfo]
    total_frames: int


class GetFrameRequest(BaseModel):
    """Request to get a specific frame's data"""
    run_id: str = Field(..., description="Run ID")
    frame_idx: int = Field(..., description="Frame index")


class GetFrameResponse(BaseModel):
    """Response with frame data"""
    run_id: str
    frame_info: FrameSegmentInfo
    frame_image_path: str
    segment_crops: Dict[int, str]  # segment_id -> crop_path
    segment_masks: Dict[int, str]  # segment_id -> mask_path


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "1.0.0"


class VeoGenerateRequest(BaseModel):
    """Request to generate a video with Veo using first/last frames and prompt"""
    upload_id: str = Field(..., description="Upload ID of the source video")
    start_time: float = Field(..., description="Start time in seconds for the Veo segment")
    end_time: float = Field(..., description="End time in seconds for the Veo segment")
    prompt: str = Field(..., description="Prompt for Veo generation")
    duration: Optional[float] = Field(None, description="Optional duration hint for Veo (seconds)")
    include_original: bool = Field(True, description="Include original pre/post segments")
    fade_duration: float = Field(0.3, description="Fade duration between segments when stitching")
    veo_only: bool = Field(False, description="If true, generate only the Veo segment (no original parts)")


class VeoGenerateResponse(BaseModel):
    """Response after generating a Veo video"""
    upload_id: str
    run_id: str
    output_video_path: str
    status: str = "completed"


class AudioReplacement(BaseModel):
    """Single replacement item from the audio pipeline"""
    timestamp_start: float
    timestamp_end: float
    speaker: str
    original_line: str
    brand_used: str
    new_line: str
    rationale: str


class AudioPipelineRequest(BaseModel):
    """Request to run the audio pipeline on an uploaded video"""
    upload_id: str = Field(..., description="Upload ID for the source video")


class AudioPipelineResponse(BaseModel):
    """Response from the audio pipeline execution"""
    upload_id: str
    run_id: str
    output_video_path: str
    transcript_path: str
    replacements: List[AudioReplacement]
    status: str = "completed"

