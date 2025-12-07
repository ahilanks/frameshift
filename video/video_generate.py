import sys
import os
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import colorsys


def generate_colors(n):
    """Generate n visually distinct colors"""
    colors = []
    for i in range(n):
        hue = i / n
        saturation = 0.9
        value = 0.9
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append(tuple(int(c * 255) for c in rgb))
    return colors


def apply_mask_overlay(frame, mask, color, alpha=0.5):
    """
    Apply a colored semi-transparent mask overlay to a frame.
    
    Args:
        frame: numpy array (H, W, 3) RGB image
        mask: numpy array (H, W) binary mask
        color: tuple (R, G, B) color for the mask
        alpha: transparency level (0=transparent, 1=opaque)
    """
    overlay = frame.copy()
    overlay[mask > 0] = color
    return cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)


def draw_bbox_and_label(frame, bbox, label, color, score=None):
    """Draw bounding box and label on frame"""
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    
    # Draw bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    
    # Prepare label text
    if score is not None:
        text = f"{label} ({score:.2f})"
    else:
        text = label
    
    # Calculate text size and background
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    # Draw background rectangle for text
    cv2.rectangle(frame, (x1, y1 - text_height - 10), (x1 + text_width + 10, y1), color, -1)
    
    # Draw text
    cv2.putText(frame, text, (x1 + 5, y1 - 5), font, font_scale, (255, 255, 255), thickness)
    
    return frame


def generate_video_with_masks(run_dir, output_path=None, alpha=0.5, show_bbox=True, show_labels=True):
    """
    Generate a video with segmentation masks overlaid.
    
    Args:
        run_dir: Path to the run directory containing metadata and frames
        output_path: Path for output video (default: run_dir/output_video.mp4)
        alpha: Transparency of mask overlay (0-1)
        show_bbox: Whether to show bounding boxes
        show_labels: Whether to show labels
    """
    run_dir = Path(run_dir)
    
    # Load metadata
    metadata_path = run_dir / "video_segments_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    print(f"📖 Loading metadata from {metadata_path}")
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    video_path = metadata['video_path']
    total_frames = metadata['total_video_frames']
    processed_frames = metadata['processed_frames']
    fps = metadata.get('fps', 30.0)
    
    print(f"📹 Original video: {video_path}")
    print(f"   Total frames: {total_frames}")
    print(f"   Processed frames: {processed_frames}")
    print(f"   FPS: {fps}")
    
    # Open original video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Setup output video
    if output_path is None:
        output_path = run_dir / "output_video.mp4"
    else:
        output_path = Path(output_path)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    print(f"🎬 Creating output video: {output_path}")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}")
    print()
    
    # Determine unique object IDs across all frames for consistent coloring
    all_object_ids = set()
    for frame_data in metadata['frames'].values():
        for segment in frame_data['segments']:
            all_object_ids.add(segment['segment_id'])
    
    # Generate colors for each unique object ID
    colors = generate_colors(len(all_object_ids))
    object_id_to_color = {obj_id: colors[i] for i, obj_id in enumerate(sorted(all_object_ids))}
    
    print(f"🎨 Generated {len(all_object_ids)} unique colors for objects")
    print()
    
    # Process each frame
    frame_idx = 0
    frames_with_masks = set(int(k) for k in metadata['frames'].keys())
    
    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            break
        
        # Convert BGR to RGB for processing
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # Check if this frame has segmentation data
        if frame_idx in frames_with_masks:
            frame_data = metadata['frames'][str(frame_idx)]
            frame_dir = run_dir / f"frame_{frame_idx:06d}"
            
            # Process each segment in this frame
            for segment in frame_data['segments']:
                segment_id = segment['segment_id']
                color = object_id_to_color[segment_id]
                
                # Load the mask
                mask_file = segment.get('mask_file')
                if mask_file:
                    mask_path = frame_dir / mask_file
                    if mask_path.exists():
                        # Load mask and resize to frame size if needed
                        mask_img = Image.open(mask_path).convert('L')
                        mask_array = np.array(mask_img)
                        
                        # Create full-size mask
                        full_mask = np.zeros((height, width), dtype=np.uint8)
                        x1, y1, x2, y2 = [int(coord) for coord in segment['bbox']]
                        
                        # Resize mask to bbox size if needed
                        bbox_h, bbox_w = y2 - y1, x2 - x1
                        if mask_array.shape != (bbox_h, bbox_w):
                            mask_resized = cv2.resize(mask_array, (bbox_w, bbox_h))
                        else:
                            mask_resized = mask_array
                        
                        # Place mask in correct position
                        full_mask[y1:y2, x1:x2] = mask_resized
                        
                        # Apply overlay
                        frame_rgb = apply_mask_overlay(frame_rgb, full_mask, color, alpha)
                
                # Draw bounding box and label
                if show_bbox:
                    label = f"ID:{segment_id}"
                    if show_labels and segment.get('name'):
                        label = segment['name']
                    
                    frame_rgb = draw_bbox_and_label(
                        frame_rgb,
                        segment['bbox'],
                        label,
                        color,
                        segment.get('score')
                    )
            
            if (frame_idx + 1) % 10 == 0:
                print(f"   Processed frame {frame_idx + 1}/{total_frames} (with masks)")
        else:
            if (frame_idx + 1) % 50 == 0:
                print(f"   Processed frame {frame_idx + 1}/{total_frames}")
        
        # Convert back to BGR for video writing
        frame_bgr_out = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr_out)
        
        frame_idx += 1
    
    cap.release()
    out.release()
    
    print()
    print(f"{'='*60}")
    print(f"✅ Video generation complete!")
    print(f"{'='*60}")
    print(f"Output video: {output_path}")
    print(f"Total frames processed: {frame_idx}")
    print(f"Frames with masks: {len(frames_with_masks)}")
    print(f"{'='*60}")
    
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python video_generate.py <run_directory> [output_path] [alpha]")
        print("\nExamples:")
        print("  python video_generate.py video_segments/run_c5cf4832")
        print("  python video_generate.py video_segments/run_c5cf4832 output.mp4")
        print("  python video_generate.py video_segments/run_c5cf4832 output.mp4 0.3")
        print("\nArguments:")
        print("  run_directory: Path to segmentation run folder")
        print("  output_path: Optional output video path (default: run_dir/output_video.mp4)")
        print("  alpha: Mask transparency 0-1 (default: 0.5, lower=more transparent)")
        sys.exit(1)
    
    run_directory = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    alpha = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    
    generate_video_with_masks(run_directory, output, alpha=alpha)

