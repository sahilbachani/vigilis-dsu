from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, post, video

app = FastAPI(title="Vigilis Backend")

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(post.router, prefix="/api/post", tags=["post"])
app.include_router(video.router, prefix="/api/video", tags=["video"])

# Allow CORS (so frontend can call backend)
origins = [
    "http://localhost:5173",  # React dev server
    "http://localhost:3000",  # If using other frontend port
    "http://localhost",        # Generic localhost
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Vigilis backend running"}
