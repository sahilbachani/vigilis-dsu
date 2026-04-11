#!/usr/bin/env python
"""
Run website scraper for a specific source from terminal
Usage: python run_website_scraper.py <source_id>
Example: python run_website_scraper.py 10
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.db.models import Source, Post
from app.scrapers.generic_website_scraper import GenericWebsiteScraper, WebsiteScraperConfig
from datetime import datetime

def run_scraper(source_id):
    """Run the website scraper for a specific source"""
    
    db = SessionLocal()
    
    try:
        # Get the source
        source = db.query(Source).filter(Source.source_id == source_id).first()
        
        if not source:
            print(f"❌ Source {source_id} not found")
            return
        
        print(f"\n{'='*70}")
        print(f"🌐 SCRAPING: {source.source_name}")
        print(f"   URL: {source.url}")
        print(f"   Source ID: {source.source_id}")
        print(f"{'='*70}")
        
        # Initialize scraper with CSS selectors from database
        config = WebsiteScraperConfig(
            url=source.url,
            post_selector=source.post_selector,
            content_selector=source.content_selector,
            title_selector=source.title_selector,
            author_selector=source.author_selector,
            date_selector=source.date_selector,
            link_selector=source.link_selector,
        )
        
        scraper = GenericWebsiteScraper(config)
        
        # Scrape posts
        posts = scraper.scrape()
        
        print(f"\n✅ Scraped {len(posts)} posts")
        
        # Save to database
        saved_count = 0
        for post_data in posts:
            try:
                # Check if post already exists
                existing = db.query(Post).filter(
                    Post.source_id == source_id,
                    Post.url == post_data.get("url")
                ).first()
                
                if not existing:
                    post = Post(
                        source_id=source_id,
                        author=post_data.get("author", "Unknown"),
                        text_content=post_data.get("content", ""),
                        url=post_data.get("url", ""),
                        timestamp=post_data.get("date", datetime.now()),
                        category="news"
                    )
                    db.add(post)
                    saved_count += 1
            except Exception as e:
                print(f"   ⚠️  Error saving post: {str(e)}")
        
        db.commit()
        print(f"✅ Saved {saved_count} new posts to database")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_website_scraper.py <source_id>")
        print("Example: python run_website_scraper.py 10")
        sys.exit(1)
    
    try:
        source_id = int(sys.argv[1])
        run_scraper(source_id)
    except ValueError:
        print("❌ Invalid source ID (must be a number)")
        sys.exit(1)
