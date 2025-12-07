import os
import time
import shutil
import soundfile as sf
import librosa
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
from dotenv import load_dotenv

from elevenlabs import save
from elevenlabs.client import ElevenLabs
from elevenlabs.types import VoiceSettings

load_dotenv()

def get_client():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("❌ Error: ELEVENLABS_API_KEY environment variable not set.")
    return ElevenLabs(api_key=api_key)

def create_voice_clone(client, reference_audio_path: str) -> str:
    print(f"🧬 Creating Voice Clone from: {reference_audio_path}")
    try:
        with open(reference_audio_path, "rb") as f:
            voice = client.voices.ivc.create(
                name=f"Temp Clone {int(time.time())}",
                description="Pipeline clone",
                files=[f] 
            )
        return voice.voice_id
    except Exception as e:
        print(f"❌ Error creating voice clone: {e}")
        return None

def generate_speech(client, voice_id: str, text: str, output_file: str, speed: float = 1.0):
    api_speed = max(0.7, min(speed, 1.2))
    print(f"💬 Generating: '{text}' (Speed: {api_speed:.2f}x)")
    
    try:
        settings = VoiceSettings(
            stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=True, speed=api_speed 
        )
        audio = client.text_to_speech.convert(
            text=text, voice_id=voice_id, model_id="eleven_multilingual_v2", voice_settings=settings
        )
        save(audio, output_file)
        return output_file
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None

def process_video_replacement(video_path, output_path, start_time, stop_time, text, speaker_wav):
    """
    Main insertion logic. Uses a specific speaker_wav to clone the voice.
    """
    client = get_client()
    
    # Temp files
    temp_gen = f"temp_gen_{int(time.time())}.mp3"
    voice_id = None 
    clip = None

    try:
        # 1. Setup
        print(f"🎬 Processing Video Segment: {start_time}-{stop_time}s")
        clip = VideoFileClip(video_path)
        target_duration = stop_time - start_time
        
        # 2. Clone Voice from the ISOLATED speaker wav (passed from pipeline)
        if not os.path.exists(speaker_wav):
            raise FileNotFoundError(f"Speaker WAV not found: {speaker_wav}")
            
        voice_id = create_voice_clone(client, speaker_wav)
        if not voice_id: return None

        # 3. Generate Audio (Try 1.0x first)
        if not generate_speech(client, voice_id, text, temp_gen, speed=1.0): return None

        y, sr = librosa.load(temp_gen, sr=None)
        gen_duration = librosa.get_duration(y=y, sr=sr)

        # 4. Check Fit & Speed adjustment
        if gen_duration > target_duration:
            print("⚠️  Audio too long. Speeding up...")
            needed_speed = gen_duration / target_duration
            if needed_speed > 1.2: needed_speed = 1.2
            
            if generate_speech(client, voice_id, text, temp_gen, speed=needed_speed):
                y, sr = librosa.load(temp_gen, sr=None)
                gen_duration = librosa.get_duration(y=y, sr=sr)
        
        # 5. Strategic Placement (Center)
        padding_needed = max(0, (target_duration - gen_duration) / 2)
        start_pos = start_time + padding_needed

        # 6. Mixing
        original_audio = clip.audio
        part1 = original_audio.subclipped(0, start_time)
        new_part = AudioFileClip(temp_gen).with_start(start_pos)
        part3 = original_audio.subclipped(stop_time, clip.duration).with_start(stop_time)
        
        final_audio = CompositeAudioClip([part1, new_part, part3])
        final_clip = clip.with_audio(final_audio)
        
        print(f"💾 Writing result to {output_path}...")
        final_clip.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            logger=None
        )
        return output_path

    except Exception as e:
        print(f"❌ Error in insertion: {e}")
        return None
        
    finally:
        # Cleanup
        if os.path.exists(temp_gen): os.remove(temp_gen)
        if os.path.exists("temp-audio.m4a"): os.remove("temp-audio.m4a")
        
        if voice_id:
            try:
                client.voices.delete(voice_id)
                print(f"🗑️  Deleted temporary voice {voice_id}")
            except: pass
            
        if clip: clip.close()