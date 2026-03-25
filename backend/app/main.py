import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, post, video, scraper

app = FastAPI()

# Serve downloaded media
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# Allow CORS for your frontend
origins = [
    "http://localhost:5173",  # React frontend URL
    "http://localhost:3000",  # if you use CRA
    "*",  # optional, allow all origins (use carefully in prod)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

# Include your routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(post.router, prefix="/api/post", tags=["post"])
app.include_router(video.router, prefix="/api/video", tags=["video"])
app.include_router(scraper.router, prefix="/api/scraper", tags=["scraper"])
