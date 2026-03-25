from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.deps import get_db
from app.db.models import Post, PostMedia
from typing import Optional

router = APIRouter()

@router.delete("/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}

@router.get("/")
def get_posts(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    flagged: Optional[bool] = Query(None),
    limit: int = Query(50, le=100)
):
    """
    Get posts with optional filtering
    - category: Filter by category (e.g., 'twitter')
    - platform: Filter by platform (e.g., 'Twitter/X')
    - flagged: Filter by flagged status
    - limit: Number of results (max 100)
    """
    query = db.query(Post).order_by(Post.timestamp.desc())
    
    if category:
        query = query.filter(Post.category == category)
    if platform:
        query = query.filter_by(platform=platform)
    if flagged is not None:
        query = query.filter(Post.flagged == flagged)
    
    return query.limit(limit).all()

@router.get("/scraped")
def get_scraped_posts(
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100)
):
    """
    Get scraped posts (posts with category='twitter' or 'facebook' or 'website')
    """
    # Use joinedload to fetch associated media items automatically
    return (
        db.query(Post)
        .options(joinedload(Post.media))
        .filter(Post.category.in_(["twitter", "facebook", "website", "tiktok"]))
        .order_by(Post.timestamp.desc())
        .limit(limit)
        .all()
    )

@router.get("/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific post by ID"""
    return db.query(Post).filter(Post.id == post_id).first()
