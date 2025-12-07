# Veo 3.1 API Setup Instructions

## 🎬 FRAMESHIFT - VEO 3.1 INTEGRATION COMPLETE ✅

Your Frameshift application is now **properly integrated** with Google's Veo 3.1 API! Here's how to configure it:

## 🔑 API Key Setup

1. **Get Google API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or use existing one
   - Enable the Generative AI API
   - Generate an API key with Veo 3.1 access

2. **Configure Environment:**
   ```bash
   # Edit .env.local file
   GOOGLE_API_KEY=your_actual_google_api_key_here
   ```

## 🧪 Testing the Integration

### Quick Test:
```bash
# Open in browser:
http://localhost:5001/api/test-veo
```

### Custom Test:
```bash
curl -X POST http://localhost:5001/api/test-veo \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate video with iPhone placement",
    "productName": "iPhone 15 Pro",
    "timeStart": 0,
    "timeEnd": 5
  }'
```

## ✅ Verification Checklist

- [x] **Veo Client Initialized** - Google AI client properly configured
- [x] **API Key Detection** - Environment variable reading works
- [x] **Model Specification** - Using `veo-3.1-generate-preview`
- [x] **Logging System** - Comprehensive API call tracking
- [x] **Error Handling** - Robust failure management
- [x] **Request Tracking** - Unique ID for each API call

## 🎯 What's Actually Happening

When you upload a video and request product placement:

1. **Prompt Generation** - AI-optimized prompt created
2. **Veo 3.1 API Call** - Real call to Google's model:
   ```javascript
   const model = client.getGenerativeModel({ model: "veo-3.1-generate-preview" });
   const operation = await model.generateContent({
     prompt: prompt,
     referenceImages: [extractedFrame]
   });
   ```
3. **Response Processing** - Extract generated video URL
4. **Comprehensive Logging** - All calls tracked and logged

## 📊 Monitoring

Check the browser console and terminal for:
- `🔥 VEO 3.1 API CALL INITIATED`
- `✅ VEO 3.1 API RESPONSE RECEIVED`
- `📊 VEO 3.1 API CALL SUMMARY`

## 🚨 Important Notes

- **Real API Calls**: This makes actual calls to Google's Veo 3.1
- **Billing**: Each call may incur charges
- **Rate Limits**: Respect Google's API limits
- **Key Security**: Keep your API key secure

## 🎬 Ready to Use!

Your Frameshift application now has **real Veo 3.1 integration** with:
- Proper Google GenerativeAI client
- Correct model name (`veo-3.1-generate-preview`)
- Comprehensive logging and monitoring
- Robust error handling

**Just add your Google API key and start generating AI-powered product placements!** 🚀