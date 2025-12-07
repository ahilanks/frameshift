"""
Image Masking Module for Frameshift

This module provides functionality to mask/composite a replacement image onto a base image
using segmentation coordinates. It supports both mask-based and bounding box-based compositing.
"""

import sys
sys.path.append('.')

import numpy as np
from PIL import Image
from typing import Union, Optional, Tuple
from pathlib import Path

from sam import SegmentationResult, SegmentMetadata


def mask_image_onto_base(
    base_image: Union[str, Image.Image],
    replacement_image: Union[str, Image.Image],
    segment_mask: np.ndarray,
    blend_mode: str = "replace",
    feather_radius: int = 0,
    opacity: float = 1.0
) -> Image.Image:
    """
    Mask a replacement image onto a base image using a binary segmentation mask.
    
    Args:
        base_image: The base/background image (PIL Image or path)
        replacement_image: The image to composite onto the base (PIL Image or path)
        segment_mask: Binary segmentation mask (H, W) where True/1 indicates the region to replace
        blend_mode: How to blend the images ("replace", "multiply", "screen", "overlay")
        feather_radius: Optional feathering/smoothing of mask edges in pixels
        opacity: Opacity of the replacement image (0.0 to 1.0)
    
    Returns:
        PIL Image with the replacement image masked onto the base
    """
    # Load images
    if isinstance(base_image, str):
        base_image = Image.open(base_image).convert("RGBA")
    else:
        base_image = base_image.convert("RGBA")
    
    if isinstance(replacement_image, str):
        replacement_image = Image.open(replacement_image).convert("RGBA")
    else:
        replacement_image = replacement_image.convert("RGBA")
    
    # Ensure images are the same size
    if replacement_image.size != base_image.size:
        replacement_image = replacement_image.resize(base_image.size, Image.Resampling.LANCZOS)
    
    # Convert mask to uint8 if needed
    if segment_mask.dtype == bool:
        mask = (segment_mask * 255).astype(np.uint8)
    elif segment_mask.dtype != np.uint8:
        mask = (segment_mask * 255).astype(np.uint8)
    else:
        mask = segment_mask
    
    # Create PIL mask
    mask_pil = Image.fromarray(mask, mode='L')
    
    # Resize mask if needed
    if mask_pil.size != base_image.size:
        mask_pil = mask_pil.resize(base_image.size, Image.Resampling.LANCZOS)
    
    # Apply feathering if requested
    if feather_radius > 0:
        from PIL import ImageFilter
        mask_pil = mask_pil.filter(ImageFilter.GaussianBlur(radius=feather_radius))
    
    # Apply opacity
    if opacity < 1.0:
        mask_array = np.array(mask_pil).astype(float)
        mask_array = (mask_array * opacity).astype(np.uint8)
        mask_pil = Image.fromarray(mask_array, mode='L')
    
    # Apply blend mode
    if blend_mode == "replace":
        # Simple alpha composite
        result = Image.composite(replacement_image, base_image, mask_pil)
    elif blend_mode == "multiply":
        # Multiply blend
        base_array = np.array(base_image, dtype=float) / 255.0
        repl_array = np.array(replacement_image, dtype=float) / 255.0
        mask_array = np.array(mask_pil, dtype=float) / 255.0
        
        # Multiply where mask is active
        multiplied = base_array[:, :, :3] * repl_array[:, :, :3]
        result_array = base_array.copy()
        for i in range(3):  # RGB channels
            result_array[:, :, i] = base_array[:, :, i] * (1 - mask_array) + multiplied[:, :, i] * mask_array
        
        result = Image.fromarray((result_array * 255).astype(np.uint8), mode='RGBA')
    elif blend_mode == "screen":
        # Screen blend
        base_array = np.array(base_image, dtype=float) / 255.0
        repl_array = np.array(replacement_image, dtype=float) / 255.0
        mask_array = np.array(mask_pil, dtype=float) / 255.0
        
        # Screen: 1 - (1-a)(1-b)
        screened = 1 - (1 - base_array[:, :, :3]) * (1 - repl_array[:, :, :3])
        result_array = base_array.copy()
        for i in range(3):
            result_array[:, :, i] = base_array[:, :, i] * (1 - mask_array) + screened[:, :, i] * mask_array
        
        result = Image.fromarray((result_array * 255).astype(np.uint8), mode='RGBA')
    elif blend_mode == "overlay":
        # Overlay blend
        base_array = np.array(base_image, dtype=float) / 255.0
        repl_array = np.array(replacement_image, dtype=float) / 255.0
        mask_array = np.array(mask_pil, dtype=float) / 255.0
        
        # Overlay: multiply if base < 0.5, screen if base >= 0.5
        overlayed = np.where(
            base_array[:, :, :3] < 0.5,
            2 * base_array[:, :, :3] * repl_array[:, :, :3],
            1 - 2 * (1 - base_array[:, :, :3]) * (1 - repl_array[:, :, :3])
        )
        result_array = base_array.copy()
        for i in range(3):
            result_array[:, :, i] = base_array[:, :, i] * (1 - mask_array) + overlayed[:, :, i] * mask_array
        
        result = Image.fromarray((result_array * 255).astype(np.uint8), mode='RGBA')
    else:
        raise ValueError(f"Unknown blend mode: {blend_mode}")
    
    return result


def mask_image_with_bbox(
    base_image: Union[str, Image.Image],
    replacement_image: Union[str, Image.Image],
    bbox: Tuple[int, int, int, int],
    resize_mode: str = "fit",
    blend_mode: str = "replace",
    opacity: float = 1.0
) -> Image.Image:
    """
    Mask a replacement image onto a base image using a bounding box.
    
    Args:
        base_image: The base/background image (PIL Image or path)
        replacement_image: The image to composite onto the base (PIL Image or path)
        bbox: Bounding box as (x1, y1, x2, y2) in pixels
        resize_mode: How to fit the replacement image ("fit", "fill", "stretch")
        blend_mode: How to blend the images ("replace", "multiply", "screen", "overlay")
        opacity: Opacity of the replacement image (0.0 to 1.0)
    
    Returns:
        PIL Image with the replacement image masked onto the base
    """
    # Load images
    if isinstance(base_image, str):
        base_image = Image.open(base_image).convert("RGBA")
    else:
        base_image = base_image.convert("RGBA")
    
    if isinstance(replacement_image, str):
        replacement_image = Image.open(replacement_image).convert("RGBA")
    else:
        replacement_image = replacement_image.convert("RGBA")
    
    # Extract bbox coordinates
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    bbox_width = x2 - x1
    bbox_height = y2 - y1
    
    # Resize replacement image based on mode
    if resize_mode == "fit":
        # Maintain aspect ratio, fit within bbox
        replacement_image.thumbnail((bbox_width, bbox_height), Image.Resampling.LANCZOS)
        # Center in bbox
        repl_width, repl_height = replacement_image.size
        x_offset = (bbox_width - repl_width) // 2
        y_offset = (bbox_height - repl_height) // 2
        paste_x = x1 + x_offset
        paste_y = y1 + y_offset
    elif resize_mode == "fill":
        # Maintain aspect ratio, fill bbox (may crop)
        repl_aspect = replacement_image.width / replacement_image.height
        bbox_aspect = bbox_width / bbox_height
        
        if repl_aspect > bbox_aspect:
            # Replacement is wider, scale by height
            new_height = bbox_height
            new_width = int(bbox_height * repl_aspect)
        else:
            # Replacement is taller, scale by width
            new_width = bbox_width
            new_height = int(bbox_width / repl_aspect)
        
        replacement_image = replacement_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to bbox size
        x_offset = (new_width - bbox_width) // 2
        y_offset = (new_height - bbox_height) // 2
        replacement_image = replacement_image.crop((x_offset, y_offset, x_offset + bbox_width, y_offset + bbox_height))
        paste_x = x1
        paste_y = y1
    elif resize_mode == "stretch":
        # Stretch to fill bbox exactly
        replacement_image = replacement_image.resize((bbox_width, bbox_height), Image.Resampling.LANCZOS)
        paste_x = x1
        paste_y = y1
    else:
        raise ValueError(f"Unknown resize mode: {resize_mode}")
    
    # Apply opacity if needed
    if opacity < 1.0:
        alpha = replacement_image.split()[3]
        alpha = Image.eval(alpha, lambda a: int(a * opacity))
        replacement_image.putalpha(alpha)
    
    # Create a copy of base image
    result = base_image.copy()
    
    # Paste replacement image
    if blend_mode == "replace":
        result.paste(replacement_image, (paste_x, paste_y), replacement_image)
    else:
        # For other blend modes, create a temporary composite
        temp = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        temp.paste(replacement_image, (paste_x, paste_y))
        
        # Create mask from the pasted region
        mask = temp.split()[3]
        
        # Apply the blend using mask_image_onto_base logic
        if blend_mode in ["multiply", "screen", "overlay"]:
            base_array = np.array(result, dtype=float) / 255.0
            temp_array = np.array(temp, dtype=float) / 255.0
            mask_array = np.array(mask, dtype=float) / 255.0
            
            if blend_mode == "multiply":
                blended = base_array[:, :, :3] * temp_array[:, :, :3]
            elif blend_mode == "screen":
                blended = 1 - (1 - base_array[:, :, :3]) * (1 - temp_array[:, :, :3])
            elif blend_mode == "overlay":
                blended = np.where(
                    base_array[:, :, :3] < 0.5,
                    2 * base_array[:, :, :3] * temp_array[:, :, :3],
                    1 - 2 * (1 - base_array[:, :, :3]) * (1 - temp_array[:, :, :3])
                )
            
            result_array = base_array.copy()
            for i in range(3):
                result_array[:, :, i] = base_array[:, :, i] * (1 - mask_array) + blended[:, :, i] * mask_array
            
            result = Image.fromarray((result_array * 255).astype(np.uint8), mode='RGBA')
    
    return result


def mask_with_segmentation_result(
    base_image: Union[str, Image.Image],
    replacement_image: Union[str, Image.Image],
    segmentation_result: SegmentationResult,
    segment_id: Optional[int] = None,
    use_mask: bool = True,
    **kwargs
) -> Image.Image:
    """
    Mask a replacement image onto a base image using a SegmentationResult.
    
    Args:
        base_image: The base/background image (PIL Image or path)
        replacement_image: The image to composite onto the base (PIL Image or path)
        segmentation_result: SegmentationResult containing masks and metadata
        segment_id: Optional segment ID to use (if None, uses the first/largest segment)
        use_mask: If True, uses the segmentation mask; if False, uses bounding box
        **kwargs: Additional arguments passed to mask_image_onto_base or mask_image_with_bbox
    
    Returns:
        PIL Image with the replacement image masked onto the base
    """
    # Find the segment to use
    if segment_id is not None:
        segment = next((s for s in segmentation_result.segments if s.segment_id == segment_id), None)
        if segment is None:
            raise ValueError(f"Segment ID {segment_id} not found in segmentation result")
    else:
        # Use the largest segment (first in sorted list)
        if len(segmentation_result.segments) == 0:
            raise ValueError("No segments found in segmentation result")
        segment = segmentation_result.segments[0]
    
    if use_mask:
        # Get the mask for this segment
        mask_idx = segment.mask_index
        segment_mask = segmentation_result.masks[mask_idx]
        
        return mask_image_onto_base(
            base_image=base_image,
            replacement_image=replacement_image,
            segment_mask=segment_mask,
            **kwargs
        )
    else:
        # Use bounding box
        return mask_image_with_bbox(
            base_image=base_image,
            replacement_image=replacement_image,
            bbox=segment.bbox,
            **kwargs
        )


def mask_with_segment_metadata(
    base_image: Union[str, Image.Image],
    replacement_image: Union[str, Image.Image],
    segment: SegmentMetadata,
    mask: Optional[np.ndarray] = None,
    use_mask: bool = True,
    **kwargs
) -> Image.Image:
    """
    Mask a replacement image onto a base image using SegmentMetadata.
    
    Args:
        base_image: The base/background image (PIL Image or path)
        replacement_image: The image to composite onto the base (PIL Image or path)
        segment: SegmentMetadata containing bbox and other info
        mask: Optional binary mask (required if use_mask=True)
        use_mask: If True, uses the mask; if False, uses bounding box
        **kwargs: Additional arguments passed to mask_image_onto_base or mask_image_with_bbox
    
    Returns:
        PIL Image with the replacement image masked onto the base
    """
    if use_mask:
        if mask is None:
            raise ValueError("mask parameter is required when use_mask=True")
        return mask_image_onto_base(
            base_image=base_image,
            replacement_image=replacement_image,
            segment_mask=mask,
            **kwargs
        )
    else:
        return mask_image_with_bbox(
            base_image=base_image,
            replacement_image=replacement_image,
            bbox=segment.bbox,
            **kwargs
        )


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Mask a replacement image onto a base image using segmentation")
    parser.add_argument("base_image", help="Path to base/background image")
    parser.add_argument("replacement_image", help="Path to replacement image")
    parser.add_argument("--bbox", type=int, nargs=4, help="Bounding box as x1 y1 x2 y2")
    parser.add_argument("--segment-image", help="Path to segmented image to use for masking")
    parser.add_argument("--output", "-o", default="outputs/masked_result.png", help="Output path")
    parser.add_argument("--blend-mode", default="replace", choices=["replace", "multiply", "screen", "overlay"],
                        help="Blend mode")
    parser.add_argument("--resize-mode", default="fit", choices=["fit", "fill", "stretch"],
                        help="Resize mode for bbox masking")
    parser.add_argument("--opacity", type=float, default=1.0, help="Opacity (0.0 to 1.0)")
    parser.add_argument("--feather", type=int, default=0, help="Feather radius for mask edges")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    if args.bbox:
        # Use bounding box mode
        print(f"Masking with bounding box: {args.bbox}")
        result = mask_image_with_bbox(
            base_image=args.base_image,
            replacement_image=args.replacement_image,
            bbox=tuple(args.bbox),
            resize_mode=args.resize_mode,
            blend_mode=args.blend_mode,
            opacity=args.opacity
        )
    elif args.segment_image:
        # Use segment image as mask
        print(f"Masking with segment image: {args.segment_image}")
        # Load segment image as grayscale mask
        segment_img = Image.open(args.segment_image).convert('L')
        segment_mask = np.array(segment_img) > 128  # Threshold to binary
        
        result = mask_image_onto_base(
            base_image=args.base_image,
            replacement_image=args.replacement_image,
            segment_mask=segment_mask,
            blend_mode=args.blend_mode,
            feather_radius=args.feather,
            opacity=args.opacity
        )
    else:
        print("Error: Must provide either --bbox or --segment-image")
        sys.exit(1)
    
    # Save result
    result = result.convert("RGB")  # Convert to RGB for saving
    result.save(args.output)
    print(f"✅ Saved masked result to {args.output}")

