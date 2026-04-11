"""
Background tasks for scraping and analysis
Async operations that run without blocking the API
"""
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import threading
from sqlalchemy.orm import Session
from app.db.models import Source, Post
from app.db.session import SessionLocal


class ScrapeTask:
    """Represents an active scraping task"""
    
    # Class-level storage of active tasks
    _active_tasks: Dict[str, 'ScrapeTask'] = {}
    
    def __init__(self, task_id: str, source_id: int, source_name: str):
        self.task_id = task_id
        self.source_id = source_id
        self.source_name = source_name
        self.status = "starting"  # starting, analyzing, scraping, saving, completed, failed
        self.progress = 0  # 0-100%
        self.message = "Initializing..."
        self.posts_found = 0
        self.posts_saved = 0
        self.error = None
        self.start_time = datetime.utcnow()
        self.end_time = None
    
    @classmethod
    def create(cls, source_id: int, source_name: str) -> str:
        """Create a new scrape task, return task_id"""
        import uuid
        task_id = f"scrape_{source_id}_{uuid.uuid4().hex[:8]}"
        task = cls(task_id, source_id, source_name)
        cls._active_tasks[task_id] = task
        print(f"[BACKGROUND] Created task: {task_id}")
        return task_id
    
    @classmethod
    def get(cls, task_id: str) -> Optional['ScrapeTask']:
        """Get task by ID"""
        return cls._active_tasks.get(task_id)
    
    def update(self, status: str, progress: int, message: str):
        """Update task status"""
        self.status = status
        self.progress = progress
        self.message = message
        print(f"[BACKGROUND] Task {self.task_id}: {status} ({progress}%) - {message}")
    
    def complete(self, posts_found: int, posts_saved: int, error: Optional[str] = None):
        """Mark task as complete"""
        self.status = "completed" if not error else "failed"
        self.posts_found = posts_found
        self.posts_saved = posts_saved
        self.error = error
        self.end_time = datetime.utcnow()
        self.progress = 100 if not error else 0
        print(f"[BACKGROUND] Task {self.task_id} completed: {posts_saved} posts saved")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "task_id": self.task_id,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "posts_found": self.posts_found,
            "posts_saved": self.posts_saved,
            "error": self.error,
            "elapsed_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        }


def scrape_in_background(task_id: str, source_id: int):
    """
    Execute scraping in background thread
    Updates task progress throughout
    """
    try:
        task = ScrapeTask.get(task_id)
        if not task:
            print(f"[BACKGROUND] Task {task_id} not found!")
            return
        
        # Get database session
        db = SessionLocal()
        
        try:
            task.update("analyzing", 10, "🚀 Analyzing website structure...")
            
            # Get source
            source = db.query(Source).filter(Source.source_id == source_id).first()
            if not source:
                task.complete(0, 0, "Source not found")
                return
            
            # Auto-detect selectors if needed
            if not source.post_selector or not source.content_selector:
                task.update("analyzing", 20, "Detecting content structure...")
                from app.scrapers.generic_website_scraper import auto_detect_selectors
                
                detected = auto_detect_selectors(source.url)
                if not detected:
                    task.complete(0, 0, "Could not detect website structure")
                    return
                
                # Save detected selectors
                source.post_selector = detected.get('post_selector', '')
                source.content_selector = detected.get('content_selector', '')
                source.title_selector = detected.get('title_selector')
                source.author_selector = detected.get('author_selector')
                source.date_selector = detected.get('date_selector')
                db.commit()
                print(f"[BACKGROUND] Auto-detected selectors for source {source_id}")
            
            task.update("scraping", 30, "🔄 Fetching website content...")
            
            # Scrape
            from app.scrapers.generic_website_scraper import GenericWebsiteScraper, WebsiteScraperConfig
            
            scraper_config = WebsiteScraperConfig(
                url=source.url,
                post_selector=source.post_selector,
                content_selector=source.content_selector,
                title_selector=source.title_selector,
                author_selector=source.author_selector,
                date_selector=source.date_selector,
                link_selector=source.link_selector,
                image_selector=source.image_selector
            )
            
            scraper = GenericWebsiteScraper(scraper_config)
            posts = scraper.scrape()
            
            task.posts_found = len(posts)
            task.update("saving", 60, f"💾 Saving {len(posts)} posts to database...")
            
            # Save posts
            saved_count = 0
            duplicates_count = 0
            
            for i, post_data in enumerate(posts):
                # Progress update every 5 posts
                if i % 5 == 0:
                    progress = 60 + int((i / len(posts) * 30)) if len(posts) > 0 else 60
                    task.update("saving", progress, f"Saving post {i+1}/{len(posts)}...")
                
                # Check if post already exists
                existing = db.query(Post).filter(
                    Post.source_id == source_id,
                    Post.text_content == post_data.get('content', '')[:500]
                ).first()
                
                if existing:
                    duplicates_count += 1
                    continue
                
                post = Post(
                    source_id=source_id,
                    author=post_data.get('author', 'Unknown'),
                    text_content=post_data.get('content', ''),
                    url=post_data.get('url', ''),
                    timestamp=post_data.get('timestamp', datetime.utcnow()),
                    category="website",  # ✅ FIXED: Must be 'website' not source name
                    confidence_score=0.75,
                    flagged=False
                )
                db.add(post)
                saved_count += 1
            
            db.commit()
            
            # Mark as validated
            source.selectors_validated = True
            db.commit()
            
            task.complete(len(posts), saved_count)
            print(f"[BACKGROUND] Scrape completed: {saved_count} new posts, {duplicates_count} duplicates")
            
        except Exception as e:
            print(f"[BACKGROUND] Error in scrape task: {str(e)}")
            import traceback
            traceback.print_exc()
            task.complete(0, 0, str(e))
        finally:
            db.close()
    
    except Exception as e:
        print(f"[BACKGROUND] Fatal error in background task: {str(e)}")


def start_background_scrape(source_id: int, source_name: str) -> str:
    """Start a scraping task in background, return task_id"""
    task_id = ScrapeTask.create(source_id, source_name)
    
    # Start in background thread
    thread = threading.Thread(
        target=scrape_in_background,
        args=(task_id, source_id),
        daemon=True
    )
    thread.start()
    
    return task_id
