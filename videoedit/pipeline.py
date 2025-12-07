"""
Simple end-to-end pipeline for replacing objects in videos using SAM-3
segmentation and Gemini ("Nano Banana") image editing.

Workflow:
1) Segment the video with a text prompt to find the target object(s).
2) Edit the segmented crops with Gemini.
3) Composite the edited crops back into the original frames and write a video.

You can choose specific frames to force a fresh edit (`--keyframes`) and how
long to reuse an edit in between (`--reuse-every`). This keeps the edit
consistent across consecutive frames without calling the model every frame.
"""

import argparse
import sys
from pathlib import Path

# Allow running the script from the repo root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from video.video_segment import segment_video
from video_edit_tracked import edit_video_with_tracked_object


def run_pipeline(
    video_path: Path | None,
    segment_prompt: str | None,
    edit_prompt: str,
    output_path: Path | None = None,
    reference_images: list[str] | None = None,
    max_frames: int | None = None,
    segment_ids: list[int] | None = None,
    reuse_every: int = 1,
    keyframes: list[int] | None = None,
    output_every_n: int = 1,
    existing_run: Path | None = None,
):
    """
    Segment a video, edit the target object, and stitch frames back together.

    Args:
        video_path: Path to the source video. Optional if you pass existing_run.
        segment_prompt: Text prompt for SAM3 segmentation.
        edit_prompt: Prompt for Gemini (Nano Banana) editing.
        output_path: Where to save the final video.
        reference_images: Optional list of reference image paths (logos, styles).
        max_frames: Cap the number of frames processed.
        segment_ids: Which segment IDs to edit (None = all).
        reuse_every: Reuse the last edit for N-1 frames, regenerate on every Nth.
        keyframes: Explicit frame numbers that must regenerate a fresh edit.
        output_every_n: Sample frames during segmentation (every Nth frame).
        existing_run: If provided, skips segmentation and uses that run dir.
    """
    if existing_run:
        run_dir = Path(existing_run)
        if not run_dir.exists():
            raise FileNotFoundError(f"Provided run directory does not exist: {run_dir}")
    else:
        if not video_path or not segment_prompt:
            raise ValueError("video_path and segment_prompt are required when not using --run-dir")
        run_dir = Path(
            segment_video(
                str(video_path),
                text_prompt=segment_prompt,
                max_frames=max_frames,
                output_every_n=output_every_n,
                save_masks=True,
            )
        )

    if output_path is None:
        output_path = run_dir / "edited_video.mp4"
    else:
        output_path = Path(output_path)

    print(f"\n{'='*60}")
    print("🚀 Starting object replacement pipeline")
    print(f"{'='*60}")
    print(f"Run dir: {run_dir}")
    print(f"Output:  {output_path}")
    print(f"Reuse every: {reuse_every} frame(s)")
    if keyframes:
        print(f"Keyframes: {sorted(set(keyframes))}")
    if segment_ids:
        print(f"Segments: {segment_ids}")
    if reference_images:
        print(f"References: {len(reference_images)} file(s)")
    print(f"{'='*60}\n")

    edit_video_with_tracked_object(
        run_dir=run_dir,
        edit_prompt=edit_prompt,
        output_path=output_path,
        reference_images=reference_images,
        max_frames=max_frames,
        segment_ids=segment_ids,
        reuse_edit_every_n_frames=reuse_every,
        regenerate_frames=keyframes,
    )

    return output_path


def parse_int_list(arg_val: str | None):
    if not arg_val:
        return None
    return [int(x.strip()) for x in arg_val.split(",") if x.strip()]


def build_parser():
    parser = argparse.ArgumentParser(
        description="Replace objects in video frames using SAM3 segmentation + Gemini editing.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--video", type=Path, help="Path to source video (skip if using --run-dir)")
    parser.add_argument("--segment-prompt", type=str, help="Text prompt for segmentation (e.g., 'logo', 'poster')")
    parser.add_argument("--edit-prompt", type=str, required=True, help="Prompt describing the edit to apply")
    parser.add_argument("--reference", action="append", help="Reference image path (can repeat)", default=[])
    parser.add_argument("--run-dir", type=Path, help="Existing segmentation run directory to reuse")
    parser.add_argument("--output", type=Path, help="Output video path")
    parser.add_argument("--segments", type=str, help="Comma-separated segment IDs to edit (e.g., 0,2)")
    parser.add_argument("--keyframes", type=str, help="Comma-separated frames to force regeneration")
    parser.add_argument("--reuse-every", type=int, default=1, help="Regenerate every N frames")
    parser.add_argument("--max-frames", type=int, help="Limit total frames processed")
    parser.add_argument("--stride", type=int, default=1, help="Segment every Nth frame to save time")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    segment_ids = parse_int_list(args.segments)
    keyframes = parse_int_list(args.keyframes)
    reference_images = args.reference or None

    run_pipeline(
        video_path=args.video,
        segment_prompt=args.segment_prompt,
        edit_prompt=args.edit_prompt,
        output_path=args.output,
        reference_images=reference_images,
        max_frames=args.max_frames,
        segment_ids=segment_ids,
        reuse_every=args.reuse_every,
        keyframes=keyframes,
        output_every_n=args.stride,
        existing_run=args.run_dir,
    )


if __name__ == "__main__":
    main()

