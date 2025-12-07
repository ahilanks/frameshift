import sys
import os
import uuid
import json

sys.path.append('.')

from sam import SAM3ImageSegmenter
from PIL import Image
import numpy as np


def segment_and_crop(image_path, text_prompt=None):
    segmenter = SAM3ImageSegmenter()
    image = Image.open(image_path).convert("RGB")

    # Run segmentation
    if text_prompt:
        result = segmenter.segment_with_text(image_path, text_prompt)
    else:
        result = segmenter.segment_automatic(image_path)

    print(f"Found {len(result.segments)} segments\n")

    # Base folder for all segment runs
    base_dir = "segments"
    os.makedirs(base_dir, exist_ok=True)

    # Create a random subfolder for this run
    run_id = uuid.uuid4().hex[:8]
    run_dir = os.path.join(base_dir, f"run_{run_id}")
    os.makedirs(run_dir, exist_ok=False)

    print(f"Saving outputs in: {run_dir}\n")

    # Collect metadata for JSON
    segments_metadata = []

    for segment in result.segments:
        print(f"Segment {segment.segment_id}:")
        print(f"  BBox: {segment.bbox}")
        print(f"  Area: {segment.area:.0f} px")
        print(f"  Score: {segment.score:.3f}")

        x1, y1, x2, y2 = segment.bbox
        cropped = image.crop((x1, y1, x2, y2))

        output_name = f"segment_{segment.segment_id}_crop.png"
        output_path = os.path.join(run_dir, output_name)
        cropped.save(output_path)
        print(f"  Saved: {output_path}\n")

        segments_metadata.append(
            {
                "segment_id": segment.segment_id,
                "bbox": segment.bbox,          # [x1, y1, x2, y2]
                "area": float(segment.area),   # ensure JSON-serializable
                "score": float(segment.score),
                "image_file": output_name,
            }
        )

    # Save metadata JSON in the same run directory
    metadata_path = os.path.join(run_dir, "segments_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(
            {
                "image_path": image_path,
                "text_prompt": text_prompt,
                "num_segments": len(segments_metadata),
                "segments": segments_metadata,
            },
            f,
            indent=4,
        )

    print(f"Metadata saved to: {metadata_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python image_segment.py <image_file> [prompt]")
        sys.exit(1)
    image_file = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else None

    segment_and_crop(image_file, prompt)
