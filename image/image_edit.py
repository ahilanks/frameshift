from pathlib import Path
from typing import List

from google import genai
from google.genai import types
from PIL import Image

# Make sure GEMINI_API_KEY is set in your environment
# export GEMINI_API_KEY="your-key-here"
client = genai.Client()

def edit_image_with_references(
    base_image_path: str,
    reference_image_paths: List[str],
    output_path: str,
    prompt: str,
    aspect_ratio: str = None,   # Auto-detected from base image if None
    resolution: str = None,     # Auto-detected from base image if None
):
    """
    Use Nano Banana Pro (gemini-3-pro-image-preview) to edit a base image
    using multiple reference images as guidance.

    base_image_path: path to the original image you want to edit
    reference_image_paths: list of paths to reference images (logos, styles, characters, etc.)
    output_path: where to save the edited image
    prompt: natural language description of the edit to apply
    aspect_ratio: output aspect ratio (auto-detected from base image if None)
    resolution: output resolution (auto-detected from base image if None)
    """

    # Load base + reference images
    base_image = Image.open(base_image_path)
    reference_images = [Image.open(p) for p in reference_image_paths]
    
    # Auto-detect aspect ratio and resolution from base image if not provided
    if aspect_ratio is None:
        width, height = base_image.size
        # Map to nearest valid aspect ratio
        # Valid options: '1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'
        valid_ratios = {
            "1:1": 1.0,
            "2:3": 2/3,
            "3:2": 3/2,
            "3:4": 3/4,
            "4:3": 4/3,
            "4:5": 4/5,
            "5:4": 5/4,
            "9:16": 9/16,
            "16:9": 16/9,
            "21:9": 21/9,
        }
        
        actual_ratio = width / height
        # Find the closest valid ratio
        closest_ratio = min(valid_ratios.items(), key=lambda x: abs(x[1] - actual_ratio))
        aspect_ratio = closest_ratio[0]
        print(f"Auto-detected aspect ratio: {aspect_ratio} (closest to {width}x{height} = {actual_ratio:.2f})")
    
    if resolution is None:
        width, height = base_image.size
        # Determine resolution based on image size
        max_dim = max(width, height)
        if max_dim >= 3000:
            resolution = "4K"
        elif max_dim >= 1500:
            resolution = "2K"
        else:
            resolution = "1K"
        print(f"Auto-detected resolution: {resolution} from {width}x{height}")

    # Build contents: prompt + base image + reference images
    contents = [prompt, base_image, *reference_images]

    # Note: When doing image editing (passing input images), the output will 
    # match the input image dimensions automatically. Config parameters may not be supported.
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
    )

    # Grab the first image in the response and save it
    edited_image = None
    for part in response.parts:
        if part.text is not None:
            print(f"Model response: {part.text}")
        elif part.inline_data is not None:
            edited_image = part.as_image()
            break

    if edited_image is None:
        raise RuntimeError("Model did not return an image.")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    edited_image.save(output_path)
    print(f"Saved edited image to {output_path}")


if __name__ == "__main__":
    # Example usage:
    # base = "segments/run_e0c00132/segment_11_crop.png"
    base = "media/image.png"
    refs = [
        "media/ref_logo.png",        # e.g., brand logo
    ]
    out = "outputs/run_e0c00132/edited_frame_all.png"

    prompt = (
        "Replace all the company logos in the base image with the reference logo from the  "
        "reference image. Match the scene's lighting and perspective. Keep everything else in the original image unchanged."
    )

    edit_image_with_references(
        base_image_path=base,
        reference_image_paths=refs,
        output_path=out,
        prompt=prompt,
        # aspect_ratio and resolution will auto-detect from base image
    )
