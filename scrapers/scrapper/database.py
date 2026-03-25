"""
Database connection and operations for scraper using SQLAlchemy
Mirrors the backend database structure
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration (matches backend)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:5757@localhost:5432/vigilis_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get a database session"""
    return SessionLocal()


def get_or_create_source(db: Session, platform: str, source_name: str, url: str):
    """Get or create a source entry"""
    from sqlalchemy import text
    
    # Query for existing source
    result = db.execute(
        text("""
            SELECT source_id FROM sources 
            WHERE platform = :platform AND source_name = :source_name
        """),
        {"platform": platform, "source_name": source_name}
    ).fetchone()
    
    if result:
        return result[0]
    
    # Create new source
    db.execute(
        text("""
            INSERT INTO sources (platform, source_name, url, added_date) 
            VALUES (:platform, :source_name, :url, :added_date)
        """),
        {
            "platform": platform,
            "source_name": source_name,
            "url": url,
            "added_date": datetime.utcnow()
        }
    )
    db.commit()
    
    # Get the newly created source_id
    result = db.execute(
        text("""
            SELECT source_id FROM sources 
            WHERE platform = :platform AND source_name = :source_name
        """),
        {"platform": platform, "source_name": source_name}
    ).fetchone()
    
    return result[0]


def save_post_to_db(
    db: Session,
    source_id: int,
    author: str,
    text_content: str,
    timestamp: str,
    url: str = None,
    confidence_score: float = None,
    category: str = "twitter",
    media_items: list = None
) -> int:
    """
    Save a post to the database along with any media items.
    media_items should be a list of dicts:
    [{"type": "image", "url": "https...", "local_path": "/media/..."}]
    Returns the post_id
    """
    from sqlalchemy import text
    
    # Deduplication Check
    # Facebook timestamp is generated on the fly so we can't reliably dedupe using time.
    # URLs might also be empty or slightly changing due to parameters.
    # We will deduplicate based on: Exact URL OR (Author AND Text_Content)
    try:
        query = text("""
            SELECT post_id FROM posts 
            WHERE source_id = :source_id
            AND (
                (url IS NOT NULL AND url = :url)
                OR (author = :author AND text_content = :text_content)
            )
            LIMIT 1
        """)
        existing = db.execute(query, {
            "source_id": source_id,
            "url": url,
            "author": author,
            "text_content": text_content
        }).fetchone()
        
        if existing:
            # Return quietly without inserting/modifying anything
            return existing[0]
            
    except Exception as e:
        print(f"Deduplication query failed: {e}")
        db.rollback()

    db.execute(
        text("""
            INSERT INTO posts (source_id, author, text_content, timestamp, url, confidence_score, category, flagged)
            VALUES (:source_id, :author, :text_content, :timestamp, :url, :confidence_score, :category, false)
        """),
        {
            "source_id": source_id,
            "author": author,
            "text_content": text_content,
            "timestamp": timestamp,
            "url": url,
            "confidence_score": confidence_score,
            "category": category
        }
    )
    db.commit()
    
    # Get the newly created post_id
    result = db.execute(
        text("""
            SELECT post_id FROM posts 
            WHERE source_id = :source_id AND author = :author AND timestamp = :timestamp
            ORDER BY post_id DESC LIMIT 1
        """),
        {
            "source_id": source_id,
            "author": author,
            "timestamp": timestamp
        }
    ).fetchone()
    
    post_id = result[0] if result else None
    
    # Insert media items if any
    if post_id and media_items:
        for media in media_items:
            db.execute(
                text("""
                    INSERT INTO post_media (post_id, media_type, media_url, local_path, added_date)
                    VALUES (:post_id, :media_type, :media_url, :local_path, :added_date)
                """),
                {
                    "post_id": post_id,
                    "media_type": media.get("type", "image"),
                    "media_url": media.get("url"),
                    "local_path": media.get("local_path"),
                    "added_date": datetime.utcnow()
                }
            )
        db.commit()
    
    return post_id


def add_tags_to_post(db: Session, post_id: int, source_id: int, tags: list):
    """
    Add tags/keywords to a post
    """
    from sqlalchemy import text
    
    for tag in tags:
        if tag:  # Only save non-empty tags
            db.execute(
                text("""
                    INSERT INTO tags_keywords (post_id, source_id, tag, added_date)
                    VALUES (:post_id, :source_id, :tag, :added_date)
                """),
                {
                    "post_id": post_id,
                    "source_id": source_id,
                    "tag": tag.lower(),
                    "added_date": datetime.utcnow()
                }
            )
    
    db.commit()
