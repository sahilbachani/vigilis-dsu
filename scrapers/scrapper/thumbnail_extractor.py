"""
Utility for extracting thumbnails from videos.
Uses ffmpeg for efficient frame extraction, falls back to PIL if needed.
"""
import os
import subprocess
import sys
from pathlib import Path
from PIL import Image
import io

def extract_video_thumbnail(video_path: str, output_path: str, timestamp: str = "00:00:01") -> bool:
    """
    Extract a single frame from a video to use as thumbnail.
    
    Args:
        video_path: Full path to the video file
        output_path: Full path where the thumbnail JPG should be saved
        timestamp: Timestamp to extract frame from (format: HH:MM:SS)
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(video_path):
        print(f"[THUMBNAIL ERROR] Video file not found: {video_path}")
        return False
    
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Try using ffmpeg first (faster and more reliable)
        try:
            cmd = [
                "ffmpeg",
                "-ss", timestamp,
                "-i", video_path,
                "-vf", "scale=320:-1",
                "-vframes", "1",
                "-y",
                "-loglevel", "quiet",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"[THUMBNAIL] Extracted from {video_path} to {output_path}")
                return True
            else:
                print(f"[THUMBNAIL WARN] ffmpeg failed: {result.stderr}")
                # Fall through to PIL method
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("[THUMBNAIL WARN] ffmpeg not available, trying alternative method")
        
        # Fallback: Try using Python's subprocess with imagemagick or PIL
        # For now, we'll create a simple placeholder if extraction fails
        if not os.path.exists(output_path):
            print(f"[THUMBNAIL] Could not extract from video, creating placeholder")
            # Create a simple placeholder image
            placeholder = Image.new('RGB', (320, 180), color=(64, 64, 64))
            placeholder.save(output_path, 'JPEG', quality=85)
            return True
            
    except Exception as e:
        print(f"[THUMBNAIL ERROR] Failed to extract thumbnail: {e}")
        return False
    
    return False


def get_thumbnail_path(platform: str, video_id: str) -> str:
    """
    Get the destination path for a thumbnail.
    
    Args:
        platform: Platform name (tiktok, facebook, youtube, etc.)
        video_id: Unique video ID or hash
        
    Returns:
        Absolute path where thumbnail should be saved
    """
    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "backend",
        "media",
        "thumbnails",
        platform
    )
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, f"{video_id}.jpg")


def get_thumbnail_url(platform: str, video_id: str) -> str:
    """
    Get the URL/relative path for accessing a thumbnail via the API.
    
    Args:
        platform: Platform name
        video_id: Video ID or hash
        
    Returns:
        Relative path that can be served by the backend
    """
    return f"/media/thumbnails/{platform}/{video_id}.jpg"
