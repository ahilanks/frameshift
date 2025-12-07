#!/usr/bin/env python3
"""
Simple Flask backend for the Frameshift video editing workflow.
"""
import os
import sys
import json
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from video.video_segment import segment_video
from video_edit_tracked import edit_video_with_tracked_object

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = Path(__file__).parent.parent / 'uploads'
VIDEO_SEGMENTS_FOLDER = Path(__file__).parent.parent / 'video_segments'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

UPLOAD_FOLDER.mkdir(exist_ok=True)
VIDEO_SEGMENTS_FOLDER.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size


def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


@app.route('/')
def index():
    """Serve the main UI"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    """Upload a video file"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
            return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv'}), 400
        
        # Save with unique filename
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex[:8]
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{unique_id}{ext}"
        
        filepath = app.config['UPLOAD_FOLDER'] / unique_filename
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'filepath': str(filepath)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload_reference', methods=['POST'])
def upload_reference():
    """Upload a reference image"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg'}), 400
        
        # Save with unique filename
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex[:8]
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{unique_id}{ext}"
        
        filepath = app.config['UPLOAD_FOLDER'] / unique_filename
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'filepath': str(filepath)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/segment_video', methods=['POST'])
def api_segment_video():
    """Run video segmentation"""
    try:
        data = request.get_json()
        
        video_path = data.get('video_path')
        text_prompt = data.get('text_prompt', 'objects')
        max_frames = data.get('max_frames', None)
        output_every_n = data.get('output_every_n', 1)
        
        if not video_path:
            return jsonify({'error': 'No video path provided'}), 400
        
        if not Path(video_path).exists():
            return jsonify({'error': 'Video file not found'}), 404
        
        # Run segmentation
        # We need to capture the run_dir that segment_video creates
        # Let's modify the approach to return the run_dir
        from sam import SAM3VideoSegmenter
        import cv2
        from PIL import Image
        import numpy as np
        
        segmenter = SAM3VideoSegmenter()
        
        print(f"\n{'='*60}")
        print(f"Video Segmentation Started")
        print(f"{'='*60}")
        print(f"Video: {video_path}")
        print(f"Prompt: {text_prompt}")
        print(f"Max frames: {max_frames or 'all'}")
        print(f"{'='*60}\n")
        
        result = segmenter.segment_video_with_text(
            video_path,
            text_prompt=text_prompt,
            max_frames=max_frames,
            output_every_n=output_every_n
        )
        
        print(f"\n✅ Found segments in {len(result.frames)} frames\n")
        
        # Create run directory
        run_id = uuid.uuid4().hex[:8]
        run_dir = VIDEO_SEGMENTS_FOLDER / f"run_{run_id}"
        run_dir.mkdir(exist_ok=True)
        
        print(f"Saving outputs in: {run_dir}\n")
        
        # Load video to extract frames
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Collect metadata
        video_metadata = {
            "video_path": video_path,
            "text_prompt": text_prompt,
            "total_video_frames": total_frames,
            "processed_frames": len(result.frames),
            "fps": fps,
            "frames": {}
        }
        
        # Process each frame
        for frame_idx in sorted(result.frames.keys()):
            frame_result = result.frames[frame_idx]
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame_bgr = cap.read()
            if not ret:
                continue
            
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            frame_image = Image.fromarray(frame_rgb)
            
            frame_dir = run_dir / f"frame_{frame_idx:06d}"
            frame_dir.mkdir(exist_ok=True)
            
            frame_metadata = {
                "frame_index": frame_idx,
                "timestamp_ms": (frame_idx / fps * 1000) if fps > 0 else 0,
                "num_segments": len(frame_result.segments),
                "segments": []
            }
            
            for segment in frame_result.segments:
                x1, y1, x2, y2 = [int(coord) for coord in segment.bbox]
                
                # Crop and save
                cropped = frame_image.crop((x1, y1, x2, y2))
                output_name = f"segment_{segment.segment_id}_crop.png"
                output_path = frame_dir / output_name
                cropped.save(output_path)
                
                # Save mask
                mask = frame_result.masks[segment.mask_index]
                mask_cropped = mask[y1:y2, x1:x2]
                mask_image = Image.fromarray((mask_cropped * 255).astype(np.uint8))
                mask_name = f"segment_{segment.segment_id}_mask.png"
                mask_path = frame_dir / mask_name
                mask_image.save(mask_path)
                
                frame_metadata["segments"].append({
                    "segment_id": segment.segment_id,
                    "name": segment.name,
                    "bbox": segment.bbox,
                    "area": float(segment.area),
                    "centroid": list(segment.centroid),
                    "score": float(segment.score),
                    "crop_file": output_name,
                    "mask_file": mask_name
                })
            
            video_metadata["frames"][frame_idx] = frame_metadata
            
            # Save frame image
            frame_path = frame_dir / "frame.png"
            frame_image.save(frame_path)
        
        cap.release()
        
        # Save metadata
        metadata_path = run_dir / "video_segments_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(video_metadata, f, indent=4)
        
        print(f"{'='*60}")
        print(f"✅ Video segmentation complete!")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'run_id': run_id,
            'run_dir': str(run_dir),
            'frames_processed': len(result.frames),
            'metadata': video_metadata
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/edit_video', methods=['POST'])
def api_edit_video():
    """Run video editing with tracked objects"""
    try:
        data = request.get_json()
        
        run_dir = data.get('run_dir')
        edit_prompt = data.get('edit_prompt')
        reference_images = data.get('reference_images', [])
        max_frames = data.get('max_frames', None)
        segment_ids = data.get('segment_ids', None)
        reuse_every_n_frames = data.get('reuse_every_n_frames', 1)
        
        if not run_dir:
            return jsonify({'error': 'No run directory provided'}), 400
        
        if not edit_prompt:
            return jsonify({'error': 'No edit prompt provided'}), 400
        
        if not Path(run_dir).exists():
            return jsonify({'error': 'Run directory not found'}), 404
        
        # Run video editing
        output_path = edit_video_with_tracked_object(
            run_dir=run_dir,
            edit_prompt=edit_prompt,
            reference_images=reference_images if reference_images else None,
            max_frames=max_frames,
            segment_ids=segment_ids,
            reuse_edit_every_n_frames=reuse_every_n_frames
        )
        
        return jsonify({
            'success': True,
            'output_path': str(output_path),
            'run_dir': run_dir
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/runs', methods=['GET'])
def list_runs():
    """List all segmentation runs"""
    try:
        runs = []
        if VIDEO_SEGMENTS_FOLDER.exists():
            for run_dir in sorted(VIDEO_SEGMENTS_FOLDER.iterdir(), reverse=True):
                if run_dir.is_dir() and run_dir.name.startswith('run_'):
                    metadata_path = run_dir / "video_segments_metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        
                        # Check if edited video exists
                        edited_video_path = run_dir / "edited_video.mp4"
                        has_edited_video = edited_video_path.exists()
                        
                        runs.append({
                            'run_id': run_dir.name.replace('run_', ''),
                            'run_dir': str(run_dir),
                            'video_path': metadata.get('video_path'),
                            'text_prompt': metadata.get('text_prompt'),
                            'frames_processed': metadata.get('processed_frames'),
                            'has_edited_video': has_edited_video
                        })
        
        return jsonify({'runs': runs})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/run/<run_id>', methods=['GET'])
def get_run_details(run_id):
    """Get details of a specific run"""
    try:
        run_dir = VIDEO_SEGMENTS_FOLDER / f"run_{run_id}"
        if not run_dir.exists():
            return jsonify({'error': 'Run not found'}), 404
        
        metadata_path = run_dir / "video_segments_metadata.json"
        if not metadata_path.exists():
            return jsonify({'error': 'Metadata not found'}), 404
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return jsonify({
            'success': True,
            'metadata': metadata
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<run_id>/edited_video', methods=['GET'])
def download_edited_video(run_id):
    """Download the edited video"""
    try:
        run_dir = VIDEO_SEGMENTS_FOLDER / f"run_{run_id}"
        video_path = run_dir / "edited_video.mp4"
        
        if not video_path.exists():
            return jsonify({'error': 'Edited video not found'}), 404
        
        return send_file(video_path, as_attachment=True, download_name=f"edited_{run_id}.mp4")
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preview/<run_id>/frame/<int:frame_idx>/segment/<int:segment_id>', methods=['GET'])
def preview_segment(run_id, frame_idx, segment_id):
    """Get a preview image of a segment"""
    try:
        run_dir = VIDEO_SEGMENTS_FOLDER / f"run_{run_id}"
        frame_dir = run_dir / f"frame_{frame_idx:06d}"
        segment_path = frame_dir / f"segment_{segment_id}_crop.png"
        
        if not segment_path.exists():
            return jsonify({'error': 'Segment image not found'}), 404
        
        return send_file(segment_path, mimetype='image/png')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Frameshift Video Editor - Frontend Server")
    print("="*60)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Segments folder: {VIDEO_SEGMENTS_FOLDER}")
    print("="*60)
    print("\n🚀 Starting server at http://localhost:5001\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)

