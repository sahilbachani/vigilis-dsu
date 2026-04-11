from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.db.models import Post, Source
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics:
    - Total sources
    - Total posts
    - Total flagged content
    - Posts by category
    """
    from sqlalchemy import func
    
    # Count total sources
    total_sources = db.query(Source).count()
    
    # Count total posts
    total_posts = db.query(Post).count()
    
    # Count total flagged posts
    total_flagged = db.query(Post).filter(Post.flagged == True).count()
    
    # Count posts by category
    posts_by_category = db.query(
        Post.category,
        func.count(Post.post_id).label('count')
    ).group_by(Post.category).all()
    
    category_breakdown = {cat: count for cat, count in posts_by_category}
    
    return {
        "totalSources": total_sources,
        "totalPosts": total_posts,
        "totalFlagged": total_flagged,
        "postsFlagged": total_flagged,  # Keep for backward compatibility
        "postsByCategory": category_breakdown,
    }

@router.get("/status")
def get_system_status(db: Session = Depends(get_db)):
    """
    Get system status:
    - System status (online/offline)
    - Last updated timestamp
    """
    # Check if database is accessible
    try:
        db.query(Post).first()
        status = "online"
    except Exception:
        status = "offline"
    
    return {
        "status": status,
        "lastUpdated": datetime.utcnow().isoformat(),
    }

@router.get("/trend")
def get_flagged_trend(db: Session = Depends(get_db), days: int = 7):
    """
    Get flagged content trend for the last N days
    """
    trend_data = []
    
    for i in range(days, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
        
        count = db.query(Post).filter(
            Post.flagged == True,
            Post.timestamp >= date_start,
            Post.timestamp < date_end
        ).count()
        
        trend_data.append({
            "date": date_start.isoformat(),
            "flagged": count
        })
    
    return trend_data
