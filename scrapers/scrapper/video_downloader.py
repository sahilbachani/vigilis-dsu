import os
import uuid
import subprocess
import hashlib
import sys

# Path relative to the scrapper directory
BASE_MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend", "media")

def download_video(post_url: str, platform: str, cookies_file: str = None) -> str:
    """
    Downloads the best quality video from a post URL using yt-dlp.
    Returns the relative path for the database.
    """
    if not post_url:
        return None

    try:
        # e.g., backend/media/videos/twitter
        directory = os.path.join(BASE_MEDIA_DIR, "videos", platform)
        os.makedirs(directory, exist_ok=True)

        url_hash = hashlib.md5(post_url.encode()).hexdigest()
        filename = f"{url_hash}.mp4"
        local_abs_path = os.path.join(directory, filename)

        # Skip if already downloaded
        if os.path.exists(local_abs_path):
            print(f"Video already locally cached: {local_abs_path}")
            return f"/media/videos/{platform}/{filename}"

        print(f"[{platform}] Attempting to extract video using yt-dlp from: {post_url}")
        
        # Build yt-dlp command
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", local_abs_path,
            "--no-warnings",
            "--quiet",
        ]

        if cookies_file and os.path.exists(cookies_file):
            cmd.extend(["--cookies", cookies_file])
            
        cmd.append(post_url)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(local_abs_path):
            print(f"Successfully downloaded video: {filename}")
            return f"/media/videos/{platform}/{filename}"
        else:
            print(f"yt-dlp failed (Return code {result.returncode}) for {post_url}\n{result.stderr}")
            return None

    except Exception as e:
        print(f"Exception during video extraction: {e}")
        return None
