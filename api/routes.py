"""
FastAPI routes for video segmentation and editing API
"""

import json
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

from .models import (
    VideoUploadResponse,
    SegmentVideoRequest,
    SegmentVideoResponse,
    EditVideoRequest,
    EditVideoResponse,
    GetRunInfoRequest,
    GetRunInfoResponse,
    ListFramesRequest,
    ListFramesResponse,
    GetFrameRequest,
    GetFrameResponse,
    HealthCheckResponse,
    FrameSegmentInfo,
    SegmentInfo,
    CreateBoxesRunRequest,
    CreateBoxesRunResponse
)
from .storage import storage
from .services import segmentation_service, editing_service


# Create router
router = APIRouter()


def _segment_from_metadata(seg_data: dict) -> SegmentInfo:
    """Normalize persisted segment metadata into SegmentInfo"""
    bbox_xywh = seg_data.get("bbox_xywh")
    if not bbox_xywh and seg_data.get("bbox") and len(seg_data["bbox"]) == 4:
        x1, y1, x2, y2 = seg_data["bbox"]
        bbox_xywh = [x1, y1, x2 - x1, y2 - y1]
    payload = {**seg_data, "bbox_xywh": bbox_xywh}
    # Ensure optional mask presence
    if "mask_file" not in payload:
        payload["mask_file"] = None
    return SegmentInfo(**payload)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(status="healthy", version="1.0.0")


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file for processing
    
    Args:
        file: Video file to upload
        
    Returns:
        Upload information including unique upload_id
    """
    try:
        # Read file data
        file_data = await file.read()
        
        # Save to storage
        upload_id, filepath = storage.save_upload(file_data, file.filename)
        
        return VideoUploadResponse(
            upload_id=upload_id,
            filepath=str(filepath),
            filename=file.filename,
            file_size=len(file_data),
            status="uploaded"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/upload/info")
async def get_upload_info(upload_id: str):
    """
    Get information about an uploaded video (frame count, fps, dimensions)
    
    Args:
        upload_id: Upload ID (query parameter)
        
    Returns:
        Video metadata
    """
    try:
        upload_path = storage.get_upload_path(upload_id)
        if not upload_path:
            raise HTTPException(status_code=404, detail=f"Upload not found: {upload_id}")
        
        # Open video to get metadata
        import cv2
        cap = cv2.VideoCapture(str(upload_path))
        
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video file")
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return JSONResponse(content={
            "upload_id": upload_id,
            "frame_count": frame_count,
            "fps": fps,
            "width": width,
            "height": height,
            "duration_seconds": duration
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video info: {str(e)}")


@router.get("/upload/{upload_id}/frame/{frame_idx}")
async def get_upload_frame(upload_id: str, frame_idx: int):
    """
    Get a specific frame from an uploaded video as JPEG
    
    Args:
        upload_id: Upload ID
        frame_idx: Frame index (0-based)
        
    Returns:
        Frame image as JPEG
    """
    try:
        upload_path = storage.get_upload_path(upload_id)
        if not upload_path:
            raise HTTPException(status_code=404, detail=f"Upload not found: {upload_id}")
        
        import cv2
        import tempfile
        import os
        
        cap = cv2.VideoCapture(str(upload_path))
        
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video file")
        
        # Seek to frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise HTTPException(status_code=404, detail=f"Frame {frame_idx} not found")
        
        # Save frame to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        cv2.imwrite(temp_file.name, frame)
        temp_file.close()
        
        # Return file and schedule deletion
        def cleanup():
            try:
                os.unlink(temp_file.name)
            except:
                pass
        
        return FileResponse(
            path=temp_file.name,
            media_type="image/jpeg",
            filename=f"frame_{frame_idx:06d}.jpg",
            background=BackgroundTasks().add_task(cleanup)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get frame: {str(e)}")


@router.post("/segment", response_model=SegmentVideoResponse)
async def segment_video(request: SegmentVideoRequest, background_tasks: BackgroundTasks):
    """
    Segment objects in an uploaded video
    
    Args:
        request: Segmentation request with upload_id and parameters
        
    Returns:
        Segmentation results with run_id
    """
    try:
        # Get upload path
        upload_path = storage.get_upload_path(request.upload_id)
        if not upload_path:
            raise HTTPException(status_code=404, detail=f"Upload not found: {request.upload_id}")
        
        # Create run directory
        run_id, run_dir = storage.create_run_dir(request.upload_id)
        
        # Run segmentation
        metadata = segmentation_service.segment_video(
            video_path=str(upload_path),
            run_dir=str(run_dir),
            text_prompt=request.text_prompt,
            start_frame_idx=request.start_frame_idx or 0,
            end_frame_idx=request.end_frame_idx,
            max_frames=request.max_frames,
            output_every_n=request.output_every_n,
            save_masks=request.save_masks
        )
        
        # Convert metadata to response format
        frames_response = {}
        for frame_idx_key, frame_data in metadata['frames'].items():
            # Ensure key is a string for Pydantic validation
            frame_idx_str = str(frame_idx_key)
            segments = [
                _segment_from_metadata(seg_data) for seg_data in frame_data['segments']
            ]
            frames_response[frame_idx_str] = FrameSegmentInfo(
                frame_index=frame_data['frame_index'],
                timestamp_ms=frame_data['timestamp_ms'],
                num_segments=frame_data['num_segments'],
                segments=segments
            )
        
        return SegmentVideoResponse(
            upload_id=request.upload_id,
            run_id=run_id,
            run_dir=str(run_dir),
            video_path=metadata['video_path'],
            text_prompt=metadata['text_prompt'],
            total_video_frames=metadata['total_video_frames'],
            processed_frames=metadata['processed_frames'],
            fps=metadata['fps'],
            frames=frames_response,
            status="completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")


@router.post("/boxes/manual", response_model=CreateBoxesRunResponse)
async def create_boxes_run(request: CreateBoxesRunRequest):
    """
    Create a segmentation run from user-provided bounding boxes (no masks).
    """
    try:
        upload_path = storage.get_upload_path(request.upload_id)
        if not upload_path:
            raise HTTPException(status_code=404, detail=f"Upload not found: {request.upload_id}")

        run_id, run_dir = storage.create_run_dir(request.upload_id)

        metadata = segmentation_service.create_run_from_boxes(
            video_path=str(upload_path),
            run_dir=str(run_dir),
            frames=[frame.dict() for frame in request.frames],
            text_prompt=request.text_prompt,
            start_frame_idx=request.start_frame_idx,
            end_frame_idx=request.end_frame_idx,
        )

        frames_response: Dict[str, FrameSegmentInfo] = {}
        for frame_idx_key, frame_data in metadata["frames"].items():
            frame_idx_str = str(frame_idx_key)
            segments = [_segment_from_metadata(seg_data) for seg_data in frame_data["segments"]]
            frames_response[frame_idx_str] = FrameSegmentInfo(
                frame_index=frame_data["frame_index"],
                timestamp_ms=frame_data["timestamp_ms"],
                num_segments=frame_data["num_segments"],
                segments=segments,
            )

        return CreateBoxesRunResponse(
            upload_id=request.upload_id,
            run_id=run_id,
            run_dir=str(run_dir),
            total_video_frames=metadata.get("total_video_frames", 0),
            frames=frames_response,
            status="completed",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save bounding boxes: {str(e)}")


@router.post("/edit", response_model=EditVideoResponse)
async def edit_video(request: EditVideoRequest, background_tasks: BackgroundTasks):
    """
    Edit tracked objects in a segmented video
    
    Args:
        request: Edit request with run_id and parameters
        
    Returns:
        Edited video information
    """
    try:
        # Get run directory
        run_dir = storage.get_run_dir(request.run_id)
        if not run_dir:
            raise HTTPException(status_code=404, detail=f"Run not found: {request.run_id}")
        
        # Get upload_id for this run
        upload_id = storage.get_upload_id_for_run(request.run_id)
        
        # Run editing
        output_path = editing_service.edit_video(
            run_dir=str(run_dir),
            edit_prompt=request.edit_prompt,
            reference_images=request.reference_images,
            start_frame_idx=request.start_frame_idx,
            end_frame_idx=request.end_frame_idx,
            segment_ids=request.segment_ids,
            model=request.model,
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
            reuse_edit_every_n_frames=request.reuse_edit_every_n_frames
        )
        
        # Load metadata to get frame counts
        metadata_path = storage.get_metadata_path(request.run_id)
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return EditVideoResponse(
            run_id=request.run_id,
            upload_id=upload_id or request.run_id,
            output_video_path=output_path,
            total_frames=metadata.get('total_video_frames', 0),
            edited_frames=metadata.get('processed_frames', 0),
            status="completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Editing failed: {str(e)}")


@router.post("/run/info", response_model=GetRunInfoResponse)
async def get_run_info(request: GetRunInfoRequest):
    """
    Get information about a processing run
    
    Args:
        request: Request with run_id
        
    Returns:
        Run information including metadata
    """
    try:
        # Get run directory
        run_dir = storage.get_run_dir(request.run_id)
        if not run_dir:
            raise HTTPException(status_code=404, detail=f"Run not found: {request.run_id}")
        
        # Load metadata
        metadata_path = storage.get_metadata_path(request.run_id)
        if not metadata_path:
            raise HTTPException(status_code=404, detail=f"Metadata not found for run: {request.run_id}")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Get upload_id
        upload_id = storage.get_upload_id_for_run(request.run_id)
        
        # Get available frames
        available_frames = [int(k) for k in metadata['frames'].keys()]
        
        # Count total segments
        total_segments = sum(
            len(frame_data['segments']) 
            for frame_data in metadata['frames'].values()
        )
        
        return GetRunInfoResponse(
            run_id=request.run_id,
            upload_id=upload_id or request.run_id,
            run_dir=str(run_dir),
            metadata=metadata,
            available_frames=sorted(available_frames),
            total_segments=total_segments,
            status="completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get run info: {str(e)}")


@router.post("/run/frames", response_model=ListFramesResponse)
async def list_frames(request: ListFramesRequest):
    """
    List frames in a run with optional range filtering
    
    Args:
        request: Request with run_id and optional frame range
        
    Returns:
        List of frames with segment information
    """
    try:
        # Get run directory
        run_dir = storage.get_run_dir(request.run_id)
        if not run_dir:
            raise HTTPException(status_code=404, detail=f"Run not found: {request.run_id}")
        
        # Load metadata
        metadata_path = storage.get_metadata_path(request.run_id)
        if not metadata_path:
            raise HTTPException(status_code=404, detail=f"Metadata not found for run: {request.run_id}")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Filter frames by range
        frames_list = []
        for frame_idx_str, frame_data in metadata['frames'].items():
            frame_idx = int(frame_idx_str)
            
            # Apply range filter
            if request.start_idx is not None and frame_idx < request.start_idx:
                continue
            if request.end_idx is not None and frame_idx >= request.end_idx:
                continue
            
            # Convert to response format
            segments = [
                _segment_from_metadata(seg_data) for seg_data in frame_data['segments']
            ]
            frame_info = FrameSegmentInfo(
                frame_index=frame_data['frame_index'],
                timestamp_ms=frame_data['timestamp_ms'],
                num_segments=frame_data['num_segments'],
                segments=segments
            )
            frames_list.append(frame_info)
        
        # Sort by frame index
        frames_list.sort(key=lambda x: x.frame_index)
        
        return ListFramesResponse(
            run_id=request.run_id,
            frames=frames_list,
            total_frames=len(frames_list)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list frames: {str(e)}")


@router.post("/run/frame", response_model=GetFrameResponse)
async def get_frame(request: GetFrameRequest):
    """
    Get detailed information about a specific frame
    
    Args:
        request: Request with run_id and frame_idx
        
    Returns:
        Frame information with file paths
    """
    try:
        # Get frame directory
        frame_dir = storage.get_frame_dir(request.run_id, request.frame_idx)
        if not frame_dir:
            raise HTTPException(
                status_code=404, 
                detail=f"Frame {request.frame_idx} not found in run: {request.run_id}"
            )
        
        # Load metadata
        metadata_path = storage.get_metadata_path(request.run_id)
        if not metadata_path:
            raise HTTPException(status_code=404, detail=f"Metadata not found for run: {request.run_id}")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Get frame data
        frame_data = metadata['frames'].get(str(request.frame_idx))
        if not frame_data:
            raise HTTPException(
                status_code=404,
                detail=f"Frame {request.frame_idx} not in metadata"
            )
        
        # Build response
        segments = [
            _segment_from_metadata(seg_data) for seg_data in frame_data['segments']
        ]
        frame_info = FrameSegmentInfo(
            frame_index=frame_data['frame_index'],
            timestamp_ms=frame_data['timestamp_ms'],
            num_segments=frame_data['num_segments'],
            segments=segments
        )
        
        # Build file paths
        frame_image_path = str(frame_dir / "frame.png")
        segment_crops = {}
        segment_masks = {}
        
        for seg_data in frame_data['segments']:
            seg_id = seg_data['segment_id']
            if seg_data['crop_file']:
                segment_crops[seg_id] = str(frame_dir / seg_data['crop_file'])
            if seg_data.get('mask_file'):
                segment_masks[seg_id] = str(frame_dir / seg_data['mask_file'])
        
        return GetFrameResponse(
            run_id=request.run_id,
            frame_info=frame_info,
            frame_image_path=frame_image_path,
            segment_crops=segment_crops,
            segment_masks=segment_masks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get frame: {str(e)}")


@router.get("/download/video/{run_id}")
async def download_video(run_id: str):
    """
    Download the edited video for a run
    
    Args:
        run_id: Run ID
        
    Returns:
        Video file
    """
    try:
        # Get run directory
        run_dir = storage.get_run_dir(run_id)
        if not run_dir:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
        
        # Check for edited video
        video_path = run_dir / "edited_video.mp4"
        if not video_path.exists():
            raise HTTPException(status_code=404, detail=f"Edited video not found for run: {run_id}")
        
        return FileResponse(
            path=str(video_path),
            media_type="video/mp4",
            filename=f"{run_id}_edited.mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/download/frame/{run_id}/{frame_idx}")
async def download_frame(run_id: str, frame_idx: int):
    """
    Download the original frame image
    
    Args:
        run_id: Run ID
        frame_idx: Frame index
        
    Returns:
        Frame image file
    """
    try:
        # Get frame directory
        frame_dir = storage.get_frame_dir(run_id, frame_idx)
        if not frame_dir:
            raise HTTPException(
                status_code=404,
                detail=f"Frame {frame_idx} not found in run: {run_id}"
            )
        
        # Get frame image
        frame_path = frame_dir / "frame.png"
        if not frame_path.exists():
            raise HTTPException(status_code=404, detail=f"Frame image not found")
        
        return FileResponse(
            path=str(frame_path),
            media_type="image/png",
            filename=f"frame_{frame_idx:06d}.png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/download/segment/{run_id}/{frame_idx}/{segment_id}")
async def download_segment(run_id: str, frame_idx: int, segment_id: int, type: str = "crop"):
    """
    Download a segment crop or mask
    
    Args:
        run_id: Run ID
        frame_idx: Frame index
        segment_id: Segment ID
        type: "crop" or "mask"
        
    Returns:
        Segment image file
    """
    try:
        # Get frame directory
        frame_dir = storage.get_frame_dir(run_id, frame_idx)
        if not frame_dir:
            raise HTTPException(
                status_code=404,
                detail=f"Frame {frame_idx} not found in run: {run_id}"
            )
        
        # Get segment file
        if type == "crop":
            segment_path = frame_dir / f"segment_{segment_id}_crop.png"
        elif type == "mask":
            segment_path = frame_dir / f"segment_{segment_id}_mask.png"
        else:
            raise HTTPException(status_code=400, detail="Type must be 'crop' or 'mask'")
        
        if not segment_path.exists():
            raise HTTPException(status_code=404, detail=f"Segment {type} not found")
        
        return FileResponse(
            path=str(segment_path),
            media_type="image/png",
            filename=f"segment_{segment_id}_{type}.png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/runs")
async def list_runs(include_metadata: bool = False):
    """
    List all available runs with optional metadata
    
    Args:
        include_metadata: If true, includes full metadata for each run
    
    Returns:
        List of run IDs with optional metadata
    """
    try:
        runs = storage.list_runs()
        
        if not include_metadata:
            return JSONResponse(content={"runs": runs, "total": len(runs)})
        
        # Include metadata for each run
        runs_with_metadata = []
        for run_id in runs:
            run_dir = storage.get_run_dir(run_id)
            if not run_dir:
                continue
            
            metadata_path = storage.get_metadata_path(run_id)
            if not metadata_path or not metadata_path.exists():
                # Run without metadata
                runs_with_metadata.append({
                    "run_id": run_id,
                    "has_metadata": False,
                    "run_dir": str(run_dir)
                })
                continue
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Check for edited video
            has_edited_video = (run_dir / "edited_video.mp4").exists()
            
            # Get frame count
            available_frames = sorted([int(k) for k in metadata.get('frames', {}).keys()])
            
            runs_with_metadata.append({
                "run_id": run_id,
                "has_metadata": True,
                "run_dir": str(run_dir),
                "video_path": metadata.get('video_path'),
                "text_prompt": metadata.get('text_prompt'),
                "total_video_frames": metadata.get('total_video_frames'),
                "processed_frames": metadata.get('processed_frames'),
                "start_frame_idx": metadata.get('start_frame_idx', 0),
                "end_frame_idx": metadata.get('end_frame_idx'),
                "fps": metadata.get('fps'),
                "has_edited_video": has_edited_video,
                "available_frames": available_frames[:10] if len(available_frames) > 10 else available_frames,  # Limit to first 10
                "total_available_frames": len(available_frames)
            })
        
        return JSONResponse(content={
            "runs": runs_with_metadata,
            "total": len(runs_with_metadata)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")


@router.get("/runs/{run_id}/preview/{frame_idx}")
async def get_run_frame_preview(run_id: str, frame_idx: int):
    """
    Get a preview of a specific frame from a run
    
    Args:
        run_id: Run ID
        frame_idx: Frame index
        
    Returns:
        Frame image
    """
    try:
        frame_dir = storage.get_frame_dir(run_id, frame_idx)
        if not frame_dir:
            raise HTTPException(
                status_code=404,
                detail=f"Frame {frame_idx} not found in run: {run_id}"
            )
        
        frame_path = frame_dir / "frame.png"
        if not frame_path.exists():
            raise HTTPException(status_code=404, detail="Frame image not found")
        
        return FileResponse(
            path=str(frame_path),
            media_type="image/png",
            filename=f"preview_{run_id}_{frame_idx}.png"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preview: {str(e)}")

