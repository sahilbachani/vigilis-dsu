#!/usr/bin/env python3
"""
Fix category field for website posts and cleanup old duplicates
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.db.models import Post, Source

def fix_website_categories():
    """Fix posts with wrong categories"""
    db = SessionLocal()
    
    try:
        # Get all website sources
        website_sources = db.query(Source).filter(Source.platform.in_(["website", "Website"])).all()
        
        print(f"Found {len(website_sources)} website sources")
        
        for source in website_sources:
            # Get all posts from this source
            posts = db.query(Post).filter(Post.source_id == source.id).all()
            
            print(f"\n📰 {source.name} ({source.id})")
            print(f"   Total posts: {len(posts)}")
            
            # Update categories based on source
            for post in posts:
                if not post.category or post.category == "unknown":
                    post.category = "news"
                    
            db.commit()
            print(f"   ✅ Updated category for {len(posts)} posts")
        
        print(f"\n✅ All categories fixed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_website_categories()
#!/usr/bin/env python3
"""
Fix category field for website posts and cleanup old duplicates
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.db.models import Post, Source

def fix_website_categories():
    """Fix posts with wrong categories"""
    db = SessionLocal()
    
    try:
        # Get all website sources
        website_sources = db.query(Source).filter(Source.platform.in_(["website", "Website"])).all()
        
        print(f"Found {len(website_sources)} website sources")
        
        for source in website_sources:
            print(f"\n📌 {source.source_name} (ID: {source.source_id})")
            
            # Fix category for posts from this source
            posts_with_wrong_category = db.query(Post).filter(
                Post.source_id == source.source_id,
                Post.category != "website"
            ).all()
            
            if posts_with_wrong_category:
                print(f"   ❌ Found {len(posts_with_wrong_category)} posts with wrong category")
                for post in posts_with_wrong_category:
                    print(f"      Fixing: {post.post_id} ({post.category} → website)")
                    post.category = "website"
                
                db.commit()
                print(f"   ✅ Fixed!")
            else:
                # Check if posts exist
                posts = db.query(Post).filter(Post.source_id == source.source_id).all()
                if posts:
                    print(f"   ✅ {len(posts)} posts with correct category='website'")
                else:
                    print(f"   ℹ️  No posts scraped yet")
        
        print(f"\n{'='*60}")
        print("✅ Category fix complete!")
        print(f"{'='*60}")
        
        # Check /api/post/scraped would return
        website_posts = db.query(Post).filter(Post.category == "website").count()
        print(f"Total 'website' category posts: {website_posts}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = fix_website_categories()
    sys.exit(0 if success else 1)
