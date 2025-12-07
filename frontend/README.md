# Frameshift Frontend

A simple web UI for the Frameshift video editing workflow.

## Features

- **Upload Video**: Upload your video file for processing
- **Segment Video**: Automatically segment objects in the video using SAM2
- **Edit Video**: Apply AI-powered edits to tracked objects across frames

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have the required environment variables:
```bash
export GOOGLE_API_KEY='your-gemini-api-key'
```

3. Start the server:
```bash
cd frontend
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5001
```

## Workflow

### Step 1: Upload Video
- Click "Choose Video" and select a video file (mp4, avi, mov, mkv)
- Click "Upload Video"

### Step 2: Segment Video
- Enter a text prompt describing what to segment (e.g., "person", "car", "shirt")
- (Optional) Configure advanced options:
  - Max frames: Limit how many frames to process
  - Output every N frames: Process every Nth frame for faster results
- Click "Run Segmentation"
- This will create a run directory with all segmented objects

### Step 3: Edit Video
- Enter an edit prompt (e.g., "add a Nike logo to the shirt in the direct center")
- (Optional) Upload reference images (logos, textures, etc.)
- (Optional) Configure advanced options:
  - Max frames to edit: Limit editing to first N frames
  - Segment IDs: Only edit specific segments (comma-separated, e.g., "0,2,5")
  - Reuse every N frames: Reuse AI edits across frames for faster processing
- Click "Run Video Edit"
- Download your edited video when complete!

## API Endpoints

- `POST /api/upload_video` - Upload a video file
- `POST /api/upload_reference` - Upload a reference image
- `POST /api/segment_video` - Run video segmentation
- `POST /api/edit_video` - Run video editing
- `GET /api/runs` - List all segmentation runs
- `GET /api/run/<run_id>` - Get details of a specific run
- `GET /api/download/<run_id>/edited_video` - Download edited video
- `GET /api/preview/<run_id>/frame/<frame_idx>/segment/<segment_id>` - Preview segment

## Notes

- Segmentation and editing can take several minutes depending on:
  - Video length and resolution
  - Number of frames processed
  - Number of objects to track
  - API response times
- Use the "max frames" and "reuse every N frames" options for faster testing
- The server stores all uploads and outputs in the parent directory

