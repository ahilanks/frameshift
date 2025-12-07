"""
Core service functions for video segmentation and editing
"""

import sys
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import cv2
import numpy as np
from PIL import Image

# Add parent directory to path to import local modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sam import SAM3VideoSegmenter
from video_edit_tracked import (
    edit_video_with_tracked_object,
    load_image_with_alpha,
    apply_mask_to_image,
    composite_on_frame
)
from create_veo_video_enhanced import VeoVideoGenerator


class VideoSegmentationService:
    """Service for video segmentation operations"""
    
    def __init__(self):
        self.segmenter = None
    
    def _get_segmenter(self):
        """Lazy load the segmenter"""
        if self.segmenter is None:
            self.segmenter = SAM3VideoSegmenter()
        return self.segmenter
    
    def segment_video(
        self,
        video_path: str,
        run_dir: str,
        text_prompt: Optional[str] = None,
        start_frame_idx: int = 0,
        end_frame_idx: Optional[int] = None,
        max_frames: Optional[int] = None,
        output_every_n: int = 1,
        save_masks: bool = False
    ) -> Dict[str, Any]:
        """
        Segment objects in a video and save outputs frame by frame.
        
        Args:
            video_path: Path to video file
            run_dir: Directory to save outputs
            text_prompt: Text description of what to segment
            start_frame_idx: Starting frame index (0-based)
            end_frame_idx: Ending frame index (None = until max_frames or end)
            max_frames: Maximum number of frames to process from start
            output_every_n: Save results every N frames
            save_masks: Whether to save mask images alongside crops
            
        Returns:
            Dictionary with segmentation results and metadata
        """
        segmenter = self._get_segmenter()
        
        print(f"\n{'='*60}")
        print(f"Video Segmentation Started")
        print(f"{'='*60}")
        print(f"Video: {video_path}")
        print(f"Prompt: {text_prompt or 'automatic'}")
        print(f"Start frame: {start_frame_idx}")
        print(f"End frame: {end_frame_idx or 'auto'}")
        print(f"Max frames: {max_frames or 'all'}")
        print(f"{'='*60}\n")
        
        # Load video to determine frame range
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        # Determine actual end frame
        actual_end_frame = end_frame_idx if end_frame_idx is not None else total_frames
        if max_frames:
            actual_end_frame = min(start_frame_idx + max_frames, actual_end_frame)
        
        # If we need a specific frame range, extract those frames to a temporary video
        if start_frame_idx > 0 or actual_end_frame < total_frames:
            import tempfile
            import os
            
            print(f"📹 Extracting frames {start_frame_idx} to {actual_end_frame}...")
            
            # Create temporary video with only the selected frame range
            temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_video_path = temp_video.name
            temp_video.close()
            
            cap = cv2.VideoCapture(video_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
            
            # Skip to start frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_idx)
            
            # Write selected frames
            for i in range(start_frame_idx, actual_end_frame):
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
            
            cap.release()
            out.release()
            
            # Use temporary video for segmentation
            segmentation_video_path = temp_video_path
            frames_in_range = actual_end_frame - start_frame_idx
            
            # Adjust max_frames for the extracted video
            adjusted_max_frames = max_frames if max_frames and max_frames < frames_in_range else None
        else:
            segmentation_video_path = video_path
            adjusted_max_frames = max_frames
        
        # Run video segmentation on the (possibly extracted) video
        result = segmenter.segment_video_with_text(
            segmentation_video_path,
            text_prompt=text_prompt or "objects",
            max_frames=adjusted_max_frames,
            output_every_n=output_every_n
        )
        
        # Clean up temporary video if created
        if segmentation_video_path != video_path:
            try:
                os.unlink(segmentation_video_path)
            except:
                pass
        
        print(f"\n✅ Found segments in {len(result.frames)} frames\n")
        
        # Create run directory
        run_path = Path(run_dir)
        run_path.mkdir(parents=True, exist_ok=True)
        
        # Load original video to extract frames
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Collect metadata for all frames
        video_metadata = {
            "video_path": video_path,
            "text_prompt": text_prompt,
            "total_video_frames": total_frames,
            "processed_frames": len(result.frames),
            "start_frame_idx": start_frame_idx,
            "end_frame_idx": actual_end_frame,
            "fps": fps,
            "frames": {}
        }
        
        # Process each frame with segments
        # Note: result.frames has indices starting from 0, but they represent frames starting at start_frame_idx
        for result_frame_idx in sorted(result.frames.keys()):
            # Map result frame index to actual video frame index
            actual_frame_idx = start_frame_idx + result_frame_idx
            
            frame_result = result.frames[result_frame_idx]
            
            # Read the specific frame from original video
            cap.set(cv2.CAP_PROP_POS_FRAMES, actual_frame_idx)
            ret, frame_bgr = cap.read()
            if not ret:
                print(f"⚠️  Could not read frame {actual_frame_idx}")
                continue
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            frame_image = Image.fromarray(frame_rgb)
            
            # Create frame directory using actual frame index
            frame_dir = run_path / f"frame_{actual_frame_idx:06d}"
            frame_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"Frame {actual_frame_idx} ({result_frame_idx + 1}/{len(result.frames)}):")
            print(f"  Segments found: {len(frame_result.segments)}")
            
            frame_metadata = {
                "frame_index": actual_frame_idx,
                "timestamp_ms": (actual_frame_idx / fps * 1000) if fps > 0 else 0,
                "num_segments": len(frame_result.segments),
                "segments": []
            }
            
            # Save each segment
            for segment in frame_result.segments:
                print(f"  Segment {segment.segment_id}:")
                print(f"    BBox: {segment.bbox}")
                print(f"    Area: {segment.area:.0f} px")
                print(f"    Score: {segment.score:.3f}")
                
                x1, y1, x2, y2 = [int(coord) for coord in segment.bbox]
                bbox_xywh = [x1, y1, max(0, x2 - x1), max(0, y2 - y1)]
                
                # Crop the segment
                cropped = frame_image.crop((x1, y1, x2, y2))
                
                output_name = f"segment_{segment.segment_id}_crop.png"
                output_path = frame_dir / output_name
                cropped.save(output_path)
                print(f"    Saved crop: {output_path}")
                
                # Optionally save mask
                mask_name = None
                if save_masks:
                    mask = frame_result.masks[segment.mask_index]
                    mask_cropped = mask[y1:y2, x1:x2]
                    mask_image = Image.fromarray((mask_cropped * 255).astype(np.uint8))
                    mask_name = f"segment_{segment.segment_id}_mask.png"
                    mask_path = frame_dir / mask_name
                    mask_image.save(mask_path)
                    print(f"    Saved mask: {mask_path}")
                
                # Add to metadata
                frame_metadata["segments"].append({
                    "segment_id": segment.segment_id,
                    "name": segment.name,
                    "bbox": segment.bbox,
                    "bbox_xywh": bbox_xywh,
                    "area": float(segment.area),
                    "centroid": list(segment.centroid),
                    "score": float(segment.score),
                    "crop_file": output_name,
                    "mask_file": mask_name
                })
            
            print()
            
            # Save per-frame metadata using actual frame index
            video_metadata["frames"][actual_frame_idx] = frame_metadata
            
            # Save frame image for reference
            frame_path = frame_dir / "frame.png"
            frame_image.save(frame_path)
        
        cap.release()
        
        # Save overall metadata JSON
        metadata_path = run_path / "video_segments_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(video_metadata, f, indent=4)
        
        print(f"{'='*60}")
        print(f"✅ Video segmentation complete!")
        print(f"{'='*60}")
        print(f"Processed: {len(result.frames)} frames")
        print(f"Output directory: {run_dir}")
        print(f"Metadata file: {metadata_path}")
        print(f"{'='*60}\n")
        
        return video_metadata

    def create_run_from_boxes(
        self,
        video_path: str,
        run_dir: str,
        frames: List[Dict[str, Any]],
        text_prompt: Optional[str] = None,
        start_frame_idx: Optional[int] = None,
        end_frame_idx: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Persist user-provided bounding boxes as a run (no masks, rectangular crops only).
        Frames input format: [{"frame_index": int, "boxes": [{"x":..., "y":..., "w":..., "h":..., "segment_id":?, "name":?}, ...]}, ...]
        """
        import cv2

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames_full = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        start_idx = start_frame_idx or 0
        end_idx_effective = end_frame_idx if end_frame_idx is not None else total_frames_full
        end_idx_effective = min(end_idx_effective, total_frames_full)
        total_frames = max(0, end_idx_effective - start_idx)

        run_path = Path(run_dir)
        run_path.mkdir(parents=True, exist_ok=True)

        video_metadata: Dict[str, Any] = {
            "video_path": video_path,
            "text_prompt": text_prompt or "manual_boxes",
            "mode": "manual_boxes",
            "total_video_frames": total_frames_full,
            "processed_frames": len(frames),
            "start_frame_idx": start_idx,
            "end_frame_idx": end_idx_effective,
            "fps": fps,
            "frames": {},
        }

        for frame_entry in frames:
            frame_idx = int(frame_entry.get("frame_index", 0))
            if frame_idx < start_idx or frame_idx >= end_idx_effective:
                continue
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame_bgr = cap.read()
            if not ret:
                print(f"⚠️  Could not read frame {frame_idx}, skipping")
                continue

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            frame_image = Image.fromarray(frame_rgb)
            frame_dir = run_path / f"frame_{frame_idx:06d}"
            frame_dir.mkdir(parents=True, exist_ok=True)

            frame_metadata = {
                "frame_index": frame_idx,
                "timestamp_ms": (frame_idx / fps * 1000) if fps > 0 else 0,
                "num_segments": len(frame_entry.get("boxes", [])),
                "segments": [],
            }

            for i, box in enumerate(frame_entry.get("boxes", [])):
                x = int(box.get("x", 0))
                y = int(box.get("y", 0))
                w = int(box.get("w", 0))
                h = int(box.get("h", 0))
                seg_id = int(box["segment_id"]) if box.get("segment_id") is not None else i
                name = box.get("name") or f"box_{seg_id}"

                x1, y1, x2, y2 = x, y, x + w, y + h

                crop = frame_image.crop((x1, y1, x2, y2))
                output_name = f"segment_{seg_id}_crop.png"
                output_path = frame_dir / output_name
                crop.save(output_path)

                frame_metadata["segments"].append(
                    {
                        "segment_id": seg_id,
                        "name": name,
                        "bbox": [x1, y1, x2, y2],
                        "bbox_xywh": [x, y, w, h],
                        "area": float(max(w, 0) * max(h, 0)),
                        "centroid": [x + w / 2.0, y + h / 2.0],
                        "score": 1.0,
                        "crop_file": output_name,
                        "mask_file": None,
                    }
                )

            # Save frame image for reference
            frame_image.save(frame_dir / "frame.png")
            video_metadata["frames"][frame_idx] = frame_metadata

        cap.release()

        metadata_path = run_path / "video_segments_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(video_metadata, f, indent=4)

        return video_metadata


class VideoEditingService:
    """Service for video editing operations"""
    
    def edit_video(
        self,
        run_dir: str,
        edit_prompt: str,
        reference_images: Optional[List[str]] = None,
        start_frame_idx: Optional[int] = None,
        end_frame_idx: Optional[int] = None,
        segment_ids: Optional[List[int]] = None,
        model: str = "gemini-2.5-flash-image",
        aspect_ratio: Optional[str] = None,
        resolution: str = "1K",
        reuse_edit_every_n_frames: int = 1,
        max_output_tokens: Optional[int] = None,
        regenerate_every_n_tokens: Optional[int] = None,
        regenerate_frames: Optional[List[int]] = None,
    ) -> str:
        """
        Edit tracked objects in a video using Gemini image editing.
        
        Args:
            run_dir: Path to the video segmentation run directory
            edit_prompt: Text prompt for editing
            reference_images: List of paths to reference images
            start_frame_idx: Starting frame index (None = from beginning)
            end_frame_idx: Ending frame index (None = until end)
            segment_ids: List of segment IDs to edit (None = all segments)
            model: Gemini model to use for editing
            aspect_ratio: Aspect ratio for generated images
            resolution: Resolution for generated images
            reuse_edit_every_n_frames: Edit once every N frames
            
        Returns:
            Path to the output video file
        """
        run_path = Path(run_dir)
        
        # Load metadata to determine frame range
        metadata_path = run_path / "video_segments_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Determine max_frames based on start/end frame indices
        max_frames = None
        if start_frame_idx is not None or end_frame_idx is not None:
            start = start_frame_idx or 0
            end = end_frame_idx or metadata['total_video_frames']
            max_frames = end - start
        
        # Call the existing edit function
        output_path = edit_video_with_tracked_object(
            run_dir=run_dir,
            edit_prompt=edit_prompt,
            output_path=None,  # Will default to run_dir/edited_video.mp4
            model=model,
            reference_images=reference_images,
            max_frames=max_frames,
            start_frame_idx=start_frame_idx,
            end_frame_idx=end_frame_idx,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            segment_ids=segment_ids,
            reuse_edit_every_n_frames=reuse_edit_every_n_frames,
            max_output_tokens=max_output_tokens,
            regenerate_every_n_tokens=regenerate_every_n_tokens,
            regenerate_frames=regenerate_frames,
        )
        
        return str(output_path)


class VeoGenerationService:
    """Service for Veo-based video generation using first/last frames."""

    def __init__(self):
        self._generator: Optional[VeoVideoGenerator] = None

    def _get_generator(self) -> VeoVideoGenerator:
        if self._generator is not None:
            return self._generator
        api_key = (
            os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("VEO_API_KEY")
        )
        if not api_key:
            raise ValueError("Veo/Gemini API key not found. Set GOOGLE_API_KEY, GEMINI_API_KEY, or VEO_API_KEY.")
        self._generator = VeoVideoGenerator(api_key)
        return self._generator

    def generate_from_upload(
        self,
        upload_path: str,
        run_dir: Path,
        start_time: float,
        end_time: float,
        prompt: str,
        duration: Optional[float] = None,
        include_original: bool = True,
        fade_duration: float = 0.3,
        veo_only: bool = False,
    ) -> str:
        generator = self._get_generator()
        run_dir.mkdir(parents=True, exist_ok=True)
        output_path = run_dir / "veo_video.mp4"

        # If include_original is requested, leverage the enhanced sequence helper
        if include_original and not veo_only:
            return generator.create_enhanced_sequence(
                input_video=upload_path,
                start_time=start_time,
                end_time=end_time,
                prompt=prompt,
                output_path=str(output_path),
                include_original=True,
                fade_duration=fade_duration,
            )

        # Otherwise, just generate the Veo segment using start/end frames
        start_frame = generator.extract_frame_at_time(upload_path, start_time)
        end_frame = generator.extract_frame_at_time(upload_path, end_time)
        try:
            enhanced_prompt = generator.create_consistency_prompt(prompt)
            return generator.generate_video(
                start_frame_path=start_frame,
                end_frame_path=end_frame,
                prompt=enhanced_prompt,
                output_path=str(output_path),
                duration=duration,
            )
        finally:
            for temp_frame in (start_frame, end_frame):
                try:
                    if temp_frame and os.path.exists(temp_frame):
                        os.unlink(temp_frame)
                except:
                    pass


class AudioPipelineService:
    """Service wrapper for the audio pipeline."""

    def __init__(self):
        self._pipeline = None
        self._audio_dir = Path(__file__).parent.parent / "audio"

    def _get_pipeline(self):
        """Lazy load the audio pipeline module."""
        if self._pipeline is not None:
            return self._pipeline
        if str(self._audio_dir) not in sys.path:
            sys.path.insert(0, str(self._audio_dir))
        import pipeline as audio_pipeline  # type: ignore
        self._pipeline = audio_pipeline
        return self._pipeline

    def run_pipeline(self, video_path: str, run_dir: str) -> Dict[str, Any]:
        """Execute the audio pipeline and persist metadata in the run directory."""
        pipeline_module = self._get_pipeline()
        artifacts_dir = Path(run_dir) / "audio_artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        result = pipeline_module.run_pipeline(
            input_video_path=video_path,
            output_dir=str(Path(run_dir)),
            artifacts_dir=str(artifacts_dir),
        ) or {}

        metadata = {
            "video_path": video_path,
            "artifacts_dir": str(artifacts_dir),
            "replacements": result.get("replacements", []),
            "transcript_json": result.get("transcript_json"),
            "analysis_path": result.get("analysis_path"),
            "final_video": result.get("final_video"),
        }

        metadata_path = Path(run_dir) / "audio_pipeline_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)

        return metadata


# Global service instances
segmentation_service = VideoSegmentationService()
editing_service = VideoEditingService()
veo_service = VeoGenerationService()
audio_pipeline_service = AudioPipelineService()

