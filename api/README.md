# FrameShift API Documentation

A FastAPI backend for video segmentation and editing with AI.

## Features

- **Video Upload**: Upload videos and get unique IDs for tracking
- **Video Segmentation**: Segment objects in videos using SAM2
- **Video Editing**: Edit tracked objects using Gemini image generation
- **File Management**: Organized storage with unique IDs per upload
- **Frame-level Access**: Get individual frames and segments

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn python-multipart pydantic
```

### 2. Start the Server

```bash
# From the frameshift directory
cd /home/ray/src/frameshift
python -m api.main

# Or using uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

The API will be available at `http://localhost:8000`

### 3. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check
```
GET /api/v1/health
```
Check if the API is running.

### Upload Video
```
POST /api/v1/upload
Content-Type: multipart/form-data

Parameters:
  - file: Video file to upload

Returns:
  - upload_id: Unique identifier for this upload
  - filepath: Server path to the uploaded file
  - filename: Original filename
  - file_size: Size in bytes
```

### Segment Video
```
POST /api/v1/segment
Content-Type: application/json

Body:
{
  "upload_id": "string",
  "text_prompt": "person" (optional),
  "max_frames": 100 (optional),
  "start_frame_idx": 0 (optional),
  "end_frame_idx": null (optional),
  "output_every_n": 1,
  "save_masks": true
}

Returns:
  - run_id: Unique identifier for this segmentation run
  - run_dir: Directory containing all outputs
  - frames: Dictionary of frame data with segments
```

### Edit Video
```
POST /api/v1/edit
Content-Type: application/json

Body:
{
  "run_id": "string",
  "edit_prompt": "add Nike logo to the shirt",
  "reference_images": ["path/to/logo.png"] (optional),
  "start_frame_idx": null (optional),
  "end_frame_idx": null (optional),
  "segment_ids": [0, 2] (optional - edit specific segments only),
  "model": "gemini-2.5-flash-image",
  "reuse_edit_every_n_frames": 1
}

Returns:
  - run_id: Run identifier
  - output_video_path: Path to edited video
  - total_frames: Number of frames processed
```

### Get Run Information
```
POST /api/v1/run/info
Content-Type: application/json

Body:
{
  "run_id": "string"
}

Returns:
  - Complete metadata about the run
  - Available frames
  - Total segments
```

### List Frames
```
POST /api/v1/run/frames
Content-Type: application/json

Body:
{
  "run_id": "string",
  "start_idx": 0 (optional),
  "end_idx": null (optional)
}

Returns:
  - List of frames with segment information
```

### Get Frame Details
```
POST /api/v1/run/frame
Content-Type: application/json

Body:
{
  "run_id": "string",
  "frame_idx": 0
}

Returns:
  - Frame information
  - Paths to frame image, crops, and masks
```

### Download Files
```
GET /api/v1/download/video/{run_id}
GET /api/v1/download/frame/{run_id}/{frame_idx}
GET /api/v1/download/segment/{run_id}/{frame_idx}/{segment_id}?type=crop
GET /api/v1/download/segment/{run_id}/{frame_idx}/{segment_id}?type=mask
```

### List All Runs
```
GET /api/v1/runs

Returns:
  - List of all run IDs
```

## Storage Structure

All uploads and outputs are organized by unique IDs:

```
frameshift/
├── uploads/
│   └── {upload_id}/
│       └── {original_filename}
│
└── video_segments/
    └── run_{run_id}/
        ├── video_segments_metadata.json
        ├── edited_video.mp4 (after editing)
        ├── frame_000000/
        │   ├── frame.png
        │   ├── segment_0_crop.png
        │   ├── segment_0_mask.png
        │   └── ...
        ├── frame_000001/
        └── ...
```

## Example Workflow

### Python Client Example

See `examples/client_example.py` for a complete working example.

```python
import requests

# 1. Upload video
with open("media/scene.mp4", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/upload",
        files={"file": f}
    )
upload_id = response.json()["upload_id"]

# 2. Segment video
response = requests.post(
    "http://localhost:8000/api/v1/segment",
    json={
        "upload_id": upload_id,
        "text_prompt": "person",
        "max_frames": 10,
        "save_masks": True
    }
)
run_id = response.json()["run_id"]

# 3. Edit video
response = requests.post(
    "http://localhost:8000/api/v1/edit",
    json={
        "run_id": run_id,
        "edit_prompt": "add a Nike logo to the shirt",
        "reference_images": ["media/ref_logo.png"],
        "segment_ids": [0]
    }
)
output_path = response.json()["output_video_path"]

# 4. Download edited video
response = requests.get(f"http://localhost:8000/api/v1/download/video/{run_id}")
with open("output.mp4", "wb") as f:
    f.write(response.content)
```

### cURL Examples

```bash
# Upload video
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@media/scene.mp4"

# Segment video
curl -X POST "http://localhost:8000/api/v1/segment" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "abc123def456",
    "text_prompt": "person",
    "max_frames": 10
  }'

# Edit video
curl -X POST "http://localhost:8000/api/v1/edit" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "c5cf4832",
    "edit_prompt": "add logo",
    "segment_ids": [0]
  }'

# Download edited video
curl -O "http://localhost:8000/api/v1/download/video/c5cf4832"
```

## Frontend Integration

The API is designed to be easily integrated with a frontend:

1. **File Upload**: Use FormData to upload videos
2. **Progress Tracking**: Use the run_id to query status
3. **Preview**: Download individual frames or segments
4. **Results**: Download the edited video

Example frontend workflow:
```javascript
// Upload
const formData = new FormData();
formData.append('file', videoFile);
const uploadRes = await fetch('/api/v1/upload', {
  method: 'POST',
  body: formData
});
const { upload_id } = await uploadRes.json();

// Segment
const segmentRes = await fetch('/api/v1/segment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    upload_id,
    text_prompt: 'person',
    max_frames: 100
  })
});
const { run_id } = await segmentRes.json();

// Edit
const editRes = await fetch('/api/v1/edit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    run_id,
    edit_prompt: 'add logo'
  })
});

// Download
window.location.href = `/api/v1/download/video/${run_id}`;
```

## Error Handling

All endpoints return standard HTTP status codes:
- 200: Success
- 400: Bad request (invalid parameters)
- 404: Resource not found
- 500: Server error

Error responses include a detail field:
```json
{
  "detail": "Upload not found: abc123"
}
```

## Environment Variables

Required for video editing:
```bash
export GOOGLE_API_KEY="your-gemini-api-key"
# or
export GEMINI_API_KEY="your-gemini-api-key"
```

## Notes

- Each upload gets a unique ID for organization
- All outputs are stored under the run's directory
- Frame indices are 0-based
- Segment IDs are assigned automatically during segmentation
- Reference images should be accessible from the server filesystem

