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
    "postgresql://postgres:CHERRY718hf@localhost:5432/vigilis_db"
)

# Debug: Print connection info (redacted password)
import re
debug_url = re.sub(r'://[^:]+:([^@]+)@', r'://USER:***@', DATABASE_URL)
print(f"[DB] Connecting to: {debug_url}")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connection before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get a database session with connection testing"""
    try:
        from sqlalchemy import text
        session = SessionLocal()
        # Test the connection
        session.execute(text("SELECT 1"))
        return session
    except Exception as e:
        print(f"\n[DB ERROR] Failed to connect to database!")
        print(f"  - Check PostgreSQL is running on localhost:5432")
        print(f"  - Check username/password in scrapers/scrapper/.env")
        print(f"  - Error: {str(e)[:200]}")
        raise


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
    category: str = "twitter"
) -> int:
    """
    Save a post to the database
    Returns the post_id
    """
    from sqlalchemy import text
    
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
    
    return result[0] if result else None


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
