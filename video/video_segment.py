import sys
import os
import uuid
import json
from pathlib import Path

sys.path.append('.')

from sam import SAM3VideoSegmenter
from PIL import Image
import numpy as np
import cv2


def segment_video(video_path, text_prompt=None, max_frames=None, output_every_n=1, save_masks=False):
    """
    Segment objects in a video and save outputs frame by frame.
    
    Args:
        video_path: Path to video file (e.g., media/scene.mp4)
        text_prompt: Text description of what to segment (e.g., "person", "logo")
        max_frames: Maximum number of frames to process (None = all)
        output_every_n: Save results every N frames
        save_masks: Whether to save mask images alongside crops
    """
    segmenter = SAM3VideoSegmenter()
    
    # Run video segmentation
    print(f"\n{'='*60}")
    print(f"Video Segmentation Started")
    print(f"{'='*60}")
    print(f"Video: {video_path}")
    print(f"Prompt: {text_prompt or 'automatic'}")
    print(f"Max frames: {max_frames or 'all'}")
    print(f"{'='*60}\n")
    
    result = segmenter.segment_video_with_text(
        video_path,
        text_prompt=text_prompt or "objects",
        max_frames=max_frames,
        output_every_n=output_every_n
    )
    
    print(f"\n✅ Found segments in {len(result.frames)} frames\n")
    
    # Base folder for all video segment runs
    base_dir = "video_segments"
    os.makedirs(base_dir, exist_ok=True)
    
    # Create a random subfolder for this run
    run_id = uuid.uuid4().hex[:8]
    run_dir = os.path.join(base_dir, f"run_{run_id}")
    os.makedirs(run_dir, exist_ok=True)
    
    print(f"Saving outputs in: {run_dir}\n")
    
    # Load video to extract frames
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Collect metadata for all frames
    video_metadata = {
        "video_path": video_path,
        "text_prompt": text_prompt,
        "total_video_frames": total_frames,
        "processed_frames": len(result.frames),
        "fps": fps,
        "frames": {}
    }
    
    # Process each frame with segments
    for frame_idx in sorted(result.frames.keys()):
        frame_result = result.frames[frame_idx]
        
        # Read the specific frame from video
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame_bgr = cap.read()
        if not ret:
            print(f"⚠️  Could not read frame {frame_idx}")
            continue
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_image = Image.fromarray(frame_rgb)
        
        # Create frame directory
        frame_dir = os.path.join(run_dir, f"frame_{frame_idx:06d}")
        os.makedirs(frame_dir, exist_ok=True)
        
        print(f"Frame {frame_idx} ({frame_idx + 1}/{len(result.frames)}):")
        print(f"  Segments found: {len(frame_result.segments)}")
        
        frame_metadata = {
            "frame_index": frame_idx,
            "timestamp_ms": (frame_idx / fps * 1000) if fps > 0 else 0,
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
            
            # Crop the segment
            cropped = frame_image.crop((x1, y1, x2, y2))
            
            output_name = f"segment_{segment.segment_id}_crop.png"
            output_path = os.path.join(frame_dir, output_name)
            cropped.save(output_path)
            print(f"    Saved crop: {output_path}")
            
            # Optionally save mask
            mask_name = None
            if save_masks:
                mask = frame_result.masks[segment.mask_index]
                mask_cropped = mask[y1:y2, x1:x2]
                mask_image = Image.fromarray((mask_cropped * 255).astype(np.uint8))
                mask_name = f"segment_{segment.segment_id}_mask.png"
                mask_path = os.path.join(frame_dir, mask_name)
                mask_image.save(mask_path)
                print(f"    Saved mask: {mask_path}")
            
            # Add to metadata
            frame_metadata["segments"].append({
                "segment_id": segment.segment_id,
                "name": segment.name,
                "bbox": segment.bbox,
                "area": float(segment.area),
                "centroid": list(segment.centroid),
                "score": float(segment.score),
                "crop_file": output_name,
                "mask_file": mask_name
            })
        
        print()
        
        # Save per-frame metadata
        video_metadata["frames"][frame_idx] = frame_metadata
        
        # Save frame image for reference
        frame_path = os.path.join(frame_dir, "frame.png")
        frame_image.save(frame_path)
    
    cap.release()
    
    # Save overall metadata JSON
    metadata_path = os.path.join(run_dir, "video_segments_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(video_metadata, f, indent=4)
    
    print(f"{'='*60}")
    print(f"✅ Video segmentation complete!")
    print(f"{'='*60}")
    print(f"Processed: {len(result.frames)} frames")
    print(f"Output directory: {run_dir}")
    print(f"Metadata file: {metadata_path}")
    print(f"{'='*60}\n")

    # Return run directory for downstream pipelines
    return run_dir


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python video_segment.py <video_file> [prompt] [max_frames] [output_every_n]")
        print("\nExamples:")
        print("  python video_segment.py media/scene.mp4")
        print("  python video_segment.py media/scene.mp4 'person walking'")
        print("  python video_segment.py media/scene.mp4 'logo' 100")
        print("  python video_segment.py media/scene.mp4 'car' 50 5")
        sys.exit(1)
    
    video_file = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else None
    max_frames = int(sys.argv[3]) if len(sys.argv) > 3 else None
    output_every_n = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    
    segment_video(video_file, prompt, max_frames, output_every_n, save_masks=True)
    
