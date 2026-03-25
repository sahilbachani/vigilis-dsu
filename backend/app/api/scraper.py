"""
Scraper trigger API - runs scraper scripts from the frontend
"""
import subprocess
import sys
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Path to the scrapers directory
SCRAPERS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "scrapers", "scrapper")
)

# Map platform names to their scraper scripts
SCRAPER_SCRIPTS = {
    "twitter": "x_scrapper.py",
    "facebook": "fb_scrapper.py",
    "website": "web_scrapper.py",
    "tiktok": "tiktok_scrapper.py",
}


class ScrapeRequest(BaseModel):
    platform: str


class ScrapeResponse(BaseModel):
    status: str
    platform: str
    message: str


@router.post("/run", response_model=ScrapeResponse)
def run_scraper(request: ScrapeRequest):
    """
    Trigger a scraper by platform name.
    Spawns the script as a background subprocess and returns immediately.
    """
    platform = request.platform.lower()

    is_website_source = platform.startswith("website-")
    base_platform = "website" if is_website_source else platform

    if base_platform not in SCRAPER_SCRIPTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown platform '{platform}'."
        )

    script_name = SCRAPER_SCRIPTS[base_platform]
    script_path = os.path.join(SCRAPERS_DIR, script_name)

    if not os.path.exists(script_path):
        raise HTTPException(
            status_code=404,
            detail=f"Scraper script not found: {script_name}"
        )

    # Find Python executable - prefer the scraper's venv if it exists
    scraper_venv_python = os.path.join(SCRAPERS_DIR, "venv", "Scripts", "python.exe")
    if not os.path.exists(scraper_venv_python):
        # Try Linux/Mac path
        scraper_venv_python = os.path.join(SCRAPERS_DIR, "venv", "bin", "python")
    
    python_exe = scraper_venv_python if os.path.exists(scraper_venv_python) else sys.executable

    cmd = [python_exe, script_path]
    if is_website_source:
        source_id = platform.split("website-")[1]
        cmd.extend(["--source", source_id])

    try:
        # Spawn scraper as a detached background process
        subprocess.Popen(
            cmd,
            cwd=SCRAPERS_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            # On Windows, CREATE_NEW_PROCESS_GROUP detaches the child
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )

        return ScrapeResponse(
            status="started",
            platform=platform,
            message=f"Scraper for '{platform}' has been started in the background."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start scraper: {str(e)}"
        )


@router.get("/platforms")
def get_available_platforms():
    """Return list of available scraper platforms."""
    platforms = []
    for key, script in SCRAPER_SCRIPTS.items():
        if key == "website":
            continue # specific sources are handled below
        script_path = os.path.join(SCRAPERS_DIR, script)
        platforms.append({
            "id": key,
            "name": key.capitalize(),
            "script": script,
            "available": os.path.exists(script_path),
        })
        
    # Add specific website sources
    website_script = os.path.join(SCRAPERS_DIR, SCRAPER_SCRIPTS["website"])
    is_website_available = os.path.exists(website_script)
    
    website_sources = [
        {"id": "website-dawn", "name": "Dawn News"},
        {"id": "website-toi", "name": "Times of India"},
        {"id": "website-jihadintel", "name": "Jihad Intel"},
        {"id": "website-khorasandiary", "name": "The Khorasan Diary"}
    ]
    
    for source in website_sources:
        platforms.append({
            "id": source["id"],
            "name": source["name"],
            "script": SCRAPER_SCRIPTS["website"],
            "available": is_website_available,
        })
        
    return platforms
