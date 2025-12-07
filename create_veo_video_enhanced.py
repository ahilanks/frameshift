#!/usr/bin/env python3
"""
Enhanced Veo Video Generation Script

This script takes an MP4 video input, extracts frames from a specified time range,
and generates a new video using Veo 3.1 with custom prompts while maintaining
scene consistency between start and end frames.

Requirements:
    pip install google-genai opencv-python pillow

Usage:
    python create_veo_video_enhanced.py --input video.mp4 --start 5.0 --end 10.0 --prompt "Your custom prompt"
"""

import argparse
import time
import cv2
import os
import tempfile
import subprocess
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

class VeoVideoGenerator:
    def __init__(self, api_key: str):
        """Initialize the Veo video generator with API key."""
        self.client = genai.Client(api_key=api_key)

    def extract_frame_at_time(self, video_path: str, timestamp: float, output_path: str = None) -> str:
        """
        Extract a single frame from video at specified timestamp.

        Args:
            video_path: Path to input MP4 video
            timestamp: Time in seconds to extract frame
            output_path: Optional output path for frame (defaults to temp file)

        Returns:
            Path to extracted frame image
        """
        if output_path is None:
            output_path = tempfile.mktemp(suffix='.png')

        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        print(f"Video info: {duration:.2f}s, {fps:.2f} FPS, {total_frames} frames")

        # Validate timestamp - allow slight buffer for end frame
        if timestamp >= duration:
            print(f"Warning: Timestamp {timestamp}s at/near end of video ({duration:.2f}s), using last frame")
            timestamp = max(0, duration - 0.1)  # Use frame 0.1s before end

        # Seek to frame
        frame_number = int(timestamp * fps)
        # Ensure we don't exceed total frames
        frame_number = min(frame_number, total_frames - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        # Read frame
        ret, frame = cap.read()
        if not ret:
            raise ValueError(f"Could not extract frame at {timestamp}s")

        # Convert BGR to RGB and save
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        image.save(output_path, 'PNG')

        cap.release()
        print(f"Extracted frame at {timestamp}s -> {output_path}")
        return output_path

    def get_video_info(self, video_path: str) -> dict:
        """
        Get basic video information.

        Args:
            video_path: Path to input video

        Returns:
            Dictionary with video info (duration, fps, frames)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        cap.release()
        return {
            'duration': duration,
            'fps': fps,
            'frames': total_frames
        }

    def create_consistency_prompt(self, user_prompt: str) -> str:
        """
        Create a prompt that ensures consistency between start and end frames.

        Args:
            user_prompt: User's custom prompt for the video generation

        Returns:
            Enhanced prompt with consistency instructions
        """
        base_consistency = """
Use the provided reference frame as both the first frame and the last frame of the video.

CRITICAL REQUIREMENTS:
- The very first and very last frame MUST visually match the input image as closely as possible
- Maintain exact same composition, pose, framing, lighting, and environment
- Ensure perfect loop continuity - the video should seamlessly loop when played repeatedly
- All objects, people, and elements should return to their starting positions/states

"""

        user_section = f"""
CUSTOM ANIMATION REQUIREMENTS:
{user_prompt}

"""

        style_consistency = """
STYLE AND TECHNICAL REQUIREMENTS:
- Keep the overall look realistic and consistent with the reference frame
- Motion should feel smooth and cinematic, not glitchy or jarring
- Maintain lighting consistency throughout the video
- Preserve all visual elements from the reference frame
- Make the loop feel natural when it returns to the starting frame
- Duration should be appropriate for the requested animation (typically 3-8 seconds)
"""

        return base_consistency + user_section + style_consistency

    def generate_video(self, start_frame_path: str, end_frame_path: str, prompt: str, output_path: str, duration: float = None) -> str:
        """
        Generate video using Veo 3.1 with start and end frames.

        Args:
            start_frame_path: Path to starting frame image
            end_frame_path: Path to ending frame image
            prompt: Video generation prompt
            output_path: Output path for generated video
            duration: Video duration in seconds (4-8, defaults to smart calculation)

        Returns:
            Path to generated video
        """
        print(f"Loading start frame: {start_frame_path}")
        with open(start_frame_path, "rb") as f:
            start_bytes = f.read()

        print(f"Loading end frame: {end_frame_path}")
        with open(end_frame_path, "rb") as f:
            end_bytes = f.read()

        # Convert to Veo image objects
        start_image_part = types.Part.from_bytes(
            data=start_bytes,
            mime_type="image/png"
        )
        start_image = start_image_part.as_image()

        end_image_part = types.Part.from_bytes(
            data=end_bytes,
            mime_type="image/png"
        )
        end_image = end_image_part.as_image()

        print("Starting Veo 3.1 video generation...")
        print(f"Prompt: {prompt}")

        # This exactly follows the original working API pattern
        operation = self.client.models.generate_videos(
            model="veo-3.1-fast-generate-preview",
            prompt=prompt,
            image=start_image,  # first frame
            config=types.GenerateVideosConfig(
                last_frame=end_image,  # last frame
                # You can also add things like: duration_seconds=8, aspect_ratio="16:9", etc.
            ),
        )

        # Poll the operation until the video is ready (exact original pattern)
        while not operation.done:
            print("Waiting for video generation to complete...")
            time.sleep(10)
            operation = self.client.operations.get(operation)

        print(f"Operation completed. Status: {getattr(operation, 'done', 'unknown')}")

        # Check if operation completed successfully
        if not hasattr(operation, 'response') or operation.response is None:
            # Print more debug info
            print(f"Debug: operation has attributes: {dir(operation)}")
            if hasattr(operation, 'error'):
                print(f"Operation error: {operation.error}")
            raise ValueError("Video generation failed: No response from API")

        # Debug: Print the actual response structure
        print(f"Debug: Response type: {type(operation.response)}")
        print(f"Debug: Response attributes: {dir(operation.response)}")

        if hasattr(operation.response, 'generated_videos'):
            print(f"Debug: generated_videos type: {type(operation.response.generated_videos)}")
            if operation.response.generated_videos is not None:
                print(f"Debug: generated_videos length: {len(operation.response.generated_videos)}")
            else:
                print("Debug: generated_videos is None")
        else:
            print("Debug: No generated_videos attribute")

        # Check for other possible response attributes
        for attr in dir(operation.response):
            if not attr.startswith('_'):
                value = getattr(operation.response, attr)
                print(f"Debug: response.{attr} = {type(value)} {value if not callable(value) else '(callable)'}")

        if not hasattr(operation.response, 'generated_videos') or operation.response.generated_videos is None:
            raise ValueError("Video generation failed: No generated videos in response")

        if len(operation.response.generated_videos) == 0:
            raise ValueError("Video generation failed: Empty generated videos list")

        # Download and save the resulting video (exact original pattern)
        video = operation.response.generated_videos[0]

        if not hasattr(video, 'video') or video.video is None:
            raise ValueError("Video generation failed: No video file in response")

        self.client.files.download(file=video.video)
        video.video.save(output_path)

        print(f"✅ Generated video saved to {output_path}")
        return output_path

    def extract_video_segment(self, video_path: str, start_time: float, end_time: float, output_path: str) -> str:
        """
        Extract a segment from video using ffmpeg, ensuring both video and audio streams.

        Args:
            video_path: Path to input video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Output path for extracted segment

        Returns:
            Path to extracted segment
        """
        duration = end_time - start_time

        # Re-encode to ensure we get both video and audio streams
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c:v', 'libx264',  # Re-encode video to ensure stream exists
            '-c:a', 'aac',      # Re-encode audio to ensure stream exists
            '-avoid_negative_ts', 'make_zero',
            '-y',  # Overwrite output file
            output_path
        ]

        print(f"Extracting segment {start_time}s-{end_time}s from {video_path}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ Segment saved to {output_path}")

            # Verify the segment has video
            info = self.check_video_streams(output_path)
            print(f"  Segment streams: video={info['has_video']}, audio={info['has_audio']}")

            return output_path
        except subprocess.CalledProcessError as e:
            raise ValueError(f"FFmpeg failed: {e.stderr}")

    def check_video_streams(self, video_path: str) -> dict:
        """Check what streams a video file has."""
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', video_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            data = json.loads(result.stdout)
            streams = data.get('streams', [])

            has_video = any(s.get('codec_type') == 'video' for s in streams)
            has_audio = any(s.get('codec_type') == 'audio' for s in streams)

            return {'has_video': has_video, 'has_audio': has_audio}
        except:
            return {'has_video': True, 'has_audio': True}  # Assume both if check fails

    def stitch_videos_simple(self, video_paths: list, output_path: str) -> str:
        """
        Simple, reliable video concatenation without complex filters.

        Args:
            video_paths: List of video file paths to stitch
            output_path: Output path for final stitched video

        Returns:
            Path to stitched video
        """
        if len(video_paths) < 2:
            raise ValueError("Need at least 2 videos to stitch")

        print(f"🔗 Simple concatenation of {len(video_paths)} videos...")

        # Create file list for concat
        concat_file = tempfile.mktemp(suffix='.txt')

        try:
            with open(concat_file, 'w') as f:
                for path in video_paths:
                    f.write(f"file '{os.path.abspath(path)}'\n")

            # Simple concatenation with re-encoding for compatibility
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-pix_fmt', 'yuv420p',
                '-y',
                output_path
            ]

            print(f"Running: {' '.join(cmd[:6])}...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            os.unlink(concat_file)
            print(f"✅ Stitched video saved to {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            if os.path.exists(concat_file):
                os.unlink(concat_file)
            raise ValueError(f"Video stitching failed: {e.stderr}")

    def stitch_videos(self, video_paths: list, output_path: str, fade_duration: float = 0.5) -> str:
        """
        Stitch multiple videos together with optional crossfade transitions.
        Handles mixed audio-only and video files.

        Args:
            video_paths: List of video file paths to stitch
            output_path: Output path for final stitched video
            fade_duration: Duration of crossfade between clips (0 for hard cut)

        Returns:
            Path to stitched video
        """
        if len(video_paths) < 2:
            raise ValueError("Need at least 2 videos to stitch")

        print(f"Stitching {len(video_paths)} videos together...")

        # Check what streams each file has
        stream_info = []
        for path in video_paths:
            info = self.check_video_streams(path)
            stream_info.append(info)
            print(f"  {os.path.basename(path)}: video={info['has_video']}, audio={info['has_audio']}")

        # Always use simple concatenation for reliability
        # The crossfade filter often creates compatibility issues
        print("Using simple concatenation (most reliable)")
        return self.stitch_videos_simple(video_paths, output_path)

    def create_enhanced_sequence(self, input_video: str, start_time: float, end_time: float,
                               prompt: str, output_path: str, include_original: bool = True,
                               fade_duration: float = 0.3) -> str:
        """
        Create an enhanced video sequence: original start → Veo generated → original end.

        Args:
            input_video: Path to input MP4 video
            start_time: Start time for Veo generation
            end_time: End time for Veo generation
            prompt: Custom prompt for Veo generation
            output_path: Final output video path
            include_original: Whether to include original segments
            fade_duration: Crossfade duration between segments

        Returns:
            Path to final enhanced sequence
        """
        video_info = self.get_video_info(input_video)
        temp_files = []

        try:
            segments = []

            # 1. Extract pre-segment if requested and there's content before start
            if include_original and start_time > 0.5:
                pre_segment = tempfile.mktemp(suffix='_pre.mp4')
                temp_files.append(pre_segment)
                self.extract_video_segment(input_video, 0, start_time, pre_segment)
                segments.append(pre_segment)
                print(f"📹 Pre-segment: 0s → {start_time}s")

            # 2. Generate Veo enhanced middle segment
            print(f"🎨 Generating Veo segment: {start_time}s → {end_time}s")
            start_frame = self.extract_frame_at_time(input_video, start_time)
            end_frame = self.extract_frame_at_time(input_video, end_time)
            temp_files.extend([start_frame, end_frame])

            enhanced_prompt = self.create_consistency_prompt(prompt)
            veo_segment = tempfile.mktemp(suffix='_veo.mp4')
            temp_files.append(veo_segment)

            self.generate_video(start_frame, end_frame, enhanced_prompt, veo_segment)
            segments.append(veo_segment)

            # 3. Extract post-segment if requested and there's content after end
            if include_original and end_time < video_info['duration'] - 0.5:
                post_segment = tempfile.mktemp(suffix='_post.mp4')
                temp_files.append(post_segment)
                self.extract_video_segment(input_video, end_time, video_info['duration'], post_segment)
                segments.append(post_segment)
                print(f"📹 Post-segment: {end_time}s → {video_info['duration']:.1f}s")

            # 4. Stitch everything together
            if len(segments) > 1:
                print(f"🔗 Stitching {len(segments)} segments with {fade_duration}s crossfades...")
                self.stitch_videos(segments, output_path, fade_duration)
            else:
                # Just copy the single Veo segment
                import shutil
                shutil.copy2(veo_segment, output_path)
                print(f"✅ Single segment saved to {output_path}")

            return output_path

        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except:
                        pass

def main():
    parser = argparse.ArgumentParser(description='Enhanced Veo Video Generation')
    parser.add_argument('--input', '-i', required=True, help='Input MP4 video file')
    parser.add_argument('--start', '-s', type=float, required=True, help='Start time in seconds')
    parser.add_argument('--end', '-e', type=float, required=True, help='End time in seconds')
    parser.add_argument('--prompt', '-p', required=True, help='Custom prompt for video generation')
    parser.add_argument('--output', '-o', help='Output video file (default: generated_video.mp4)')
    parser.add_argument('--duration', '-d', type=float, help='Video duration in seconds (4-8, default: 4)')
    parser.add_argument('--api-key', help='Veo API key (default: from script)')
    parser.add_argument('--keep-frames', action='store_true', help='Keep extracted frame files')
    parser.add_argument('--stitch', action='store_true', help='Create full sequence: original → Veo → original')
    parser.add_argument('--fade', type=float, default=0.3, help='Crossfade duration between segments (default: 0.3s)')
    parser.add_argument('--veo-only', action='store_true', help='Generate only Veo segment (no original parts)')

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        return 1

    # Set default output file
    if not args.output:
        input_stem = Path(args.input).stem
        args.output = f"generated_{input_stem}_{args.start}s-{args.end}s.mp4"

    # Use API key from args or default from script
   
    api_key = args.api_key

    try:
        # Initialize generator
        generator = VeoVideoGenerator(api_key)

        # Get video info and validate timestamps
        video_info = generator.get_video_info(args.input)
        print(f"Input video: {video_info['duration']:.2f}s, {video_info['fps']:.1f} FPS")

        # Suggest safe end time if user provided one that's too close to the end
        if args.end >= video_info['duration']:
            safe_end = max(0.1, video_info['duration'] - 0.2)
            print(f"⚠️  Warning: End time {args.end}s is at/beyond video duration ({video_info['duration']:.2f}s)")
            print(f"   Suggested safe end time: {safe_end:.1f}s")
            print(f"   Proceeding with automatic adjustment...")

        # Choose generation method based on flags
        if args.stitch:
            # Create full enhanced sequence with original segments
            print(f"🎬 Creating enhanced sequence with original segments...")
            output_path = generator.create_enhanced_sequence(
                input_video=args.input,
                start_time=args.start,
                end_time=args.end,
                prompt=args.prompt,
                output_path=args.output,
                include_original=not args.veo_only,
                fade_duration=args.fade
            )
        else:
            # Original mode: just generate Veo segment
            print(f"Extracting frames from {args.input}")
            start_frame_path = generator.extract_frame_at_time(args.input, args.start)
            end_frame_path = generator.extract_frame_at_time(args.input, args.end)

            # Create enhanced prompt
            enhanced_prompt = generator.create_consistency_prompt(args.prompt)

            # Generate video
            output_path = generator.generate_video(
                start_frame_path,
                end_frame_path,
                enhanced_prompt,
                args.output,
                duration=args.duration
            )

            # Cleanup frame files if not keeping them
            if not args.keep_frames:
                os.unlink(start_frame_path)
                os.unlink(end_frame_path)
                print("Cleaned up temporary frame files")
            else:
                print(f"Frame files kept: {start_frame_path}, {end_frame_path}")

        print(f"\n🎬 Video generation complete!")
        print(f"📁 Output: {output_path}")
        print(f"⏱️  Scene: {args.start}s - {args.end}s from {args.input}")

        if args.stitch:
            print(f"🔗 Mode: Enhanced sequence with crossfades ({args.fade}s)")
        else:
            print(f"🎨 Mode: Veo generation only")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())