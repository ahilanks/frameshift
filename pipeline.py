import os
import sys
from dotenv import load_dotenv

# Import local modules
import transcribe
import analyze_video
import isolate_speaker
import voice_insertion

# Load Env
load_dotenv()

def run_pipeline(input_video_path):
    if not os.path.exists(input_video_path):
        print(f"❌ Error: Input file '{input_video_path}' does not exist.")
        return

    # Directories for artifacts
    artifacts_dir = "pipeline_artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # 1. TRANSCRIBE
    print("\n" + "="*50)
    print("STEP 1: TRANSCRIBE VIDEO")
    print("="*50)
    json_path = os.path.join(artifacts_dir, "transcript.json")
    transcript_data = transcribe.transcribe_video(input_video_path, json_path)

    # 2. ANALYZE
    print("\n" + "="*50)
    print("STEP 2: ANALYZE FOR BRAND PLACEMENT")
    print("="*50)
    analysis = analyze_video.analyze_json_for_placements(transcript_data)
    
    if not analysis.replacements:
        print("No brand placements found. Exiting.")
        return

    # 3. ISOLATE SPEAKERS (Only for speakers involved in replacements)
    print("\n" + "="*50)
    print("STEP 3: ISOLATE SPEAKER VOICES")
    print("="*50)
    
    unique_speakers = set(r.speaker for r in analysis.replacements)
    speaker_wav_map = {}

    for speaker in unique_speakers:
        wav_path = os.path.join(artifacts_dir, f"{speaker}_clean.wav")
        # We use the original video and original json to extract clean audio
        result_wav = isolate_speaker.isolate_specific_speaker(
            source_mp4=input_video_path,
            segments_json_path=json_path,
            target_speaker=speaker,
            output_wav=wav_path
        )
        if result_wav:
            speaker_wav_map[speaker] = result_wav

    # 4. VOICE INSERTION (Iterative)
    print("\n" + "="*50)
    print("STEP 4: VOICE INSERTION & VIDEO GENERATION")
    print("="*50)

    current_video = input_video_path
    final_output = f"final_branded_{os.path.basename(input_video_path)}"

    for i, rep in enumerate(analysis.replacements):
        print(f"\n🔄 Processing Replacement {i+1}/{len(analysis.replacements)}")
        print(f"   Brand: {rep.brand_used}")
        print(f"   Line:  \"{rep.new_line}\"")
        
        wav_source = speaker_wav_map.get(rep.speaker)
        if not wav_source:
            print(f"❌ Skipping: No audio model found for {rep.speaker}")
            continue

        # Define output for this step
        step_output = os.path.join(artifacts_dir, f"step_{i+1}.mp4")
        
        # Run insertion
        # Note: We use 'current_video' as input, so edits stack up
        success_path = voice_insertion.process_video_replacement(
            video_path=current_video,
            output_path=step_output,
            start_time=rep.timestamp_start,
            stop_time=rep.timestamp_end,
            text=rep.new_line,
            speaker_wav=wav_source
        )

        if success_path:
            current_video = success_path
        else:
            print("⚠️  Insertion failed for this step. Continuing with previous video state.")

    # Final Copy
    if current_video != input_video_path:
        import shutil
        shutil.copy(current_video, final_output)
        print("\n" + "="*50)
        print(f"🎉 PIPELINE COMPLETE!")
        print(f"Output Video: {final_output}")
        print("="*50)
    else:
        print("Pipeline finished but no changes were made.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <input_video.mp4>")
    else:
        run_pipeline(sys.argv[1])