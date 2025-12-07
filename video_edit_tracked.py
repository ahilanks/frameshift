import sys
import os
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from google import genai
from google.genai import types


def load_image_with_alpha(image_path):
    """Load an image and ensure it has an alpha channel"""
    img = Image.open(image_path).convert("RGBA")
    return img


def apply_mask_to_image(image, mask):
    """
    Apply a mask to an image to create a masked RGBA image.
    
    Args:
        image: PIL Image (RGB or RGBA)
        mask: PIL Image or numpy array (grayscale mask)
    
    Returns:
        PIL Image with alpha channel from mask
    """
    # Ensure image is RGBA
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    
    # Convert mask to numpy if it's a PIL Image
    if isinstance(mask, Image.Image):
        mask_array = np.array(mask.convert('L'))
    else:
        mask_array = mask
    
    # Resize mask to match image size if needed
    if mask_array.shape[:2] != (image.height, image.width):
        mask_pil = Image.fromarray(mask_array)
        mask_pil = mask_pil.resize((image.width, image.height), Image.LANCZOS)
        mask_array = np.array(mask_pil)
    
    # Convert image to numpy
    img_array = np.array(image)
    
    # Apply mask to alpha channel
    img_array[:, :, 3] = mask_array
    
    return Image.fromarray(img_array, 'RGBA')


def composite_on_frame(background, foreground, position):
    """
    Composite a foreground RGBA image onto a background at a specific position.
    
    Args:
        background: PIL Image (RGB)
        foreground: PIL Image (RGBA) with transparency
        position: tuple (x, y) top-left position
    
    Returns:
        PIL Image (RGB) with composited result
    """
    # Ensure background is RGBA for compositing
    if background.mode != "RGBA":
        background = background.convert("RGBA")
    
    # Create a copy to avoid modifying original
    result = background.copy()
    
    # Paste with alpha mask
    result.paste(foreground, position, foreground)
    
    # Convert back to RGB
    return result.convert("RGB")


def edit_video_with_tracked_object(
    run_dir,
    edit_prompt,
    output_path=None,
    model="gemini-2.5-flash-image",
    reference_images=None,
    max_frames=None,
    aspect_ratio=None,
    resolution="1K"
):
    """
    Edit tracked objects in a video using Gemini image editing.
    
    Args:
        run_dir: Path to the video segmentation run directory
        edit_prompt: Text prompt for editing (e.g., "add a Nike logo to the shirt")
        output_path: Path for output video (default: run_dir/edited_video.mp4)
        model: Gemini model to use for editing
        reference_images: List of paths to reference images (e.g., logos to add)
        max_frames: Maximum number of frames to process (None = all)
        aspect_ratio: Aspect ratio for generated images (None = auto)
        resolution: Resolution for generated images ("1K", "2K", "4K")
    """
    run_dir = Path(run_dir)
    
    # Load metadata
    metadata_path = run_dir / "video_segments_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    print(f"{'='*60}")
    print(f"Video Editing with Tracked Objects")
    print(f"{'='*60}")
    print(f"📖 Loading metadata from {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    video_path = metadata['video_path']
    total_frames = metadata['total_video_frames']
    fps = metadata.get('fps', 30.0)
    
    print(f"📹 Original video: {video_path}")
    print(f"   Total frames: {total_frames}")
    print(f"   FPS: {fps}")
    print(f"🎨 Edit prompt: '{edit_prompt}'")
    if reference_images:
        print(f"📎 Reference images: {len(reference_images)}")
        for i, ref in enumerate(reference_images, 1):
            print(f"     {i}. {ref}")
    print(f"{'='*60}\n")
    
    # Initialize Gemini client
    # Try to get API key from environment variable
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError(
            "Gemini API key not found! Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.\n"
            "Example: export GOOGLE_API_KEY='your-api-key-here'"
        )
    
    client = genai.Client(api_key=api_key)
    
    # Open original video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Setup output video
    if output_path is None:
        output_path = run_dir / "edited_video.mp4"
    else:
        output_path = Path(output_path)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    print(f"🎬 Creating output video: {output_path}")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}\n")
    
    # Load reference images if provided
    reference_pil_images = []
    if reference_images:
        for ref_path in reference_images:
            try:
                ref_img = Image.open(ref_path).convert("RGB")
                # Validate reference image size
                ref_width, ref_height = ref_img.size
                print(f"     Reference: {Path(ref_path).name} ({ref_width}x{ref_height})")
                
                # Ensure reasonable size (Gemini limits)
                MAX_REF_DIM = 2048
                if ref_width > MAX_REF_DIM or ref_height > MAX_REF_DIM:
                    scale = MAX_REF_DIM / max(ref_width, ref_height)
                    new_width = int(ref_width * scale)
                    new_height = int(ref_height * scale)
                    ref_img = ref_img.resize((new_width, new_height), Image.LANCZOS)
                    print(f"       Resized to: {new_width}x{new_height}")
                
                reference_pil_images.append(ref_img)
            except Exception as e:
                print(f"⚠️  Could not load reference image {ref_path}: {e}")
    
    # Build generation config - keep it simple to avoid errors
    config_dict = {
        'response_modalities': ['IMAGE'],
    }
    
    # Don't set image_config for edits, let Gemini handle dimensions automatically
    # This avoids INVALID_ARGUMENT errors from incompatible aspect ratios
    
    generation_config = types.GenerateContentConfig(**config_dict)
    
    # Process each frame
    frames_with_segments = sorted([int(k) for k in metadata['frames'].keys()])
    if max_frames:
        frames_with_segments = frames_with_segments[:max_frames]
        total_frames = min(max_frames, total_frames)
    
    frame_idx = 0
    processed_count = 0
    
    while frame_idx < total_frames:
        ret, frame_bgr = cap.read()
        if not ret:
            break
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        
        # Check if this frame has segmentation data
        if frame_idx in frames_with_segments:
            print(f"Frame {frame_idx} ({frame_idx + 1}/{total_frames}):")
            
            frame_data = metadata['frames'][str(frame_idx)]
            frame_dir = run_dir / f"frame_{frame_idx:06d}"
            
            # Process each segment in this frame
            for segment in frame_data['segments']:
                print(f"  Segment {segment['segment_id']}:")
                print(f"    BBox: {[int(x) for x in segment['bbox']]}")
                
                # Get bbox coordinates
                x1, y1, x2, y2 = [int(coord) for coord in segment['bbox']]
                
                # Crop the segment from the original frame
                cropped = frame_pil.crop((x1, y1, x2, y2))
                crop_width, crop_height = cropped.size
                
                print(f"    Crop size: {crop_width}x{crop_height}")
                
                # Add black borders to match standard aspect ratios
                # This preserves the original image without distortion
                # and ensures uniform dimensions for Gemini API
                
                # Target resolution: aim for 512x512 or nearest standard size
                TARGET_SIZE = 512
                MIN_SIZE = 256
                MAX_SIZE = 1024
                
                # First, ensure minimum size with scaling if needed
                scale_factor = 1.0
                if crop_width < MIN_SIZE or crop_height < MIN_SIZE:
                    scale_factor = MIN_SIZE / min(crop_width, crop_height)
                    crop_width = int(crop_width * scale_factor)
                    crop_height = int(crop_height * scale_factor)
                    cropped = cropped.resize((crop_width, crop_height), Image.LANCZOS)
                    print(f"      Scaled up to: {crop_width}x{crop_height}")
                
                # Then scale down if too large
                if crop_width > MAX_SIZE or crop_height > MAX_SIZE:
                    scale_factor = MAX_SIZE / max(crop_width, crop_height)
                    crop_width = int(crop_width * scale_factor)
                    crop_height = int(crop_height * scale_factor)
                    cropped = cropped.resize((crop_width, crop_height), Image.LANCZOS)
                    print(f"      Scaled down to: {crop_width}x{crop_height}")
                
                # Determine target dimensions with black borders
                # Use square format for simplicity and consistency
                target_dim = max(crop_width, crop_height)
                
                # Round up to nearest standard size for better API compatibility
                if target_dim <= 256:
                    target_dim = 256
                elif target_dim <= 512:
                    target_dim = 512
                elif target_dim <= 768:
                    target_dim = 768
                else:
                    target_dim = 1024
                
                # Create padded image with black borders
                padded = Image.new('RGB', (target_dim, target_dim), (0, 0, 0))
                paste_x = (target_dim - crop_width) // 2
                paste_y = (target_dim - crop_height) // 2
                padded.paste(cropped, (paste_x, paste_y))
                
                # Store padding info for later mask application
                padding_info = {
                    'paste_x': paste_x,
                    'paste_y': paste_y,
                    'original_width': crop_width,
                    'original_height': crop_height,
                    'padded_size': target_dim
                }
                
                cropped_for_edit = padded
                print(f"      Padded to: {target_dim}x{target_dim} (borders: {paste_x}px, {paste_y}px)")
                
                # Edit the cropped segment with Gemini
                print(f"    Editing crop...")
                try:
                    # Build content list
                    content = [edit_prompt, cropped_for_edit]
                    if reference_pil_images:
                        content.extend(reference_pil_images)
                    
                    # Truncate prompt for display
                    display_prompt = edit_prompt[:60] + '...' if len(edit_prompt) > 60 else edit_prompt
                    print(f"      🎨 Editing with Gemini: '{display_prompt}'")
                    
                    if reference_pil_images:
                        for i, ref_img in enumerate(reference_pil_images, 1):
                            ref_name = Path(reference_images[i-1]).name
                            ref_size = f"{ref_img.width}x{ref_img.height}"
                            print(f"        📎 Using reference {i}: {ref_name} ({ref_size})")
                    
                    response = client.models.generate_content(
                        model=model,
                        contents=content,
                        config=generation_config
                    )
                    
                    # Extract edited image
                    edited_crop = None
                    for part in response.parts:
                        if part.inline_data is not None:
                            # Convert genai Image to PIL Image
                            genai_image = part.as_image()
                            # genai's as_image() already returns a PIL Image, but let's ensure it
                            if hasattr(genai_image, 'size'):
                                # It's already a PIL Image
                                edited_crop = genai_image
                            else:
                                # It's a genai Image object, need to convert
                                # The inline_data contains the image bytes
                                import io
                                image_bytes = part.inline_data.data
                                edited_crop = Image.open(io.BytesIO(image_bytes))
                            break
                    
                    if edited_crop is None:
                        print(f"        ⚠️  No image returned, using original")
                        # Use original cropped image from frame
                        original_bbox_width = x2 - x1
                        original_bbox_height = y2 - y1
                        edited_crop = frame_pil.crop((x1, y1, x2, y2))
                    else:
                        # Verify it's a PIL Image now
                        if not hasattr(edited_crop, 'size'):
                            print(f"        ⚠️  Could not convert to PIL Image, using original")
                            original_bbox_width = x2 - x1
                            original_bbox_height = y2 - y1
                            edited_crop = frame_pil.crop((x1, y1, x2, y2))
                        else:
                            print(f"        ✅ Edit successful ({edited_crop.size[0]}x{edited_crop.size[1]})")
                            
                            # Extract the center region from padded result
                            # The edited image should match the padded size
                            if edited_crop.size == (padding_info['padded_size'], padding_info['padded_size']):
                                # Crop out the padding to get back to original dimensions
                                edited_crop = edited_crop.crop((
                                    padding_info['paste_x'],
                                    padding_info['paste_y'],
                                    padding_info['paste_x'] + padding_info['original_width'],
                                    padding_info['paste_y'] + padding_info['original_height']
                                ))
                                print(f"        Extracted from padding: {edited_crop.size[0]}x{edited_crop.size[1]}")
                            
                            # Now resize to match the ORIGINAL crop bbox size (before any scaling)
                            original_bbox_width = x2 - x1
                            original_bbox_height = y2 - y1
                            if edited_crop.size != (original_bbox_width, original_bbox_height):
                                edited_crop = edited_crop.resize((original_bbox_width, original_bbox_height), Image.LANCZOS)
                    
                except Exception as e:
                    print(f"        ❌ Error during editing: {e}")
                    import traceback
                    print(f"        Traceback: {traceback.format_exc()}")
                    # Use original cropped image
                    original_bbox_width = x2 - x1
                    original_bbox_height = y2 - y1
                    edited_crop = frame_pil.crop((x1, y1, x2, y2))
                
                # Load the mask
                mask_file = segment.get('mask_file')
                if mask_file:
                    mask_path = frame_dir / mask_file
                    if mask_path.exists():
                        # Load mask
                        mask_pil = Image.open(mask_path).convert('L')
                        mask_array = np.array(mask_pil)
                        
                        # Ensure edited crop matches the bbox size (should already be correct)
                        original_bbox_width = x2 - x1
                        original_bbox_height = y2 - y1
                        if edited_crop.size != (original_bbox_width, original_bbox_height):
                            edited_crop = edited_crop.resize((original_bbox_width, original_bbox_height), Image.LANCZOS)
                        
                        # Apply mask to edited crop
                        masked_edit = apply_mask_to_image(edited_crop, mask_array)
                        
                        # Composite back onto original frame
                        frame_pil = composite_on_frame(frame_pil, masked_edit, (x1, y1))
                        
                        print(f"    ✓ Edited and composited")
                    else:
                        print(f"    ⚠️  Mask file not found: {mask_path}")
                else:
                    print(f"    ⚠️  No mask file in metadata")
            
            processed_count += 1
            print()
        
        # Convert back to BGR and write
        frame_rgb_out = np.array(frame_pil)
        frame_bgr_out = cv2.cvtColor(frame_rgb_out, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr_out)
        
        frame_idx += 1
    
    cap.release()
    out.release()
    
    print(f"{'='*60}")
    print(f"✅ Video editing complete!")
    print(f"{'='*60}")
    print(f"Output video: {output_path}")
    print(f"Total frames: {frame_idx}")
    print(f"Frames with edits: {processed_count}")
    print(f"{'='*60}\n")
    
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python video_edit_tracked.py <run_directory> <edit_prompt> [reference_images...] [--max-frames N]")
        print("\nExamples:")
        print("  # Add a logo to tracked shirt")
        print("  python video_edit_tracked.py video_segments/run_c5cf4832 \\")
        print("    'add the logo to the shirt in the direct center onto the shirt' \\")
        print("    media/ref_logo.png")
        print()
        print("  # Change color of tracked object")
        print("  python video_edit_tracked.py video_segments/run_c5cf4832 \\")
        print("    'change the shirt color to bright red'")
        print()
        print("  # Process only first 50 frames")
        print("  python video_edit_tracked.py video_segments/run_c5cf4832 \\")
        print("    'add stripes to the shirt' --max-frames 50")
        print()
        print("Arguments:")
        print("  run_directory: Path to video segmentation run folder")
        print("  edit_prompt: Text description of the edit to perform")
        print("  reference_images: Optional paths to reference images (e.g., logos)")
        print("  --max-frames N: Only process first N frames (optional)")
        sys.exit(1)
    
    run_directory = sys.argv[1]
    edit_prompt = sys.argv[2]
    
    # Parse remaining arguments
    reference_images = []
    max_frames = None
    
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--max-frames':
            if i + 1 < len(sys.argv):
                max_frames = int(sys.argv[i + 1])
                i += 2
            else:
                print("Error: --max-frames requires a value")
                sys.exit(1)
        else:
            # Assume it's a reference image
            if Path(arg).exists():
                reference_images.append(arg)
            else:
                print(f"Warning: File not found, skipping: {arg}")
            i += 1
    
    edit_video_with_tracked_object(
        run_directory,
        edit_prompt,
        reference_images=reference_images if reference_images else None,
        max_frames=max_frames
    )

