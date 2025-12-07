"""
Utility functions for visualization and export of SAM 3 segmentation results
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image
from typing import List, Optional, Union, Tuple
import cv2
import json
import pandas as pd
from pathlib import Path

from sam import SegmentationResult, VideoSegmentationResult


def overlay_masks(
    image: Union[str, Image.Image, np.ndarray],
    masks: np.ndarray,
    alpha: float = 0.5,
    colors: Optional[List[Tuple[int, int, int]]] = None
) -> Image.Image:
    """
    Overlay segmentation masks on an image with colors.
    
    Args:
        image: PIL Image, numpy array, or path to image
        masks: Binary masks array of shape (N, H, W)
        alpha: Transparency of mask overlay (0-1)
        colors: Optional list of RGB colors for each mask
        
    Returns:
        PIL Image with overlaid masks
    """
    # Load and convert image
    if isinstance(image, str):
        image = Image.open(image).convert("RGB")
    elif isinstance(image, np.ndarray):
        image = Image.fromarray(image).convert("RGB")
    else:
        image = image.convert("RGB")
    
    image = image.convert("RGBA")
    
    # Convert masks to uint8
    if masks.dtype != np.uint8:
        masks = (255 * masks).astype(np.uint8)
    
    n_masks = masks.shape[0]
    
    # Generate colors if not provided
    if colors is None:
        cmap = matplotlib.colormaps.get_cmap("rainbow").resampled(n_masks)
        colors = [
            tuple(int(c * 255) for c in cmap(i)[:3])
            for i in range(n_masks)
        ]
    
    # Overlay each mask
    for mask, color in zip(masks, colors):
        mask_img = Image.fromarray(mask)
        overlay = Image.new("RGBA", image.size, color + (0,))
        alpha_channel = mask_img.point(lambda v: int(v * alpha))
        overlay.putalpha(alpha_channel)
        image = Image.alpha_composite(image, overlay)
    
    return image.convert("RGB")


def draw_bounding_boxes(
    image: Union[str, Image.Image, np.ndarray],
    result: SegmentationResult,
    show_labels: bool = True,
    line_thickness: int = 2
) -> Image.Image:
    """
    Draw bounding boxes and labels on image.
    
    Args:
        image: PIL Image, numpy array, or path to image
        result: SegmentationResult containing segment metadata
        show_labels: Whether to show text labels
        line_thickness: Thickness of bounding box lines
        
    Returns:
        PIL Image with bounding boxes
    """
    # Load image
    if isinstance(image, str):
        img = cv2.imread(image)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    elif isinstance(image, Image.Image):
        img = np.array(image)
    else:
        img = image.copy()
    
    # Generate colors
    n_segments = len(result.segments)
    cmap = matplotlib.colormaps.get_cmap("rainbow").resampled(n_segments)
    colors = [
        tuple(int(c * 255) for c in cmap(i)[:3])
        for i in range(n_segments)
    ]
    
    # Draw each bounding box
    for segment, color in zip(result.segments, colors):
        x1, y1, x2, y2 = [int(v) for v in segment.bbox]
        
        # Draw rectangle
        cv2.rectangle(img, (x1, y1), (x2, y2), color, line_thickness)
        
        if show_labels:
            # Create label text
            label = f"{segment.name} ({segment.score:.2f})"
            
            # Get text size for background
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (text_width, text_height), baseline = cv2.getTextSize(
                label, font, font_scale, thickness
            )
            
            # Draw background rectangle for text
            cv2.rectangle(
                img,
                (x1, y1 - text_height - 10),
                (x1 + text_width, y1),
                color,
                -1
            )
            
            # Draw text
            cv2.putText(
                img,
                label,
                (x1, y1 - 5),
                font,
                font_scale,
                (255, 255, 255),
                thickness
            )
    
    return Image.fromarray(img)


def create_segmentation_visualization(
    image: Union[str, Image.Image],
    result: SegmentationResult,
    output_path: Optional[str] = None,
    show_boxes: bool = True,
    show_masks: bool = True,
    figsize: Tuple[int, int] = (15, 5)
) -> Optional[plt.Figure]:
    """
    Create a comprehensive visualization with original image, masks, and boxes.
    
    Args:
        image: PIL Image or path to image
        result: SegmentationResult
        output_path: Optional path to save figure
        show_boxes: Whether to show bounding boxes
        show_masks: Whether to show mask overlay
        figsize: Figure size (width, height)
        
    Returns:
        Matplotlib figure if output_path is None
    """
    # Load image
    if isinstance(image, str):
        img = Image.open(image).convert("RGB")
    else:
        img = image.convert("RGB")
    
    # Create subplots
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    # Original image
    axes[0].imshow(img)
    axes[0].set_title("Original Image")
    axes[0].axis("off")
    
    # Image with masks
    if show_masks:
        img_with_masks = overlay_masks(img, result.masks)
        axes[1].imshow(img_with_masks)
        axes[1].set_title(f"Segmentation Masks ({len(result.segments)} segments)")
        axes[1].axis("off")
    else:
        axes[1].imshow(img)
        axes[1].set_title("No Masks")
        axes[1].axis("off")
    
    # Image with bounding boxes
    if show_boxes:
        img_with_boxes = draw_bounding_boxes(img, result, show_labels=True)
        axes[2].imshow(img_with_boxes)
        axes[2].set_title("Bounding Boxes & Labels")
        axes[2].axis("off")
    else:
        axes[2].imshow(img)
        axes[2].set_title("No Boxes")
        axes[2].axis("off")
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"✅ Saved visualization to {output_path}")
        plt.close()
        return None
    else:
        return fig


def export_segments_to_dataframe(result: SegmentationResult) -> pd.DataFrame:
    """
    Export segmentation results to pandas DataFrame.
    
    Args:
        result: SegmentationResult
        
    Returns:
        DataFrame with segment metadata
    """
    data = []
    for seg in result.segments:
        data.append({
            'segment_id': seg.segment_id,
            'name': seg.name,
            'score': seg.score,
            'area_pixels': seg.area,
            'centroid_x': seg.centroid[0],
            'centroid_y': seg.centroid[1],
            'bbox_x1': seg.bbox[0],
            'bbox_y1': seg.bbox[1],
            'bbox_x2': seg.bbox[2],
            'bbox_y2': seg.bbox[3],
            'bbox_width': seg.bbox[2] - seg.bbox[0],
            'bbox_height': seg.bbox[3] - seg.bbox[1],
        })
    
    return pd.DataFrame(data)


def export_segments_to_csv(
    result: SegmentationResult,
    output_path: str
):
    """
    Export segmentation results to CSV file.
    
    Args:
        result: SegmentationResult
        output_path: Path to save CSV file
    """
    df = export_segments_to_dataframe(result)
    df.to_csv(output_path, index=False)
    print(f"✅ Saved {len(df)} segments to {output_path}")


def crop_segments(
    image: Union[str, Image.Image],
    result: SegmentationResult,
    output_dir: str,
    padding: int = 10
) -> List[str]:
    """
    Crop individual segments from image and save them.
    
    Args:
        image: PIL Image or path to image
        result: SegmentationResult
        output_dir: Directory to save cropped segments
        padding: Padding around bounding box in pixels
        
    Returns:
        List of paths to saved crop images
    """
    # Load image
    if isinstance(image, str):
        img = Image.open(image).convert("RGB")
    else:
        img = image.convert("RGB")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    saved_paths = []
    
    for segment in result.segments:
        x1, y1, x2, y2 = [int(v) for v in segment.bbox]
        
        # Add padding
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(img.width, x2 + padding)
        y2 = min(img.height, y2 + padding)
        
        # Crop
        cropped = img.crop((x1, y1, x2, y2))
        
        # Save
        output_file = output_path / f"segment_{segment.segment_id:03d}_{segment.name}.png"
        cropped.save(output_file)
        saved_paths.append(str(output_file))
    
    print(f"✅ Saved {len(saved_paths)} cropped segments to {output_dir}")
    return saved_paths


def create_video_summary(
    video_result: VideoSegmentationResult,
    output_path: str,
    sample_frames: int = 10
):
    """
    Create a summary visualization of video segmentation results.
    
    Args:
        video_result: VideoSegmentationResult
        output_path: Path to save summary figure
        sample_frames: Number of frames to include in summary
    """
    # Sample frames evenly
    frame_indices = sorted(video_result.frames.keys())
    if len(frame_indices) > sample_frames:
        step = len(frame_indices) // sample_frames
        sampled_indices = frame_indices[::step][:sample_frames]
    else:
        sampled_indices = frame_indices
    
    # Create grid
    n_samples = len(sampled_indices)
    cols = min(5, n_samples)
    rows = (n_samples + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
    if rows == 1 and cols == 1:
        axes = np.array([[axes]])
    elif rows == 1 or cols == 1:
        axes = axes.reshape(rows, cols)
    
    for idx, frame_idx in enumerate(sampled_indices):
        row = idx // cols
        col = idx % cols
        ax = axes[row, col]
        
        frame_result = video_result.frames[frame_idx]
        
        # Create a simple visualization (just masks for summary)
        # In a real scenario, you'd load the actual frame image
        # For now, just show mask count info
        ax.text(
            0.5, 0.5,
            f"Frame {frame_idx}\n{len(frame_result.segments)} objects",
            ha='center', va='center',
            fontsize=12
        )
        ax.set_title(f"Frame {frame_idx}")
        ax.axis("off")
    
    # Hide unused subplots
    for idx in range(len(sampled_indices), rows * cols):
        row = idx // cols
        col = idx % cols
        axes[row, col].axis("off")
    
    plt.suptitle(
        f"Video Segmentation Summary\nPrompt: '{video_result.prompt}' | "
        f"Total Frames: {video_result.num_frames}",
        fontsize=14,
        y=1.02
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    print(f"✅ Saved video summary to {output_path}")


def export_video_summary_to_csv(
    video_result: VideoSegmentationResult,
    output_path: str
):
    """
    Export video segmentation summary to CSV.
    
    Args:
        video_result: VideoSegmentationResult
        output_path: Path to save CSV file
    """
    data = []
    
    for frame_idx, frame_result in video_result.frames.items():
        for segment in frame_result.segments:
            data.append({
                'frame_idx': frame_idx,
                'segment_id': segment.segment_id,
                'name': segment.name,
                'score': segment.score,
                'area_pixels': segment.area,
                'centroid_x': segment.centroid[0],
                'centroid_y': segment.centroid[1],
                'bbox_x1': segment.bbox[0],
                'bbox_y1': segment.bbox[1],
                'bbox_x2': segment.bbox[2],
                'bbox_y2': segment.bbox[3],
            })
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"✅ Saved video summary with {len(df)} segment-frames to {output_path}")


if __name__ == "__main__":
    print("SAM 3 Visualization & Export Utilities")
    print("=" * 50)
    print("\nAvailable functions:")
    print("  • overlay_masks() - Overlay colored masks on image")
    print("  • draw_bounding_boxes() - Draw boxes with labels")
    print("  • create_segmentation_visualization() - Full visualization")
    print("  • export_segments_to_csv() - Export to CSV")
    print("  • crop_segments() - Extract individual segments")
    print("  • create_video_summary() - Video result visualization")

