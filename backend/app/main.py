from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, post, video, dashboard, scraper, sources, alerts, tasks

app = FastAPI()

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
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
