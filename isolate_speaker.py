import json
import subprocess
import os

def ms_to_seconds(ms):
    return ms / 1000

def isolate_specific_speaker(source_mp4, segments_json_path, target_speaker, output_wav):
    """
    Extracts all audio segments for a specific speaker and concatenates them 
    into a single wav file for voice cloning.
    """
    print(f"🎙️  Isolating audio for {target_speaker}...")
    
    temp_clips_dir = f"temp_clips_{target_speaker}"
    os.makedirs(temp_clips_dir, exist_ok=True)

    with open(segments_json_path) as f:
        data = json.load(f)

    segments = [s for s in data["segments"] if s["speaker"] == target_speaker]

    if not segments:
        print(f"⚠️ No segments found for {target_speaker}")
        return None

    clip_files = []

    # Extract segments
    for i, seg in enumerate(segments):
        start = ms_to_seconds(seg["start_ms"])
        duration = ms_to_seconds(seg["duration_ms"])
        clip_path = f"{temp_clips_dir}/clip_{i}.wav"
        clip_files.append(clip_path)

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", source_mp4,
                "-ss", str(start),
                "-t", str(duration),
                "-vn", "-ac", "1", "-ar", "16000",
                clip_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    # Concatenate
    concat_file = f"{temp_clips_dir}/concat.txt"
    with open(concat_file, "w") as f:
        for clip in clip_files:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_wav
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Cleanup
    for clip in clip_files:
        if os.path.exists(clip): os.remove(clip)
    if os.path.exists(concat_file): os.remove(concat_file)
    os.rmdir(temp_clips_dir)

    print(f"✅ Isolated audio saved to {output_wav}")
    return output_wav