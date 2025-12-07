import os
import json
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from xai_sdk import Client
from xai_sdk.chat import user, system

# Load environment variables
load_dotenv()

# --- Structured Output Schema ---
class LineReplacement(BaseModel):
    timestamp_start: float = Field(description="Start time (seconds).")
    timestamp_end: float = Field(description="End time (seconds).")
    speaker: str = Field(description="Speaker identifier (e.g., SPEAKER_A).")
    original_line: str = Field(description="Original dialogue.")
    brand_used: str = Field(description="Brand inserted.")
    new_line: str = Field(description="Rewritten line.")
    rationale: str = Field(description="Reasoning.")

class ScriptAnalysis(BaseModel):
    replacements: List[LineReplacement] = Field(description="List of opportunities.")

def analyze_json_for_placements(json_data):
    """
    Parses JSON transcript data and uses xai_sdk to identify brand opportunities.
    """
    xai_key = os.getenv("XAI_API_KEY")
    if not xai_key:
        raise ValueError("XAI_API_KEY not found.")

    print("🧠 Analyzing transcript for brand opportunities...")
    
    transcript_lines = []
    for segment in json_data.get('segments', []):
        start = segment.get('start_ms', 0.0) / 1000.0
        end = segment.get('end_ms', 0.0) / 1000.0
        speaker = segment.get('speaker', 'Unknown')
        text = segment.get('text', '')
        transcript_lines.append(f"[{start:.2f}-{end:.2f}] {speaker}: {text}")
    
    full_transcript_context = "\n".join(transcript_lines)

    client = Client(api_key=xai_key)

    system_prompt = (
        "You are a Global Brand Strategist and Script Editor. "
        "Your goal is to monetize video content by rewriting lines of dialogue to include "
        "The placement must feel seamless, as if the product naturally comes up in conversation"
    )

    user_prompt = f"""Analyze the transcript below. Identify lines could naturally feature some brand while not disrupting the conversation or meaning.

    ### Constraints:
    1. **Popular Brands Only:** Use brands that are well known and private.
    2. **Whole Line Replacement:** Rewrite the entire line changing only what is necessary.
    3. **Strict Timing:** The `new_line` must be very similar in length and duration of the `original_line`.
    4. **Speaker Accuracy:** Ensure the `speaker` field matches the speaker from the transcript exactly.

    TRANSCRIPT DATA:
    {full_transcript_context}
    """

    chat = client.chat.create(model="grok-2-latest")
    chat.append(system(system_prompt))
    chat.append(user(user_prompt))

    response, analysis = chat.parse(ScriptAnalysis)
    
    print(f"✅ Analysis complete. Found {len(analysis.replacements)} replacements.")
    return analysis

if __name__ == "__main__":
    if os.path.exists("speaker_dialogue.json"):
        with open("speaker_dialogue.json", "r") as f:
            data = json.load(f)
        analyze_json_for_placements(data)