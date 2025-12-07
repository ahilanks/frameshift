export interface GrokContextRequest {
  text?: string;
  audioTranscription?: string;
  sceneDescription?: string;
}

export interface GrokContextResponse {
  summary: string;
  contextualInfo: string;
}

class GrokClient {
  private apiKey: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = process.env.GROK_API_KEY || '';
    this.baseUrl = process.env.GROK_API_BASE || 'https://api.x.ai';
  }

  async extractContext(request: GrokContextRequest): Promise<string | null> {
    try {
      const prompt = this.buildContextPrompt(request);

      const response = await fetch(`${this.baseUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({
          model: 'grok-2-1212',
          messages: [
            {
              role: 'system',
              content: 'You are a helpful assistant that provides concise scene summaries for video content analysis. Focus on visual elements, setting, mood, and context that would be relevant for product placement.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          max_tokens: 200,
          temperature: 0.7,
        }),
      });

      if (!response.ok) {
        console.warn('Grok API call failed:', response.statusText);
        return null;
      }

      const data = await response.json();
      return data.choices?.[0]?.message?.content?.trim() || null;
    } catch (error) {
      console.warn('Grok context extraction failed:', error);
      // Grok is optional, so we return null on failure
      return null;
    }
  }

  private buildContextPrompt(request: GrokContextRequest): string {
    let prompt = 'Please provide a brief, contextual summary of this video content:\n\n';

    if (request.text) {
      prompt += `Text content: ${request.text}\n`;
    }

    if (request.audioTranscription) {
      prompt += `Audio transcription: ${request.audioTranscription}\n`;
    }

    if (request.sceneDescription) {
      prompt += `Scene description: ${request.sceneDescription}\n`;
    }

    prompt += '\nFocus on:\n- Visual setting and environment\n- Mood and atmosphere\n- Objects and elements visible\n- Lighting and time of day\n- Any text or signage\n\nKeep response under 150 words.';

    return prompt;
  }
}

export const grokClient = new GrokClient();