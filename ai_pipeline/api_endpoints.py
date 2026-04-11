"""
AI Analysis API Endpoints
Provides REST endpoints for accessing AI analysis results and statistics.
Can be included in the FastAPI backend.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.db.deps import get_db
from app.db.models import Post

# Import AI pipeline
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ai_pipeline.integration import AIAnalysisPipeline

router = APIRouter()

# Initialize pipeline (will create singleton)
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = AIAnalysisPipeline()
    return _pipeline


# ============================================================================
# Pydantic Models for Response
# ============================================================================

class AnalysisScoresResponse(BaseModel):
    """Response model for analysis scores"""
    hate_score: float
    extremism_score: float
    misinformation_score: float
    emotion_anger: float
    emotion_fear: float
    emotion_disgust: float
    emotion_neutral: float
    confidence_score: float
    
    class Config:
        from_attributes = True


class FlaggedPostResponse(BaseModel):
    """Response model for flagged posts"""
    post_id: int
    author: str
    text_content: str
    timestamp: datetime
    category: str
    analysis_scores: AnalysisScoresResponse
    confidence_score: float
    analysis_timestamp: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AnalysisStatsResponse(BaseModel):
    """Response model for analysis statistics"""
    total_posts: int
    flagged_posts: int
    processed_posts: int
    flagging_rate: float  # percentage
    avg_hate_score: float
    avg_extremism_score: float
    avg_misinformation_score: float
    avg_confidence_score: float


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/analysis/flagged", response_model=List[FlaggedPostResponse])
def get_flagged_posts(
    db: Session = Depends(get_db),
    limit: int = Query(50, le=200),
    category: Optional[str] = Query(None),
    min_confidence: float = Query(0.3, ge=0.0, le=1.0),
):
    """
    Get flagged posts with AI analysis scores.
    
    Query Parameters:
    - limit: Number of posts to return (max 200)
    - category: Filter by category (e.g., 'twitter')
    - min_confidence: Minimum confidence score threshold
    
    Returns list of flagged posts with their analysis scores.
    """
    pipeline = get_pipeline()
    posts = pipeline.get_flagged_posts(
        db=db,
        limit=limit,
        category=category,
        min_confidence=min_confidence
    )
    
    # Convert to response models
    response_posts = []
    for post in posts:
        response_posts.append({
            "post_id": post["post_id"],
            "author": post["author"],
            "text_content": post["text_content"],
            "timestamp": post["timestamp"],
            "category": post["category"],
            "confidence_score": post["confidence_score"],
            "analysis_timestamp": post.get("analysis_timestamp"),
            "analysis_scores": {
                "hate_score": post["hate_score"],
                "extremism_score": post["extremism_score"],
                "misinformation_score": post["misinformation_score"],
                "emotion_anger": post["emotion_anger"],
                "emotion_fear": post["emotion_fear"],
                "emotion_disgust": post["emotion_disgust"],
                "emotion_neutral": post["emotion_neutral"],
                "confidence_score": post["confidence_score"],
            }
        })
    
    return response_posts


@router.get("/analysis/stats", response_model=AnalysisStatsResponse)
def get_analysis_statistics(db: Session = Depends(get_db)):
    """
    Get overall analysis statistics.
    
    Returns:
    - total_posts: Total posts in database
    - flagged_posts: Number of flagged posts
    - processed_posts: Posts analyzed with AI
    - flagging_rate: Percentage of posts flagged
    - avg_*_score: Average scores for each metric
    """
    pipeline = get_pipeline()
    stats = pipeline.get_analysis_stats(db)
    
    # Calculate flagging rate
    flagging_rate = 0.0
    if stats["total_posts"] > 0:
        flagging_rate = (stats["flagged_posts"] / stats["total_posts"]) * 100
    
    return {
        "total_posts": stats["total_posts"],
        "flagged_posts": stats["flagged_posts"],
        "processed_posts": stats["processed_posts"],
        "flagging_rate": flagging_rate,
        "avg_hate_score": stats["avg_hate_score"],
        "avg_extremism_score": stats["avg_extremism_score"],
        "avg_misinformation_score": stats["avg_misinformation_score"],
        "avg_confidence_score": stats["avg_confidence_score"],
    }


@router.get("/analysis/post/{post_id}", response_model=FlaggedPostResponse)
def get_post_analysis(post_id: int, db: Session = Depends(get_db)):
    """
    Get analysis details for a specific post.
    """
    post = db.query(Post).filter(Post.post_id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {
        "post_id": post.post_id,
        "author": post.author,
        "text_content": post.text_content,
        "timestamp": post.timestamp,
        "category": post.category,
        "confidence_score": post.confidence_score,
        "analysis_timestamp": post.analysis_timestamp,
        "analysis_scores": {
            "hate_score": post.hate_score or 0.0,
            "extremism_score": post.extremism_score or 0.0,
            "misinformation_score": post.misinformation_score or 0.0,
            "emotion_anger": post.emotion_anger or 0.0,
            "emotion_fear": post.emotion_fear or 0.0,
            "emotion_disgust": post.emotion_disgust or 0.0,
            "emotion_neutral": post.emotion_neutral or 1.0,
            "confidence_score": post.confidence_score or 0.0,
        }
    }


@router.get("/analysis/by-metric")
def get_posts_by_metric(
    db: Session = Depends(get_db),
    metric: str = Query("hate_score"),
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(50, le=200),
):
    """
    Get flagged posts filtered by a specific metric and threshold.
    
    Metrics:
    - hate_score
    - extremism_score
    - misinformation_score
    - emotion_anger
    - emotion_fear
    - emotion_disgust
    
    Example: GET /analysis/by-metric?metric=extremism_score&threshold=0.7&limit=20
    """
    from sqlalchemy import text
    
    valid_metrics = {
        "hate_score",
        "extremism_score",
        "misinformation_score",
        "emotion_anger",
        "emotion_fear",
        "emotion_disgust",
    }
    
    if metric not in valid_metrics:
        raise ValueError(f"Invalid metric. Choose from: {', '.join(valid_metrics)}")
    
    query = text(f"""
        SELECT post_id, author, text_content, timestamp, category, 
               {metric}, confidence_score, analysis_timestamp
        FROM posts
        WHERE flagged = true AND {metric} >= :threshold
        ORDER BY {metric} DESC
        LIMIT :limit
    """)
    
    results = db.execute(query, {"threshold": threshold, "limit": limit}).fetchall()
    
    posts = []
    for row in results:
        posts.append({
            "post_id": row[0],
            "author": row[1],
            "text_content": row[2],
            "timestamp": row[3],
            "category": row[4],
            "metric_value": row[5],
            "confidence_score": row[6],
            "analysis_timestamp": row[7],
        })
    
    return {
        "metric": metric,
        "threshold": threshold,
        "posts_found": len(posts),
        "posts": posts,
    }


@router.get("/analysis/category-stats")
def get_category_statistics(db: Session = Depends(get_db)):
    """
    Get analysis statistics grouped by category.
    """
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            category,
            COUNT(*) as total,
            SUM(CASE WHEN flagged = true THEN 1 ELSE 0 END) as flagged,
            AVG(hate_score) as avg_hate,
            AVG(extremism_score) as avg_extremism,
            AVG(misinformation_score) as avg_misinformation,
            AVG(confidence_score) as avg_confidence
        FROM posts
        GROUP BY category
        ORDER BY total DESC
    """)
    
    results = db.execute(query).fetchall()
    
    stats = []
    for row in results:
        stats.append({
            "category": row[0],
            "total_posts": row[1],
            "flagged_posts": row[2],
            "flagging_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0,
            "avg_hate_score": float(row[3] or 0),
            "avg_extremism_score": float(row[4] or 0),
            "avg_misinformation_score": float(row[5] or 0),
            "avg_confidence_score": float(row[6] or 0),
        })
    
    return {"category_stats": stats}


# ============================================================================
# Include in FastAPI app
# ============================================================================

# In backend/app/main.py, add:
# from app.api import analysis
# app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
