from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.db.models import Video

router = APIRouter()

@router.get("/")
def get_videos(db: Session = Depends(get_db)):
    videos = db.query(Video).all()
    return videos
