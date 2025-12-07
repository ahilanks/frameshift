import sys
import os
import json
from pathlib import Path
import math

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
    
    # Convert mask to numpy if it's a PIL Image and ensure binary alpha (0/255)
    if isinstance(mask, Image.Image):
        mask_array = np.array(mask.convert('L'))
    else:
        mask_array = mask

    # Binarize mask to avoid fractional alpha that can shift edges when resized
    mask_array = (mask_array > 127).astype(np.uint8) * 255
    
    # Resize mask to match image size if needed
    if mask_array.shape[:2] != (image.height, image.width):
        mask_pil = Image.fromarray(mask_array)
        # Use NEAREST to keep mask edges crisp and aligned
        mask_pil = mask_pil.resize((image.width, image.height), Image.NEAREST)
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


def fit_patch_to_bbox(patch: Image.Image, target_w: int, target_h: int, overscale: float = 1.05) -> Image.Image:
    """
    Fit a patch to exact bbox dimensions by overscaling slightly then center-cropping.
    This prevents black borders from undersized AI outputs.
    
    Args:
        patch: PIL Image to fit
        target_w: Target width in pixels
        target_h: Target height in pixels
        overscale: Factor to overscale before cropping (e.g., 1.05 = 5% larger)
    
    Returns:
        PIL Image resized and cropped to exactly (target_w, target_h)
    """
    if target_w <= 0 or target_h <= 0:
        return patch
    
    img = patch.convert("RGB") if patch.mode != "RGB" else patch
    
    # Scale to slightly larger than target
    scale = max(target_w / img.width, target_h / img.height) * overscale
    new_w = max(1, int(round(img.width * scale)))
    new_h = max(1, int(round(img.height * scale)))
    img = img.resize((new_w, new_h), Image.LANCZOS)
    
    # Center crop to exact target dimensions
    if new_w >= target_w and new_h >= target_h:
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))
    else:
        # Fallback: pad if somehow still too small
        canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
        offset_x = (target_w - new_w) // 2
        offset_y = (target_h - new_h) // 2
        canvas.paste(img, (offset_x, offset_y))
        img = canvas
    
    return img


def edit_video_with_tracked_object(
    run_dir,
    edit_prompt,
    output_path=None,
    model="gemini-2.5-flash-image",
    reference_images=None,
    max_frames=None,
    start_frame_idx=None,
    end_frame_idx=None,
    aspect_ratio=None,
    resolution="1K",
    segment_ids=None,
    reuse_edit_every_n_frames=1,
    regenerate_frames=None,
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
        segment_ids: List of segment IDs to edit (None = all segments). E.g., [0, 2] to only edit segments 0 and 2
        reuse_edit_every_n_frames: Edit once every N frames and reuse for intermediate frames (default: 1 = edit every frame)
        regenerate_frames: Explicit frame indices where a fresh edit should be generated regardless of reuse interval
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
    edit_start = start_frame_idx if start_frame_idx is not None else metadata.get("start_frame_idx", 0) or 0
    edit_end = end_frame_idx if end_frame_idx is not None else metadata.get("end_frame_idx", total_frames) or total_frames
    edit_end = min(edit_end, total_frames)
    # If max_frames is provided (e.g., end-start from caller), limit processing range without shrinking total_frames
    processing_end = edit_end
    if max_frames:
        processing_end = min(edit_end, edit_start + max_frames)
    
    print(f"📹 Original video: {video_path}")
    print(f"   Total frames: {total_frames}")
    print(f"   FPS: {fps}")
    print(f"🎨 Edit prompt: '{edit_prompt}'")
    if reference_images:
        print(f"📎 Reference images: {len(reference_images)}")
        for i, ref in enumerate(reference_images, 1):
            print(f"     {i}. {ref}")
    if segment_ids is not None:
        print(f"🎯 Target segments: {segment_ids}")
    else:
        print(f"🎯 Target segments: all")
    if reuse_edit_every_n_frames > 1:
        print(f"♻️  Reuse edit every {reuse_edit_every_n_frames} frames")
    if regenerate_frames:
        print(f"🎞️  Force regeneration on frames: {sorted(set(regenerate_frames))}")
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
    
    # If this run was created from manual boxes, interpolate boxes across frames
    def _interp_frames(md):
        frames_map = {int(k): v for k, v in md["frames"].items()}
        key_frames = sorted(frames_map.keys())
        def strip_crop(seg):
            seg_copy = dict(seg)
            seg_copy["crop_file"] = None
            return seg_copy
        if len(key_frames) == 0:
            return {}
        
        if len(key_frames) == 1:
            # Single keyframe: hold its boxes from edit_start through edit_end
            only_k = key_frames[0]
            fps_val = md.get("fps", 30.0) or 30.0
            total_frames_local = int(md.get("total_video_frames", only_k + 1))
            end_bound = edit_end if md.get("mode") == "manual_boxes" else total_frames_local
            total_frames_use = min(total_frames_local, end_bound)
            interpolated_single = {}
            key_segments = frames_map[only_k]["segments"]
            # Preserve the original keyframe with its crop_file
            interpolated_single[only_k] = frames_map[only_k]
            # Fill other frames with stripped crops to force reuse
            for t in range(edit_start, total_frames_use):
                if t == only_k:
                    continue
                interpolated_single[t] = {
                    "frame_index": t,
                    "timestamp_ms": (t / fps_val * 1000) if fps_val > 0 else 0,
                    "num_segments": len(key_segments),
                    "segments": [strip_crop(seg) for seg in key_segments],
                }
            return {str(k): v for k, v in interpolated_single.items()}

        fps_val = md.get("fps", 30.0) or 30.0
        total_frames_local = int(md.get("total_video_frames", max(key_frames) + 1))
        end_bound = edit_end if md.get("mode") == "manual_boxes" else total_frames_local
        total_frames_use = min(total_frames_local, end_bound)
        interpolated = {}

        def ensure_xywh(seg):
            if "bbox_xywh" in seg and seg["bbox_xywh"]:
                return seg["bbox_xywh"]
            x1, y1, x2, y2 = [int(c) for c in seg["bbox"]]
            return [x1, y1, max(0, x2 - x1), max(0, y2 - y1)]
        
        # Fill from edit_start to first keyframe with first keyframe's boxes
        first_keyframe = key_frames[0]
        first_segments = frames_map[first_keyframe]["segments"]
        for t in range(edit_start, min(first_keyframe, total_frames_use)):
            interpolated[t] = {
                "frame_index": t,
                "timestamp_ms": (t / fps_val * 1000) if fps_val > 0 else 0,
                "num_segments": len(first_segments),
                "segments": [strip_crop(seg) for seg in first_segments],
            }
        
        # Add the keyframes themselves
        for k in key_frames:
            interpolated[k] = frames_map[k]

        # Interpolate between keyframes
        for i in range(len(key_frames) - 1):
            f0, f1 = key_frames[i], key_frames[i + 1]
            span = f1 - f0
            if span <= 1:
                continue

            segs0 = {seg["segment_id"]: seg for seg in frames_map[f0]["segments"]}
            segs1 = {seg["segment_id"]: seg for seg in frames_map[f1]["segments"]}
            common_ids = set(segs0.keys()) & set(segs1.keys())

            for seg_id in common_ids:
                s0 = segs0[seg_id]
                s1 = segs1[seg_id]
                b0 = ensure_xywh(s0)
                b1 = ensure_xywh(s1)
                for t in range(f0 + 1, f1):
                    alpha = (t - f0) / span
                    x = int(round(b0[0] + (b1[0] - b0[0]) * alpha))
                    y = int(round(b0[1] + (b1[1] - b0[1]) * alpha))
                    w = int(round(b0[2] + (b1[2] - b0[2]) * alpha))
                    h = int(round(b0[3] + (b1[3] - b0[3]) * alpha))

                    seg_entry = {
                        "segment_id": seg_id,
                        "name": s0.get("name") or f"box_{seg_id}",
                        "bbox": [x, y, x + w, y + h],
                        "bbox_xywh": [x, y, w, h],
                        "area": float(max(w, 0) * max(h, 0)),
                        "centroid": [x + w / 2.0, y + h / 2.0],
                        "score": 1.0,
                        "crop_file": None,
                        "mask_file": None,
                    }
                    if t not in interpolated:
                        interpolated[t] = {
                            "frame_index": t,
                            "timestamp_ms": (t / fps_val * 1000) if fps_val > 0 else 0,
                            "num_segments": 0,
                            "segments": [],
                        }
                    interpolated[t]["segments"].append(seg_entry)

        # Hold the last keyed boxes through the end of the video
        last_key = key_frames[-1]
        if last_key < total_frames_use - 1:
            last_segments = interpolated[last_key]["segments"]
            for t in range(last_key + 1, total_frames_use):
                interpolated[t] = {
                    "frame_index": t,
                    "timestamp_ms": (t / fps_val * 1000) if fps_val > 0 else 0,
                    "num_segments": len(last_segments),
                    "segments": [strip_crop(seg) for seg in last_segments],
                }

        # Recompute num_segments and normalize keys to strings
        for _, frame_data in interpolated.items():
            frame_data["num_segments"] = len(frame_data.get("segments", []))

        return {str(k): v for k, v in interpolated.items()}

    manual_boxes_mode = metadata.get("mode") == "manual_boxes"
    if manual_boxes_mode:
        print("🎚️  Interpolating manual boxes across frames")
        metadata["frames"] = _interp_frames(metadata)
        reuse_edit_every_n_frames = 1  # force per-frame for interpolated boxes

    # Process each frame
    frames_with_segments = sorted([int(k) for k in metadata['frames'].keys() if edit_start <= int(k) < processing_end])
    if max_frames:
        frames_with_segments = frames_with_segments[:max_frames]
    
    print(f"📊 Frame range: {edit_start} to {processing_end} (exclusive)")
    print(f"📊 Frames with segments: {len(frames_with_segments)} total")
    if len(frames_with_segments) > 0:
        print(f"📊 First frame: {frames_with_segments[0]}, Last frame: {frames_with_segments[-1]}")

    frame_idx = 0
    processed_count = 0
    
    # Cache for reusing edits across frames
    # Structure: {segment_id: {frame_idx: {"image": pil_image, "bbox_size": (w, h)}}}
    edit_cache = {}

    # Normalize regeneration frames to a quick lookup set
    regenerate_set = set(regenerate_frames or [])
    
    # Jump video reader to start frame if needed
    cap.set(cv2.CAP_PROP_POS_FRAMES, edit_start)
    frame_idx = edit_start

    while frame_idx < processing_end:
        ret, frame_bgr = cap.read()
        if not ret:
            break
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        
        # Check if this frame has segmentation data
        if frame_idx in frames_with_segments:
            print(f"Frame {frame_idx} ({frame_idx + 1}/{total_frames}):")
            
            frame_data = metadata['frames'].get(str(frame_idx)) or metadata['frames'].get(frame_idx)
            if not frame_data:
                frame_idx += 1
                continue
            frame_dir = run_dir / f"frame_{frame_idx:06d}"
            
            # Process each segment in this frame
            for segment in frame_data['segments']:
                seg_id = segment['segment_id']
                
                # Filter by segment_ids if specified
                if segment_ids is not None and seg_id not in segment_ids:
                    print(f"  Segment {seg_id}: Skipped (not in target list)")
                    continue
                
                print(f"  Segment {seg_id}:")
                print(f"    BBox: {[int(x) for x in segment['bbox']]}")
                
                # Get bbox coordinates (these define the original segment location)
                x1, y1, x2, y2 = [int(coord) for coord in segment['bbox']]
                target_bbox_width = max(1, x2 - x1)
                target_bbox_height = max(1, y2 - y1)
                current_bbox_xywh = [x1, y1, target_bbox_width, target_bbox_height]
                
                # Decide whether to generate a new edit or reuse a cached one
                is_keyframe = bool(segment.get("crop_file"))
                should_edit = False
                cached_entry = None
                if manual_boxes_mode:
                    should_edit = is_keyframe or (frame_idx in regenerate_set)
                else:
                    should_edit = (frame_idx % reuse_edit_every_n_frames == 0) or (frame_idx in regenerate_set)
                
                if not should_edit and seg_id in edit_cache:
                    # Find the most recent edit for this segment
                    cached_frames = sorted([f for f in edit_cache[seg_id].keys() if f < frame_idx])
                    if cached_frames:
                        last_edit_frame = cached_frames[-1]
                        cached_entry = edit_cache[seg_id][last_edit_frame]
                        print(f"    ♻️  Reusing edit from frame {last_edit_frame}")
                elif frame_idx in regenerate_set:
                    print(f"    🎞️  Regenerating due to keyframe list")
                
                if cached_entry is not None:
                    cached_edit = cached_entry["image"]
                    cached_w, cached_h = cached_entry["bbox_size"]
                    # For manual boxes between keyframes, always reuse even if drift/size change
                    if not manual_boxes_mode or is_keyframe:
                        size_change = max(
                            abs(target_bbox_width - cached_w) / max(1, cached_w),
                            abs(target_bbox_height - cached_h) / max(1, cached_h)
                        )
                        if size_change > 0.2:  # 20% threshold
                            print(f"    ↩️  BBox changed significantly (>{size_change*100:.1f}%), re-editing instead of reusing")
                            cached_entry = None
                        else:
                            cached_bbox_xywh = cached_entry.get("bbox_xywh")
                            if cached_bbox_xywh:
                                cached_cx = cached_bbox_xywh[0] + cached_bbox_xywh[2] / 2.0
                                cached_cy = cached_bbox_xywh[1] + cached_bbox_xywh[3] / 2.0
                                current_cx = current_bbox_xywh[0] + current_bbox_xywh[2] / 2.0
                                current_cy = current_bbox_xywh[1] + current_bbox_xywh[3] / 2.0
                                drift = math.hypot(current_cx - cached_cx, current_cy - cached_cy)
                                diag = math.sqrt(max(target_bbox_width, 1) ** 2 + max(target_bbox_height, 1) ** 2)
                                if diag > 0 and drift / diag > 0.25:
                                    print(f"    ↩️  BBox drifted ({drift/diag:.2f} of diag), regenerating")
                                    cached_entry = None
                
                if cached_entry is not None:
                    # Use cached edit - keep copies so we don't mutate the cache
                    edited_crop = cached_entry["image"].copy()
                    # Fit to current bbox dimensions with slight overscale to eliminate black borders
                    edited_crop = fit_patch_to_bbox(edited_crop, target_bbox_width, target_bbox_height)
                else:
                    if manual_boxes_mode and not is_keyframe:
                        print("    ⚠️  No cached edit yet for this segment; skipping until keyframe")
                        continue
                    # Perform new edit
                    # Crop the segment from the original frame
                    cropped = frame_pil.crop((x1, y1, x2, y2))
                    
                    print(f"    Original bbox crop: {target_bbox_width}x{target_bbox_height}")
                    
                    # For Gemini editing, we'll work with a scaled version
                    # but track all transformations so we can reverse them
                    
                    # Target resolution: aim for 512-1024px on longest side
                    MIN_SIZE = 256
                    TARGET_SIZE = 512
                    MAX_SIZE = 1024
                    
                    # Calculate working dimensions (maintain aspect ratio)
                    working_width = target_bbox_width
                    working_height = target_bbox_height
                    
                    # Scale up if too small
                    if working_width < MIN_SIZE or working_height < MIN_SIZE:
                        scale_factor = MIN_SIZE / min(working_width, working_height)
                        working_width = int(working_width * scale_factor)
                        working_height = int(working_height * scale_factor)
                        print(f"      Scaling up by {scale_factor:.2f}x to: {working_width}x{working_height}")
                    
                    # Scale down if too large
                    elif working_width > MAX_SIZE or working_height > MAX_SIZE:
                        scale_factor = MAX_SIZE / max(working_width, working_height)
                        working_width = int(working_width * scale_factor)
                        working_height = int(working_height * scale_factor)
                        print(f"      Scaling down by {scale_factor:.2f}x to: {working_width}x{working_height}")
                    
                    # Resize crop to working dimensions
                    cropped_working = cropped.resize((working_width, working_height), Image.LANCZOS)
                    
                    # Add padding to make square (helps with Gemini API consistency)
                    target_dim = max(working_width, working_height)
                    
                    # Round up to nearest standard size
                    if target_dim <= 256:
                        target_dim = 256
                    elif target_dim <= 512:
                        target_dim = 512
                    elif target_dim <= 768:
                        target_dim = 768
                    else:
                        target_dim = 1024
                    
                    # Create padded square image
                    padded = Image.new('RGB', (target_dim, target_dim), (0, 0, 0))
                    paste_x = (target_dim - working_width) // 2
                    paste_y = (target_dim - working_height) // 2
                    padded.paste(cropped_working, (paste_x, paste_y))
                    
                    # Store transformation info for reversal
                    transform_info = {
                        'paste_x': paste_x,
                        'paste_y': paste_y,
                        'working_width': working_width,
                        'working_height': working_height,
                        'padded_size': target_dim,
                            'original_bbox_width': target_bbox_width,
                            'original_bbox_height': target_bbox_height
                    }
                    
                    cropped_for_edit = padded
                    print(f"      Working size: {working_width}x{working_height}")
                    print(f"      Padded to: {target_dim}x{target_dim} (padding: x={paste_x}, y={paste_y})")
                    
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
                            # Use original cropped image from frame at original bbox size
                            edited_crop = frame_pil.crop((x1, y1, x2, y2))
                        else:
                            # Verify it's a PIL Image now
                            if not hasattr(edited_crop, 'size'):
                                print(f"        ⚠️  Could not convert to PIL Image, using original")
                                edited_crop = frame_pil.crop((x1, y1, x2, y2))
                            else:
                                print(f"        ✅ Edit successful, received: {edited_crop.size[0]}x{edited_crop.size[1]}")
                                
                                # Reverse transformations:
                                # 1. If Gemini returned a padded square, extract the working area
                                if edited_crop.size == (transform_info['padded_size'], transform_info['padded_size']):
                                    edited_crop = edited_crop.crop((
                                        transform_info['paste_x'],
                                        transform_info['paste_y'],
                                        transform_info['paste_x'] + transform_info['working_width'],
                                        transform_info['paste_y'] + transform_info['working_height']
                                    ))
                                    print(f"        Removed padding: {edited_crop.size[0]}x{edited_crop.size[1]}")
                                
                                # 2. Resize back to original bbox dimensions with overscale to prevent borders
                                edited_crop = fit_patch_to_bbox(edited_crop, transform_info['original_bbox_width'], transform_info['original_bbox_height'])
                        
                    except Exception as e:
                        print(f"        ❌ Error during editing: {e}")
                        import traceback
                        print(f"        Traceback: {traceback.format_exc()}")
                        # Use original cropped image at original bbox size
                        edited_crop = frame_pil.crop((x1, y1, x2, y2))
                    
                    # Cache the edit for potential reuse
                    if seg_id not in edit_cache:
                        edit_cache[seg_id] = {}
                    edit_cache[seg_id][frame_idx] = {
                        "image": edited_crop.copy(),
                        "bbox_size": (target_bbox_width, target_bbox_height),
                        "bbox_xywh": current_bbox_xywh,
                    }
                
                # Ensure edited crop matches the intended bbox size (current frame) with overscale to prevent borders
                edited_crop = fit_patch_to_bbox(edited_crop, target_bbox_width, target_bbox_height)
                if edited_crop.size != (target_bbox_width, target_bbox_height):
                    # Final hard clamp to avoid any residual size drift that could cause borders
                    edited_crop = edited_crop.resize((target_bbox_width, target_bbox_height), Image.LANCZOS)

                # Composite rectangular patch back onto frame
                if edited_crop.mode != "RGB":
                    edited_crop = edited_crop.convert("RGB")
                frame_pil.paste(edited_crop, (x1, y1))
                print(f"    ✓ Edited and composited (rectangular)")
            
            processed_count += 1
            print()
        
        # Convert back to BGR and write
        frame_rgb_out = np.array(frame_pil)
        frame_bgr_out = cv2.cvtColor(frame_rgb_out, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr_out)
        
        frame_idx += 1
    
    cap.release()
    out.release()
    
    # Calculate actual frames written
    frames_written = frame_idx - edit_start
    
    print(f"{'='*60}")
    print(f"✅ Video editing complete!")
    print(f"{'='*60}")
    print(f"Output video: {output_path}")
    print(f"Total frames: {frames_written}")
    print(f"Frames with edits: {processed_count}")
    print(f"{'='*60}\n")
    
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python video_edit_tracked.py <run_directory> <edit_prompt> [options]")
        print("\nOptions:")
        print("  reference_images...    Paths to reference images (e.g., logos)")
        print("  --max-frames N         Only process first N frames")
        print("  --segments IDs         Comma-separated segment IDs to edit (e.g., '0,2,5')")
        print("  --keyframes IDs        Comma-separated frame numbers to regenerate edits on")
        print("  --reuse-every N        Reuse edits every N frames (default: 1)")
        print("\nExamples:")
        print("  # Add a logo to all tracked segments")
        print("  python video_edit_tracked.py video_segments/run_c5cf4832 \\")
        print("    'add the logo to the shirt in the direct center' \\")
        print("    media/ref_logo.png")
        print()
        print("  # Edit only segment 0 (ignore other segments)")
        print("  python video_edit_tracked.py video_segments/run_c5cf4832 \\")
        print("    'change to bright red' --segments 0")
        print()
        print("  # Edit segments 2 and 5 only")
        print("  python video_edit_tracked.py video_segments/run_c5cf4832 \\")
        print("    'add stripes' --segments 2,5")
        print()
        print("  # Edit once every 10 frames (reuse for frames 1-9, 11-19, etc.)")
        print("  python video_edit_tracked.py video_segments/run_c5cf4832 \\")
        print("    'add logo' media/logo.png --reuse-every 10")
        print()
        print("  # Combine: edit segment 0 only, first 50 frames, reuse every 5 frames")
        print("  python video_edit_tracked.py video_segments/run_c5cf4832 \\")
        print("    'add logo' media/logo.png --segments 0 --max-frames 50 --reuse-every 5")
        sys.exit(1)
    
    run_directory = sys.argv[1]
    edit_prompt = sys.argv[2]
    
    # Parse remaining arguments
    reference_images = []
    max_frames = None
    segment_ids = None
    reuse_every = 1
    keyframes = None
    
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
        elif arg == '--segments':
            if i + 1 < len(sys.argv):
                # Parse comma-separated segment IDs
                segment_ids = [int(s.strip()) for s in sys.argv[i + 1].split(',')]
                i += 2
            else:
                print("Error: --segments requires a comma-separated list of IDs")
                sys.exit(1)
        elif arg == '--keyframes':
            if i + 1 < len(sys.argv):
                keyframes = [int(s.strip()) for s in sys.argv[i + 1].split(',') if s.strip()]
                i += 2
            else:
                print("Error: --keyframes requires a comma-separated list of frame numbers")
                sys.exit(1)
        elif arg == '--reuse-every':
            if i + 1 < len(sys.argv):
                reuse_every = int(sys.argv[i + 1])
                i += 2
            else:
                print("Error: --reuse-every requires a value")
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
        max_frames=max_frames,
        segment_ids=segment_ids,
        reuse_edit_every_n_frames=reuse_every,
        regenerate_frames=keyframes
    )

