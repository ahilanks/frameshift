"""
Storage utilities for managing uploads and run outputs
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple


class StorageManager:
    """Manages file storage for uploads and processing runs"""
    
    def __init__(self, base_dir: str = "/home/ray/src/frameshift"):
        self.base_dir = Path(base_dir)
        self.uploads_dir = self.base_dir / "uploads"
        self.segments_dir = self.base_dir / "video_segments"
        
        # Create directories if they don't exist
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.segments_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory mapping of upload_id -> file info
        self._uploads: Dict[str, Dict] = {}
        
        # In-memory mapping of run_id -> upload_id
        self._runs: Dict[str, str] = {}
    
    def save_upload(self, file_data: bytes, filename: str) -> Tuple[str, Path]:
        """
        Save an uploaded file and return upload_id and filepath
        
        Args:
            file_data: File bytes
            filename: Original filename
            
        Returns:
            Tuple of (upload_id, filepath)
        """
        # Generate unique upload ID
        upload_id = uuid.uuid4().hex[:12]
        
        # Create upload directory
        upload_dir = self.uploads_dir / upload_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        filepath = upload_dir / filename
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        # Store metadata
        self._uploads[upload_id] = {
            'filepath': str(filepath),
            'filename': filename,
            'file_size': len(file_data),
            'upload_dir': str(upload_dir)
        }
        
        return upload_id, filepath
    
    def get_upload_info(self, upload_id: str) -> Optional[Dict]:
        """Get information about an upload"""
        return self._uploads.get(upload_id)
    
    def get_upload_path(self, upload_id: str) -> Optional[Path]:
        """Get the file path for an upload"""
        info = self.get_upload_info(upload_id)
        if info:
            return Path(info['filepath'])
        return None
    
    def create_run_dir(self, upload_id: str) -> Tuple[str, Path]:
        """
        Create a new run directory for processing
        
        Args:
            upload_id: Upload ID that this run is for
            
        Returns:
            Tuple of (run_id, run_dir)
        """
        # Generate unique run ID
        run_id = uuid.uuid4().hex[:8]
        
        # Create run directory under video_segments
        run_dir = self.segments_dir / f"run_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Map run_id to upload_id
        self._runs[run_id] = upload_id
        
        return run_id, run_dir
    
    def get_run_dir(self, run_id: str) -> Optional[Path]:
        """Get the directory for a run"""
        # Support both "run_id" and "run_run_id" formats
        if not run_id.startswith("run_"):
            run_dir = self.segments_dir / f"run_{run_id}"
        else:
            run_dir = self.segments_dir / run_id
        
        if run_dir.exists():
            return run_dir
        return None
    
    def get_upload_id_for_run(self, run_id: str) -> Optional[str]:
        """Get the upload_id associated with a run"""
        return self._runs.get(run_id)
    
    def list_runs(self) -> list:
        """List all run directories"""
        runs = []
        for run_dir in self.segments_dir.iterdir():
            if run_dir.is_dir() and run_dir.name.startswith("run_"):
                runs.append(run_dir.name)
        return sorted(runs)
    
    def get_frame_dir(self, run_id: str, frame_idx: int) -> Optional[Path]:
        """Get the directory for a specific frame in a run"""
        run_dir = self.get_run_dir(run_id)
        if not run_dir:
            return None
        
        frame_dir = run_dir / f"frame_{frame_idx:06d}"
        if frame_dir.exists():
            return frame_dir
        return None
    
    def get_metadata_path(self, run_id: str) -> Optional[Path]:
        """Get the metadata file path for a run"""
        run_dir = self.get_run_dir(run_id)
        if not run_dir:
            return None
        
        metadata_path = run_dir / "video_segments_metadata.json"
        if metadata_path.exists():
            return metadata_path
        return None
    
    def cleanup_upload(self, upload_id: str) -> bool:
        """
        Delete an upload and all associated runs
        
        Args:
            upload_id: Upload ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Find and delete all runs for this upload
        runs_to_delete = [run_id for run_id, uid in self._runs.items() if uid == upload_id]
        for run_id in runs_to_delete:
            run_dir = self.get_run_dir(run_id)
            if run_dir and run_dir.exists():
                shutil.rmtree(run_dir)
            del self._runs[run_id]
        
        # Delete the upload directory
        info = self.get_upload_info(upload_id)
        if info:
            upload_dir = Path(info['upload_dir'])
            if upload_dir.exists():
                shutil.rmtree(upload_dir)
            del self._uploads[upload_id]
            return True
        
        return False
    
    def cleanup_run(self, run_id: str) -> bool:
        """
        Delete a specific run directory
        
        Args:
            run_id: Run ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        run_dir = self.get_run_dir(run_id)
        if run_dir and run_dir.exists():
            shutil.rmtree(run_dir)
            if run_id in self._runs:
                del self._runs[run_id]
            return True
        return False


# Global storage manager instance
storage = StorageManager()

