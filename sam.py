"""
SAM 3 Segmentation Module for Snap-to-Parts System

This module provides a unified interface for image and video segmentation
using Meta's SAM 3 (Segment Anything Model 3). It supports:
- Image segmentation with text prompts or automatic detection
- Video segmentation with text prompts and temporal tracking
- Multiple output formats (masks, bounding boxes, metadata)
"""

import torch
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from PIL import Image
import json


@dataclass
class SegmentMetadata:
    """Metadata for a single segmented component"""
    segment_id: int
    name: Optional[str]
    bbox: List[int]  # [x1, y1, x2, y2] in pixels
    area: float  # in pixels
    centroid: Tuple[float, float]  # (x, y) in pixels
    score: float  # confidence score
    mask_index: int  # index in the masks array
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['centroid'] = list(data['centroid'])
        return data


@dataclass
class SegmentationResult:
    """Complete segmentation result for an image"""
    image_path: Optional[str]
    segments: List[SegmentMetadata]
    masks: np.ndarray  # Binary masks [N, H, W]
    original_size: Tuple[int, int]  # (height, width)
    prompt: Optional[str] = None
    
    def to_dict(self, include_masks: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'image_path': self.image_path,
            'segments': [seg.to_dict() for seg in self.segments],
            'original_size': list(self.original_size),
            'prompt': self.prompt,
            'num_segments': len(self.segments)
        }
        if include_masks:
            result['masks'] = self.masks.tolist()
        return result
    
    def save_json(self, output_path: str, include_masks: bool = False):
        """Save segmentation results to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(include_masks=include_masks), f, indent=2)


@dataclass
class VideoSegmentationResult:
    """Complete segmentation result for a video"""
    video_path: Optional[str]
    frames: Dict[int, SegmentationResult]  # frame_idx -> SegmentationResult
    num_frames: int
    prompt: Optional[str] = None
    
    def to_dict(self, include_masks: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'video_path': self.video_path,
            'num_frames': self.num_frames,
            'prompt': self.prompt,
            'frames': {
                str(idx): frame.to_dict(include_masks=include_masks) 
                for idx, frame in self.frames.items()
            }
        }
    
    def save_json(self, output_path: str, include_masks: bool = False):
        """Save video segmentation results to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(include_masks=include_masks), f, indent=2)


class SAM3ImageSegmenter:
    """
    Image segmentation using SAM 3 with Promptable Concept Segmentation (PCS).
    
    Supports:
    - Text prompts (e.g., "screw", "handle", "dial")
    - Visual prompts (bounding boxes, points)
    - Automatic exhaustive segmentation
    """
    
    def __init__(self, model_name: str = "facebook/sam3", device: Optional[str] = None):
        """
        Initialize SAM3 image segmenter.
        
        Args:
            model_name: HuggingFace model identifier
            device: Device to run inference on. If None, automatically selects cuda/cpu
        """
        from transformers import Sam3Processor, Sam3Model
        
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🔧 Loading SAM3 Image Model on {self.device}...")
        
        self.model = Sam3Model.from_pretrained(model_name).to(self.device)
        self.processor = Sam3Processor.from_pretrained(model_name)
        
        print("✅ SAM3 Image Model loaded successfully")
    
    def segment_with_text(
        self,
        image: Union[str, Image.Image],
        text_prompt: str,
        threshold: float = 0.5,
        mask_threshold: float = 0.5
    ) -> SegmentationResult:
        """
        Segment all instances of objects matching the text prompt.
        
        Args:
            image: PIL Image or path to image file
            text_prompt: Text description of what to segment (e.g., "screw", "dial")
            threshold: Confidence threshold for detections
            mask_threshold: Threshold for mask binarization
            
        Returns:
            SegmentationResult containing masks and metadata
        """
        # Load image if path provided
        if isinstance(image, str):
            image_path = image
            image = Image.open(image).convert("RGB")
        else:
            image_path = None
        
        # Process inputs
        inputs = self.processor(images=image, text=text_prompt, return_tensors="pt").to(self.device)
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Post-process results
        results = self.processor.post_process_instance_segmentation(
            outputs,
            threshold=threshold,
            mask_threshold=mask_threshold,
            target_sizes=inputs.get("original_sizes").tolist()
        )[0]
        
        # Extract metadata
        segments = self._extract_segment_metadata(
            results['masks'],
            results['boxes'],
            results['scores'],
            text_prompt
        )
        
        return SegmentationResult(
            image_path=image_path,
            segments=segments,
            masks=results['masks'].cpu().numpy(),
            original_size=tuple(inputs.get("original_sizes")[0].tolist()),
            prompt=text_prompt
        )
    
    def segment_with_boxes(
        self,
        image: Union[str, Image.Image],
        boxes: List[List[int]],
        box_labels: Optional[List[int]] = None,
        threshold: float = 0.5,
        mask_threshold: float = 0.5
    ) -> SegmentationResult:
        """
        Segment objects defined by bounding boxes.
        
        Args:
            image: PIL Image or path to image file
            boxes: List of bounding boxes in xyxy format [[x1, y1, x2, y2], ...]
            box_labels: List of labels for each box (1=positive, 0=negative)
            threshold: Confidence threshold for detections
            mask_threshold: Threshold for mask binarization
            
        Returns:
            SegmentationResult containing masks and metadata
        """
        # Load image if path provided
        if isinstance(image, str):
            image_path = image
            image = Image.open(image).convert("RGB")
        else:
            image_path = None
        
        # Default to all positive boxes
        if box_labels is None:
            box_labels = [1] * len(boxes)
        
        # Format inputs
        input_boxes = [[boxes]]
        input_boxes_labels = [[box_labels]]
        
        # Process inputs
        inputs = self.processor(
            images=image,
            input_boxes=input_boxes,
            input_boxes_labels=input_boxes_labels,
            return_tensors="pt"
        ).to(self.device)
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Post-process results
        results = self.processor.post_process_instance_segmentation(
            outputs,
            threshold=threshold,
            mask_threshold=mask_threshold,
            target_sizes=inputs.get("original_sizes").tolist()
        )[0]
        
        # Extract metadata
        segments = self._extract_segment_metadata(
            results['masks'],
            results['boxes'],
            results['scores'],
            None
        )
        
        return SegmentationResult(
            image_path=image_path,
            segments=segments,
            masks=results['masks'].cpu().numpy(),
            original_size=tuple(inputs.get("original_sizes")[0].tolist()),
            prompt=f"boxes: {boxes}"
        )
    
    def segment_automatic(
        self,
        image: Union[str, Image.Image],
        points_per_batch: int = 64
    ) -> SegmentationResult:
        """
        Automatically segment all objects in the image without prompts.
        Uses the mask generation pipeline.
        
        Args:
            image: PIL Image or path to image file
            points_per_batch: Number of points to sample per batch
            
        Returns:
            SegmentationResult containing masks and metadata
        """
        from transformers import pipeline
        
        # Load image if path provided
        if isinstance(image, str):
            image_path = image
            pil_image = Image.open(image).convert("RGB")
        else:
            image_path = None
            pil_image = image
        
        # Create pipeline
        generator = pipeline(
            "mask-generation",
            model=self.model,
            device=0 if self.device == "cuda" else -1
        )
        
        # Generate masks
        outputs = generator(pil_image, points_per_batch=points_per_batch)
        
        # Convert to numpy
        masks = torch.stack(outputs['masks']).numpy()
        
        # Calculate bounding boxes and scores
        boxes = []
        scores = []
        for mask in masks:
            # Find bounding box
            rows = np.any(mask, axis=1)
            cols = np.any(mask, axis=0)
            if rows.any() and cols.any():
                y1, y2 = np.where(rows)[0][[0, -1]]
                x1, x2 = np.where(cols)[0][[0, -1]]
                boxes.append([x1, y1, x2, y2])
                scores.append(1.0)  # Default score for automatic segmentation
            else:
                boxes.append([0, 0, 0, 0])
                scores.append(0.0)
        
        boxes = torch.tensor(boxes)
        scores = torch.tensor(scores)
        
        # Extract metadata
        segments = self._extract_segment_metadata(
            torch.from_numpy(masks),
            boxes,
            scores,
            None
        )
        
        return SegmentationResult(
            image_path=image_path,
            segments=segments,
            masks=masks,
            original_size=(pil_image.height, pil_image.width),
            prompt="automatic"
        )
    
    def _extract_segment_metadata(
        self,
        masks: torch.Tensor,
        boxes: torch.Tensor,
        scores: torch.Tensor,
        prompt: Optional[str]
    ) -> List[SegmentMetadata]:
        """Extract metadata from segmentation results"""
        segments = []
        
        for idx, (mask, box, score) in enumerate(zip(masks, boxes, scores)):
            mask_np = mask.cpu().numpy() if isinstance(mask, torch.Tensor) else mask
            box_np = box.cpu().numpy() if isinstance(box, torch.Tensor) else box
            score_val = score.item() if isinstance(score, torch.Tensor) else float(score)
            
            # Calculate area
            area = float(mask_np.sum())
            
            # Calculate centroid
            if area > 0:
                y_coords, x_coords = np.where(mask_np > 0.5)
                centroid = (float(x_coords.mean()), float(y_coords.mean()))
            else:
                centroid = (float(box_np[0] + box_np[2]) / 2, float(box_np[1] + box_np[3]) / 2)
            
            segments.append(SegmentMetadata(
                segment_id=idx,
                name=prompt if prompt else f"segment_{idx}",
                bbox=box_np.tolist(),
                area=area,
                centroid=centroid,
                score=score_val,
                mask_index=idx
            ))
        
        # Sort by area (largest first)
        segments.sort(key=lambda s: s.area, reverse=True)
        
        return segments


class SAM3VideoSegmenter:
    """
    Video segmentation using SAM 3 with Promptable Concept Segmentation (PCS).
    
    Supports:
    - Text prompts for tracking objects across frames
    - Pre-loaded video processing (all frames available)
    - Streaming video processing (real-time frame-by-frame)
    """
    
    def __init__(self, model_name: str = "facebook/sam3", device: Optional[str] = None):
        """
        Initialize SAM3 video segmenter.
        
        Args:
            model_name: HuggingFace model identifier
            device: Device to run inference on. If None, automatically selects cuda/cpu
        """
        from transformers import Sam3VideoModel, Sam3VideoProcessor
        
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🔧 Loading SAM3 Video Model on {self.device}...")
        
        self.model = Sam3VideoModel.from_pretrained(model_name).to(
            self.device, dtype=torch.bfloat16
        )
        self.processor = Sam3VideoProcessor.from_pretrained(model_name)
        
        print("✅ SAM3 Video Model loaded successfully")
    
    def segment_video_with_text(
        self,
        video_path: str,
        text_prompt: str,
        max_frames: Optional[int] = None,
        output_every_n: int = 1
    ) -> VideoSegmentationResult:
        """
        Segment and track objects in video using text prompt.
        
        Args:
            video_path: Path to video file or directory of JPEG frames
            text_prompt: Text description of what to segment (e.g., "person", "tool")
            max_frames: Maximum number of frames to process (None = all)
            output_every_n: Save results every N frames (to reduce memory usage)
            
        Returns:
            VideoSegmentationResult containing per-frame masks and metadata
        """
        import cv2
        
        # Load video frames using OpenCV
        print(f"📹 Loading video from {video_path}...")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        video_frames = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames_to_read = min(max_frames, total_frames) if max_frames else total_frames
        
        for i in range(frames_to_read):
            ret, frame = cap.read()
            if not ret:
                break
            # Convert BGR to RGB and to PIL Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_frames.append(Image.fromarray(frame_rgb))
        
        cap.release()
        
        print(f"   Found {len(video_frames)} frames")
        
        # Initialize video inference session
        print(f"🔍 Initializing segmentation with prompt: '{text_prompt}'")
        inference_session = self.processor.init_video_session(
            video=video_frames,
            inference_device=self.device,
            processing_device="cpu",
            video_storage_device="cpu",
            dtype=torch.bfloat16,
        )
        
        # Add text prompt
        inference_session = self.processor.add_text_prompt(
            inference_session=inference_session,
            text=text_prompt,
        )
        
        # Process all frames
        print(f"⚙️  Processing frames...")
        outputs_per_frame = {}
        
        for model_outputs in self.model.propagate_in_video_iterator(
            inference_session=inference_session,
            max_frame_num_to_track=len(video_frames)
        ):
            frame_idx = model_outputs.frame_idx
            
            # Only save every Nth frame
            if frame_idx % output_every_n == 0:
                processed_outputs = self.processor.postprocess_outputs(
                    inference_session, model_outputs
                )
                outputs_per_frame[frame_idx] = processed_outputs
                
                if (frame_idx + 1) % 10 == 0:
                    print(f"   Processed {frame_idx + 1}/{len(video_frames)} frames...")
        
        print(f"✅ Segmentation complete! Processed {len(video_frames)} frames")
        
        # Convert to VideoSegmentationResult
        frame_results = {}
        for frame_idx, outputs in outputs_per_frame.items():
            # Create SegmentationResult for this frame
            segments = []
            for i, (obj_id, box, score) in enumerate(zip(
                outputs['object_ids'].tolist(),
                outputs['boxes'].tolist(),
                outputs['scores'].tolist()
            )):
                mask = outputs['masks'][i].cpu().numpy()
                area = float(mask.sum())
                
                # Calculate centroid
                if area > 0:
                    y_coords, x_coords = np.where(mask > 0.5)
                    centroid = (float(x_coords.mean()), float(y_coords.mean()))
                else:
                    centroid = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
                
                segments.append(SegmentMetadata(
                    segment_id=obj_id,
                    name=f"{text_prompt}_{obj_id}",
                    bbox=box,
                    area=area,
                    centroid=centroid,
                    score=score,
                    mask_index=i
                ))
            
            frame_results[frame_idx] = SegmentationResult(
                image_path=f"{video_path}/frame_{frame_idx:06d}",
                segments=segments,
                masks=outputs['masks'].cpu().numpy(),
                original_size=(inference_session.video_height, inference_session.video_width),
                prompt=text_prompt
            )
        
        return VideoSegmentationResult(
            video_path=video_path,
            frames=frame_results,
            num_frames=len(video_frames),
            prompt=text_prompt
        )
    
    def segment_video_streaming(
        self,
        video_path: str,
        text_prompt: str,
        max_frames: Optional[int] = 50
    ) -> VideoSegmentationResult:
        """
        Segment video in streaming mode (frame-by-frame, for real-time use).
        
        ⚠️ Note: Streaming mode may produce more false positives and duplicates
        compared to pre-loaded video inference.
        
        Args:
            video_path: Path to video file or directory of JPEG frames
            text_prompt: Text description of what to segment
            max_frames: Maximum number of frames to process
            
        Returns:
            VideoSegmentationResult containing per-frame masks and metadata
        """
        import cv2
        
        # Load video frames using OpenCV
        print(f"📹 Loading video from {video_path}...")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        video_frames = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames_to_read = min(max_frames, total_frames) if max_frames else total_frames
        
        for i in range(frames_to_read):
            ret, frame = cap.read()
            if not ret:
                break
            # Convert BGR to RGB and to PIL Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_frames.append(Image.fromarray(frame_rgb))
        
        cap.release()
        
        print(f"   Found {len(video_frames)} frames")
        
        # Initialize streaming session
        print(f"🔍 Initializing streaming segmentation with prompt: '{text_prompt}'")
        inference_session = self.processor.init_video_session(
            inference_device=self.device,
            processing_device="cpu",
            video_storage_device="cpu",
            dtype=torch.bfloat16,
        )
        
        # Add text prompt
        inference_session = self.processor.add_text_prompt(
            inference_session=inference_session,
            text=text_prompt,
        )
        
        # Process frames one by one (streaming)
        print(f"⚙️  Processing frames in streaming mode...")
        streaming_outputs = {}
        
        for frame_idx, frame in enumerate(video_frames):
            # Process the frame
            inputs = self.processor(images=frame, device=self.device, return_tensors="pt")
            
            # Streaming inference
            model_outputs = self.model(
                inference_session=inference_session,
                frame=inputs.pixel_values[0],
                reverse=False,
            )
            
            # Post-process
            processed_outputs = self.processor.postprocess_outputs(
                inference_session,
                model_outputs,
                original_sizes=inputs.original_sizes,
            )
            
            streaming_outputs[frame_idx] = processed_outputs
            
            if (frame_idx + 1) % 10 == 0:
                print(f"   Processed {frame_idx + 1}/{len(video_frames)} frames...")
        
        print(f"✅ Streaming segmentation complete!")
        
        # Convert to VideoSegmentationResult
        frame_results = {}
        for frame_idx, outputs in streaming_outputs.items():
            segments = []
            for i, (obj_id, box, score) in enumerate(zip(
                outputs['object_ids'].tolist(),
                outputs['boxes'].tolist(),
                outputs['scores'].tolist()
            )):
                mask = outputs['masks'][i].cpu().numpy()
                area = float(mask.sum())
                
                # Calculate centroid
                if area > 0:
                    y_coords, x_coords = np.where(mask > 0.5)
                    centroid = (float(x_coords.mean()), float(y_coords.mean()))
                else:
                    centroid = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
                
                segments.append(SegmentMetadata(
                    segment_id=obj_id,
                    name=f"{text_prompt}_{obj_id}",
                    bbox=box,
                    area=area,
                    centroid=centroid,
                    score=score,
                    mask_index=i
                ))
            
            frame_results[frame_idx] = SegmentationResult(
                image_path=f"{video_path}/frame_{frame_idx:06d}",
                segments=segments,
                masks=outputs['masks'].cpu().numpy(),
                original_size=tuple(inputs.original_sizes[0].tolist()),
                prompt=text_prompt
            )
        
        return VideoSegmentationResult(
            video_path=video_path,
            frames=frame_results,
            num_frames=len(video_frames),
            prompt=text_prompt
        )


# Convenience functions for quick usage
def segment_image(
    image_path: str,
    text_prompt: Optional[str] = None,
    device: Optional[str] = None
) -> SegmentationResult:
    """
    Quick function to segment an image.
    
    Args:
        image_path: Path to image file
        text_prompt: Optional text prompt (if None, uses automatic segmentation)
        device: Device to use (cuda/cpu)
        
    Returns:
        SegmentationResult
    """
    segmenter = SAM3ImageSegmenter(device=device)
    
    if text_prompt:
        return segmenter.segment_with_text(image_path, text_prompt)
    else:
        return segmenter.segment_automatic(image_path)


def segment_video(
    video_path: str,
    text_prompt: str,
    streaming: bool = False,
    max_frames: Optional[int] = None,
    device: Optional[str] = None
) -> VideoSegmentationResult:
    """
    Quick function to segment a video.
    
    Args:
        video_path: Path to video file or frame directory
        text_prompt: Text prompt for what to segment
        streaming: Use streaming mode (for real-time)
        max_frames: Maximum frames to process
        device: Device to use (cuda/cpu)
        
    Returns:
        VideoSegmentationResult
    """
    segmenter = SAM3VideoSegmenter(device=device)
    
    if streaming:
        return segmenter.segment_video_streaming(video_path, text_prompt, max_frames)
    else:
        return segmenter.segment_video_with_text(video_path, text_prompt, max_frames)


if __name__ == "__main__":
    print("SAM 3 Segmentation Module for Snap-to-Parts")
    print("=" * 50)
    print("\nThis module provides:")
    print("  • Image segmentation with SAM3ImageSegmenter")
    print("  • Video segmentation with SAM3VideoSegmenter")
    print("  • Automatic parts detection and metadata extraction")
    print("\nSee examples/ directory for usage examples.")

