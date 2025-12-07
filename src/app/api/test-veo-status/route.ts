import { NextResponse } from 'next/server';

export async function GET() {
  const googleApiKey = process.env.GOOGLE_API_KEY;
  const veoApiKey = process.env.VEO_API_KEY;
  const geminiApiKey = process.env.GEMINI_API_KEY;
  const xaiApiKey = process.env.XAI_API_KEY;
  const grokApiKey = process.env.GROK_API_KEY;

  // Check which API key would be used by VeoClient
  const activeApiKey = veoApiKey || geminiApiKey || googleApiKey || '';
  const hasValidKey = activeApiKey && activeApiKey !== 'your_google_api_key_here';

  return NextResponse.json({
    status: 'API Configuration Check',
    keys: {
      veoApiKey: veoApiKey ? (veoApiKey === 'your_google_api_key_here' ? 'PLACEHOLDER' : 'CONFIGURED') : 'MISSING',
      geminiApiKey: geminiApiKey ? (geminiApiKey === 'your_google_api_key_here' ? 'PLACEHOLDER' : 'CONFIGURED') : 'MISSING',
      googleApiKey: googleApiKey ? (googleApiKey === 'your_google_api_key_here' ? 'PLACEHOLDER' : 'CONFIGURED') : 'MISSING',
      xaiApiKey: xaiApiKey ? 'CONFIGURED' : 'MISSING',
      grokApiKey: grokApiKey ? 'CONFIGURED' : 'MISSING'
    },
    activeApiKey: hasValidKey ? `Configured (${activeApiKey.slice(-4)})` : 'None',
    recommendation: hasValidKey
      ? '🎉 Ready for REAL Veo 3.1 API calls!'
      : 'Add your Google API key to .env.local to enable real video modification',
    demoMode: !hasValidKey,
    veoModel: 'veo-3.1-generate-preview',
    timestamp: new Date().toISOString()
  });
}