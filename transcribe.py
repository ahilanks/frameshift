import os
import json
import subprocess
import assemblyai as aai

def transcribe_video(input_mp4_path, output_json_path):
    """
    Transcribes video using AssemblyAI and saves speaker-labeled JSON.
    """
    api_key = os.getenv("ASSEMBLY_API_KEY")
    if not api_key:
        raise ValueError("ASSEMBLY_API_KEY not found in environment variables.")
    
    aai.settings.api_key = api_key
    
    temp_audio = f"temp_transcribe_{os.path.basename(input_mp4_path)}.wav"

    try:
        print(f"🔊 Extracting audio from {input_mp4_path}...")
        # 1. EXTRACT AUDIO
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", input_mp4_path,
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                temp_audio
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 2. TRANSCRIBE WITH SPEAKER LABELS
        print("📝 Transcribing with AssemblyAI...")
        config = aai.TranscriptionConfig(speaker_labels=True)
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(temp_audio, config)

        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(transcript.error)

        # 3. BUILD JSON STRUCTURE
        dialogue = []
        for utt in transcript.utterances:
            dialogue.append(
                {
                    "speaker": f"SPEAKER_{utt.speaker}",
                    "start_ms": utt.start,
                    "end_ms": utt.end,
                    "duration_ms": utt.end - utt.start,
                    "text": utt.text
                }
            )

        data = {
            "source_video": input_mp4_path,
            "num_speakers": len(set(d["speaker"] for d in dialogue)),
            "segments": dialogue
        }

        # 4. WRITE JSON
        with open(output_json_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Transcript saved to {output_json_path}")
        return data

    finally:
        # 5. CLEANUP
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

if __name__ == "__main__":
    # Allow standalone usage
    import sys
    if len(sys.argv) > 1:
        transcribe_video(sys.argv[1], "output.json")