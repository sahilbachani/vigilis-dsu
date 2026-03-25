import os
import uuid
import requests
import hashlib
from urllib.parse import urlparse

# Path relative to the scrapper directory
BASE_MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend", "media")

def download_media(url: str, platform: str, media_type: str = "image") -> str:
    """
    Downloads media from the given URL and saves it to the backend/media folder.
    Returns the relative path for the database.
    """
    if not url:
        return None

    try:
        # e.g., backend/media/images/twitter
        directory = os.path.join(BASE_MEDIA_DIR, f"{media_type}s", platform)
        os.makedirs(directory, exist_ok=True)

        # Deterministic filename using MD5 hash of URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        parsed_url = urlparse(url)
        original_filename = os.path.basename(parsed_url.path)
        
        # Give fallback names if the url doesn't have a clear extension
        if not original_filename or "." not in original_filename:
            ext = ".jpg" if media_type == "image" else ".mp4"
        else:
            _, ext = os.path.splitext(original_filename)

        filename = f"{url_hash}{ext}"
        local_abs_path = os.path.join(directory, filename)
        
        # If file already exists, do not re-download
        if os.path.exists(local_abs_path):
            return f"/media/{media_type}s/{platform}/{filename}"
        
        # Download the file
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        
        # 10s timeout, stream true to prevent loading massive files in memory
        response = requests.get(url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()

        with open(local_abs_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Return relative path like `/media/images/twitter/uuid_file.jpg`
        # for FastAPI to serve directly
        return f"/media/{media_type}s/{platform}/{filename}"

    except Exception as e:
        print(f"Failed to download media [{url}]: {e}")
        return None
