"""
Database Operations Module
Handles saving analyzed posts to PostgreSQL.
Only stores flagged posts as per requirements.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyzedPostDB:
    """
    Database operations for storing analyzed posts.
    Only persists flagged posts.
    """
    
    @staticmethod
    def save_analyzed_post(
        db: Session,
        source_id: int,
        author: str,
        text_content: str,
        timestamp: datetime,
        analysis_result: 'AnalysisResult',  # From analyzer module
        url: Optional[str] = None,
        category: str = "twitter"
    ) -> Optional[int]:
        """
        Save analyzed post to database.
        Only saves if flagged=True.
        
        Args:
            db: Database session
            source_id: Source ID from sources table
            author: Post author
            text_content: Original post text
            timestamp: Post timestamp
            analysis_result: AnalysisResult object from TextAnalyzer
            url: Optional post URL
            category: Post category (default: 'twitter')
            
        Returns:
            post_id if saved, None if not flagged or error
        """
        try:
            # Only save flagged posts
            if not analysis_result.flagged:
                logger.debug(f"Post not flagged, skipping: {author}")
                return None
            
            # Prepare the INSERT statement
            query = text("""
                INSERT INTO posts (
                    source_id, author, timestamp, text_content, url, 
                    confidence_score, flagged, category,
                    hate_score, extremism_score, misinformation_score,
                    emotion_anger, emotion_fear, emotion_disgust, emotion_neutral,
                    ai_processed, analysis_timestamp
                ) VALUES (
                    :source_id, :author, :timestamp, :text_content, :url,
                    :confidence_score, :flagged, :category,
                    :hate_score, :extremism_score, :misinformation_score,
                    :emotion_anger, :emotion_fear, :emotion_disgust, :emotion_neutral,
                    :ai_processed, :analysis_timestamp
                ) RETURNING post_id
            """)
            
            # Convert numpy types to native Python types
            def to_python_type(value):
                """Convert numpy types to native Python types"""
                if value is None:
                    return None
                # Check if it's a numpy type
                try:
                    import numpy as np
                    if isinstance(value, (np.floating, np.integer)):
                        return float(value) if isinstance(value, np.floating) else int(value)
                except ImportError:
                    pass
                return value
            
            # Execute the query
            result = db.execute(
                query,
                {
                    "source_id": source_id,
                    "author": author,
                    "timestamp": timestamp,
                    "text_content": text_content,
                    "url": url,
                    "confidence_score": to_python_type(analysis_result.confidence_score),
                    "flagged": analysis_result.flagged,
                    "category": category,
                    "hate_score": to_python_type(analysis_result.hate_score),
                    "extremism_score": to_python_type(analysis_result.extremism_score),
                    "misinformation_score": to_python_type(analysis_result.misinformation_score),
                    "emotion_anger": to_python_type(analysis_result.emotion_anger),
                    "emotion_fear": to_python_type(analysis_result.emotion_fear),
                    "emotion_disgust": to_python_type(analysis_result.emotion_disgust),
                    "emotion_neutral": to_python_type(analysis_result.emotion_neutral),
                    "ai_processed": True,
                    "analysis_timestamp": analysis_result.analysis_timestamp,
                }
            )
            
            db.commit()
            
            # Get the post ID
            post_id = result.scalar()
            
            logger.info(
                f"✓ Saved flagged post #{post_id} from {author} "
                f"(flags: {', '.join(analysis_result.flags_triggered)})"
            )
            
            return post_id
            
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Error saving post from {author}: {str(e)}")
            return None
    
    @staticmethod
    def update_post_analysis(
        db: Session,
        post_id: int,
        analysis_result: 'AnalysisResult'
    ) -> bool:
        """
        Update analysis scores for an existing post.
        Used if post is saved before analysis completes.
        
        Args:
            db: Database session
            post_id: ID of post to update
            analysis_result: AnalysisResult with new scores
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = text("""
                UPDATE posts SET
                    hate_score = :hate_score,
                    extremism_score = :extremism_score,
                    misinformation_score = :misinformation_score,
                    emotion_anger = :emotion_anger,
                    emotion_fear = :emotion_fear,
                    emotion_disgust = :emotion_disgust,
                    emotion_neutral = :emotion_neutral,
                    confidence_score = :confidence_score,
                    flagged = :flagged,
                    ai_processed = true,
                    analysis_timestamp = :analysis_timestamp
                WHERE post_id = :post_id
            """)
            
            db.execute(
                query,
                {
                    "post_id": post_id,
                    "hate_score": analysis_result.hate_score,
                    "extremism_score": analysis_result.extremism_score,
                    "misinformation_score": analysis_result.misinformation_score,
                    "emotion_anger": analysis_result.emotion_anger,
                    "emotion_fear": analysis_result.emotion_fear,
                    "emotion_disgust": analysis_result.emotion_disgust,
                    "emotion_neutral": analysis_result.emotion_neutral,
                    "confidence_score": analysis_result.confidence_score,
                    "flagged": analysis_result.flagged,
                    "analysis_timestamp": analysis_result.analysis_timestamp,
                }
            )
            
            db.commit()
            logger.info(f"✓ Updated analysis for post #{post_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Error updating post #{post_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_unanalyzed_posts(db: Session, limit: int = 100) -> List[Dict]:
        """
        Get posts that haven't been analyzed yet.
        Useful for batch processing of backlog.
        
        Args:
            db: Database session
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of unanalyzed posts
        """
        try:
            query = text("""
                SELECT post_id, source_id, author, timestamp, text_content, url, category
                FROM posts
                WHERE ai_processed = false
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            
            results = db.execute(query, {"limit": limit}).fetchall()
            
            posts = []
            for row in results:
                posts.append({
                    "post_id": row[0],
                    "source_id": row[1],
                    "author": row[2],
                    "timestamp": row[3],
                    "text_content": row[4],
                    "url": row[5],
                    "category": row[6],
                })
            
            return posts
            
        except Exception as e:
            logger.error(f"✗ Error retrieving unanalyzed posts: {str(e)}")
            return []
    
    @staticmethod
    def get_flagged_posts(
        db: Session,
        limit: int = 50,
        category: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[Dict]:
        """
        Get flagged posts for dashboard display.
        
        Args:
            db: Database session
            limit: Maximum number of posts
            category: Optional category filter
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of flagged posts
        """
        try:
            base_query = """
                SELECT 
                    post_id, source_id, author, timestamp, text_content,
                    hate_score, extremism_score, misinformation_score,
                    emotion_anger, emotion_fear, emotion_disgust,
                    confidence_score, category, url
                FROM posts
                WHERE flagged = true AND confidence_score >= :min_confidence
            """
            
            params = {"min_confidence": min_confidence}
            
            if category:
                base_query += " AND category = :category"
                params["category"] = category
            
            base_query += " ORDER BY analysis_timestamp DESC LIMIT :limit"
            params["limit"] = limit
            
            results = db.execute(text(base_query), params).fetchall()
            
            posts = []
            for row in results:
                posts.append({
                    "post_id": row[0],
                    "source_id": row[1],
                    "author": row[2],
                    "timestamp": row[3],
                    "text_content": row[4],
                    "hate_score": row[5],
                    "extremism_score": row[6],
                    "misinformation_score": row[7],
                    "emotion_anger": row[8],
                    "emotion_fear": row[9],
                    "emotion_disgust": row[10],
                    "confidence_score": row[11],
                    "category": row[12],
                    "url": row[13],
                })
            
            return posts
            
        except Exception as e:
            logger.error(f"✗ Error retrieving flagged posts: {str(e)}")
            return []
    
    @staticmethod
    def get_analysis_stats(db: Session) -> Dict:
        """
        Get analysis statistics for dashboard.
        
        Returns:
            Dictionary with stats
        """
        try:
            stats_query = text("""
                SELECT
                    COUNT(*) as total_posts,
                    SUM(CASE WHEN flagged = true THEN 1 ELSE 0 END) as flagged_posts,
                    SUM(CASE WHEN ai_processed = true THEN 1 ELSE 0 END) as processed_posts,
                    AVG(hate_score) as avg_hate_score,
                    AVG(extremism_score) as avg_extremism_score,
                    AVG(misinformation_score) as avg_misinformation_score,
                    AVG(confidence_score) as avg_confidence
                FROM posts
            """)
            
            result = db.execute(stats_query).fetchone()
            
            return {
                "total_posts": result[0] or 0,
                "flagged_posts": result[1] or 0,
                "processed_posts": result[2] or 0,
                "avg_hate_score": float(result[3] or 0),
                "avg_extremism_score": float(result[4] or 0),
                "avg_misinformation_score": float(result[5] or 0),
                "avg_confidence_score": float(result[6] or 0),
            }
            
        except Exception as e:
            logger.error(f"✗ Error retrieving stats: {str(e)}")
            return {}
