"""
Sources API - manage data sources for scrapers
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.db.models import Source, Post
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()


class SourceCreate(BaseModel):
    source_name: str
    platform: str  # 'website', 'twitter', 'facebook', 'tiktok'
    url: Optional[str] = None


class SourceUpdate(BaseModel):
    source_name: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None


class SourceResponse(BaseModel):
    source_id: int
    source_name: str
    url: Optional[str]
    platform: str
    added_date: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SourceResponse])
def get_sources(
    db: Session = Depends(get_db)
):
    """Get all sources"""
    return db.query(Source).all()


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    """Get a specific source by ID"""
    source = db.query(Source).filter(Source.source_id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return source


@router.post("/", response_model=SourceResponse)
def create_source(
    source_data: SourceCreate,
    db: Session = Depends(get_db)
):
    """Create a new data source"""
    try:
        # Check if source with same name already exists
        existing = db.query(Source).filter(Source.source_name == source_data.source_name).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Source with name '{source_data.source_name}' already exists"
            )
        
        new_source = Source(
            source_name=source_data.source_name,
            url=source_data.url,
            platform=source_data.platform,
            added_date=datetime.utcnow()
        )
        
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        print(f"[SOURCES] Created source: {new_source.source_name} (ID: {new_source.source_id})")
        return new_source
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SOURCES] Error creating source: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create source: {str(e)}"
        )


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source(
    source_id: int,
    source_data: SourceUpdate,
    db: Session = Depends(get_db)
):
    """Update a source"""
    source = db.query(Source).filter(Source.source_id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Update only provided fields
    if source_data.source_name is not None:
        source.source_name = source_data.source_name
    if source_data.url is not None:
        source.url = source_data.url
    if source_data.platform is not None:
        source.platform = source_data.platform
    
    db.commit()
    db.refresh(source)
    
    return source


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """Delete a source"""
    source = db.query(Source).filter(Source.source_id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    source_name = source.source_name
    db.delete(source)
    db.commit()
    
    return {
        "status": "deleted",
        "source_id": source_id,
        "message": f"Source '{source_name}' deleted successfully"
    }


# ==================== CSS Selectors Configuration ====================

class SelectorConfig(BaseModel):
    """CSS selector configuration for website scraping"""
    post_selector: str  # Container selector for posts
    content_selector: str  # Content selector
    title_selector: Optional[str] = None
    author_selector: Optional[str] = None
    date_selector: Optional[str] = None
    link_selector: Optional[str] = None
    image_selector: Optional[str] = None


class SelectorValidationResponse(BaseModel):
    """Response from selector validation"""
    valid: bool
    message: str
    posts_found: Optional[int] = None
    sample_posts: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@router.post("/{source_id}/selectors/validate", response_model=SelectorValidationResponse)
def validate_selectors(
    source_id: int,
    config: SelectorConfig,
    db: Session = Depends(get_db)
):
    """Validate CSS selectors for a website source before scraping"""
    source = db.query(Source).filter(Source.source_id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    if not source.url:
        raise HTTPException(status_code=400, detail="Source URL is required for selector validation")
    
    try:
        from app.scrapers.generic_website_scraper import GenericWebsiteScraper, WebsiteScraperConfig
        
        scraper_config = WebsiteScraperConfig(
            url=source.url,
            post_selector=config.post_selector,
            content_selector=config.content_selector,
            title_selector=config.title_selector,
            author_selector=config.author_selector,
            date_selector=config.date_selector,
            link_selector=config.link_selector,
            image_selector=config.image_selector
        )
        
        scraper = GenericWebsiteScraper(scraper_config)
        result = scraper.validate_selectors()
        
        return SelectorValidationResponse(
            valid=result.get("valid", False),
            message=result.get("message", ""),
            posts_found=result.get("posts_found"),
            sample_posts=result.get("sample_posts"),
            error=result.get("error")
        )
    except Exception as e:
        return SelectorValidationResponse(
            valid=False,
            message="Validation failed",
            error=str(e)
        )


@router.post("/{source_id}/selectors", response_model=SourceResponse)
def set_selectors(
    source_id: int,
    config: SelectorConfig,
    db: Session = Depends(get_db)
):
    """Save CSS selector configuration for a website source"""
    source = db.query(Source).filter(Source.source_id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Update selectors
    source.post_selector = config.post_selector
    source.content_selector = config.content_selector
    source.title_selector = config.title_selector
    source.author_selector = config.author_selector
    source.date_selector = config.date_selector
    source.link_selector = config.link_selector
    source.image_selector = config.image_selector
    source.selectors_validated = True
    
    db.commit()
    db.refresh(source)
    
    return source


@router.post("/{source_id}/selectors/auto-detect")
def auto_detect_selectors(
    source_id: int,
    db: Session = Depends(get_db)
):
    """Auto-detect CSS selectors for a website (FAST: 2-3 seconds)"""
    source = db.query(Source).filter(Source.source_id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    if not source.url:
        raise HTTPException(status_code=400, detail="Source URL is required for auto-detection")
    
    try:
        print(f"\n🚀 Analyzing website structure...")
        print(f"   This usually takes 1-2 seconds")
        print(f"   URL: {source.url}")
        
        from app.scrapers.generic_website_scraper import auto_detect_selectors
        
        detected = auto_detect_selectors(source.url)
        
        if detected:
            return {
                "success": True,
                "message": "✅ Website structure analyzed! Content patterns detected.",
                "analysis_time": "~1-2 seconds",
                "selectors": detected,
                "post_selector": detected.get("post_selector"),
                "content_selector": detected.get("content_selector"),
                "title_selector": detected.get("title_selector"),
                "author_selector": detected.get("author_selector"),
                "date_selector": detected.get("date_selector"),
                "next_step": "Validate these selectors before scraping"
            }
        else:
            return {
                "success": False,
                "message": "Could not detect selectors. Using fallback pattern.",
                "selectors": {
                    "post_selector": "article, .post, div.entry, [role='article']",
                    "content_selector": "p, .content, main, article",
                    "title_selector": "h1, h2, .title",
                }
            }
    except Exception as e:
        print(f"❌ Auto-detection error: {str(e)}")
        return {
            "success": False,
            "message": f"Auto-detection failed: {str(e)}",
            "selectors": None
        }


@router.post("/{source_id}/scrape")
def scrape_website_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """Scrape a website source using configured selectors"""
    source = db.query(Source).filter(Source.source_id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Log the request
    print(f"\n[API SCRAPE] Starting scrape for source {source_id}: {source.source_name}")
    print(f"[API SCRAPE] URL: {source.url}")
    print(f"[API SCRAPE] Selectors configured: post={bool(source.post_selector)}, content={bool(source.content_selector)}")
    
    # Check if selectors are configured, if not auto-detect them
    if not source.post_selector or not source.content_selector:
        print(f"[API SCRAPE] Selectors not configured, attempting auto-detection...")
        try:
            from app.scrapers.generic_website_scraper import auto_detect_selectors
            
            detected_selectors = auto_detect_selectors(source.url)
            
            if detected_selectors:
                print(f"[API SCRAPE] Auto-detection successful!")
                # Save the detected selectors
                source.post_selector = detected_selectors.get('post_selector', '')
                source.content_selector = detected_selectors.get('content_selector', '')
                source.title_selector = detected_selectors.get('title_selector')
                source.author_selector = detected_selectors.get('author_selector')
                source.date_selector = detected_selectors.get('date_selector')
                source.link_selector = detected_selectors.get('link_selector')
                source.image_selector = detected_selectors.get('image_selector')
                source.selectors_validated = True
                db.commit()
                db.refresh(source)
                print(f"[API SCRAPE] Selectors saved to database")
            else:
                error_msg = "Could not auto-detect CSS selectors. Please configure them manually."
                print(f"[API SCRAPE] ERROR: {error_msg}")
                raise HTTPException(
                    status_code=400,
                    detail=error_msg
                )
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Auto-detection failed: {str(e)}"
            print(f"[API SCRAPE] ERROR: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
    
    try:
        from app.scrapers.generic_website_scraper import GenericWebsiteScraper, WebsiteScraperConfig
        
        print(f"[API SCRAPE] Creating scraper config...")
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
        
        print(f"[API SCRAPE] Starting scraper...")
        scraper = GenericWebsiteScraper(scraper_config)
        posts = scraper.scrape()
        print(f"[API SCRAPE] Scraper returned {len(posts)} posts")
        
        # Save posts to database, track statistics
        saved_count = 0
        duplicates_count = 0
        flagged_count = 0
        
        for post_data in posts:
            try:
                # Check if post already exists by checking content hash
                existing_post = db.query(Post).filter(
                    Post.source_id == source_id,
                    Post.text_content == post_data.get('content', '')[:500]
                ).first()
                
                if existing_post:
                    duplicates_count += 1
                    continue
                
                post = Post(
                    source_id=source_id,
                    author=post_data.get('author', 'Unknown'),
                    text_content=post_data.get('content', ''),
                    url=post_data.get('url', ''),
                    timestamp=post_data.get('timestamp', datetime.utcnow()),
                    category="website",  # ✅ FIXED: Must be 'website' not source name
                    confidence_score=0.75,  # Default starting score
                    flagged=False
                )
                db.add(post)
                saved_count += 1
            except Exception as e:
                print(f"[API SCRAPE] Error saving post: {str(e)}")
                continue
        
        db.commit()
        print(f"[API SCRAPE] Successfully saved {saved_count} posts")
        
        # Count flagged posts (those added in this scrape)
        if saved_count > 0:
            last_posts = db.query(Post).filter(
                Post.source_id == source_id
            ).order_by(Post.post_id.desc()).limit(saved_count).all()
            flagged_count = sum(1 for p in last_posts if p.flagged)
        
        result = {
            "success": True,
            "source_id": source_id,
            "source_name": source.source_name,
            "posts_found": len(posts),
            "posts_saved": saved_count,
            "posts_duplicates": duplicates_count,
            "flagged_count": flagged_count,
            "message": f"Successfully scraped and saved {saved_count} posts from {source.source_name}"
        }
        print(f"[API SCRAPE] Result: {result['message']}")
        return result
        
    except HTTPException as http_err:
        print(f"[API SCRAPE] HTTP Exception: {http_err.detail}")
        raise http_err
    except Exception as e:
        error_msg = str(e)
        print(f"[API SCRAPE] ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": error_msg,
            "message": f"Scraping failed: {error_msg}",
            "posts_found": 0,
            "posts_saved": 0,
            "posts_duplicates": 0,
            "flagged_count": 0
        }


@router.post("/{source_id}/scrape-async")
def scrape_website_async(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Start scraping a website in background (FAST, returns immediately)
    Use GET /{task_id}/task-status to check progress
    """
    source = db.query(Source).filter(Source.source_id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    try:
        from app.core.background_tasks import start_background_scrape
        
        print(f"\n[API] Starting async scrape for source {source_id}: {source.source_name}")
        task_id = start_background_scrape(source_id, source.source_name)
        
        return {
            "success": True,
            "task_id": task_id,
            "source_id": source_id,
            "source_name": source.source_name,
            "message": "Scraping started in background",
            "check_url": f"/api/tasks/{task_id}/status"
        }
    except Exception as e:
        print(f"[API] Error starting async scrape: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to start background scrape"
        }

