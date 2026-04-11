#!/usr/bin/env python
"""
EASY Website Configuration - Auto Add, Configure & Scrape
No coding needed! Just provide website URL.
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api"

def add_website(name: str, url: str) -> int:
    """Add a new website source"""
    print(f"\n{'='*70}")
    print(f"📝 ADDING WEBSITE: {name}")
    print(f"   URL: {url}")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sources",
            json={
                "name": name,
                "url": url,
                "platform": "website",
                "category": "news"
            },
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            website_id = data.get("id")
            print(f"✅ Website added! ID: {website_id}")
            return website_id
        else:
            print(f"❌ Failed to add website: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def configure_website(website_id: int) -> bool:
    """Configure website auto-detect selectors"""
    print(f"\n{'='*70}")
    print(f"🔧 CONFIGURING WEBSITE (ID: {website_id})")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sources/{website_id}/auto-detect",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Configuration successful!")
                print(f"   Posts detected: {data.get('posts_count', 0)}")
                return True
            else:
                print(f"⚠️  Configuration partial: {data.get('message', 'Check selectors')}")
                return False
        else:
            print(f"❌ Configuration failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def start_scraping(website_id: int) -> bool:
    """Start scraping the website"""
    print(f"\n{'='*70}")
    print(f"🔄 STARTING SCRAPE (ID: {website_id})")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sources/{website_id}/scrape",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scraping started!")
            print(f"   Task ID: {data.get('task_id', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to start scraping: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 EASY WEBSITE CONFIGURATION TOOL")
    print("="*70)
    
    # Example: Add BBC News
    if len(sys.argv) > 2:
        name = sys.argv[1]
        url = sys.argv[2]
    else:
        print("💡 EXAMPLE: Add BBC News")
        name = input("Website name: ") or "BBC News"
        url = input("Website URL (https://...): ") or "https://www.bbc.com/news"
    
    # Step 1: Add website
    website_id = add_website(name, url)
    if not website_id:
        sys.exit(1)
    
    time.sleep(2)
    
    # Step 2: Configure selectors
    if not configure_website(website_id):
        print("⚠️  Configuration had issues, but you can continue")
    
    time.sleep(2)
    
    # Step 3: Start scraping
    start_scraping(website_id)
    
    print(f"\n{'='*70}")
    print(f"✅ SETUP COMPLETE!")
    print(f"{'='*70}\n")
#!/usr/bin/env python
"""
EASY Website Configuration - Auto Add, Configure & Scrape
No coding needed! Just provide website URL.
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api"

def add_website(name: str, url: str) -> int:
    """Add a new website source"""
    print(f"\n{'='*70}")
    print(f"📝 ADDING WEBSITE: {name}")
    print(f"   URL: {url}")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sources",
            json={
                "source_name": name,
                "platform": "website",
                "url": url
            },
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            source_id = response.json().get("source_id")
            print(f"✅ ADDED! Source ID: {source_id}")
            return source_id
        else:
            print(f"❌ Failed: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


def auto_detect_selectors(source_id: int) -> bool:
    """Auto-detect CSS selectors (fast: 2-3 seconds)"""
    print(f"\n{'='*70}")
    print(f"🚀 ANALYZING WEBSITE STRUCTURE")
    print(f"   This usually takes 2-3 seconds...")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sources/{source_id}/selectors/auto-detect",
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print(f"\n✅ WEBSITE STRUCTURE ANALYZED!")
                print(f"   {data.get('message', '')}")
                return True
            else:
                print(f"⚠️  {data.get('message', 'Detection incomplete')}")
                return True  # Still return True for fallback pattern
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def validate_selectors(source_id: int) -> bool:
    """Validate selectors work before scraping"""
    print(f"\n{'='*70}")
    print(f"✓ VALIDATING SELECTORS")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sources/{source_id}/selectors/validate",
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("valid"):
                posts_found = data.get("posts_found", 0)
                print(f"✅ VALIDATION PASSED!")
                print(f"   Found {posts_found} posts on the website")
                print(f"   {data.get('message', '')}")
                return True
            else:
                print(f"⚠️  Validation issue: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def start_async_scrape(source_id: int) -> str:
    """Start scraping in background"""
    print(f"\n{'='*70}")
    print(f"⚡ STARTING BACKGROUND SCRAPE")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sources/{source_id}/scrape-async",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get("task_id")
            print(f"✅ SCRAPING STARTED IN BACKGROUND!")
            print(f"   Task ID: {task_id}")
            print(f"   Check progress with: python check_scrape_status.py {task_id}")
            return task_id
        else:
            print(f"❌ Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


def check_task_status(task_id: str):
    """Check background task status"""
    print(f"\n{'='*70}")
    print(f"📊 CHECKING SCRAPE PROGRESS")
    print(f"{'='*70}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/tasks/{task_id}/status",
            timeout=5
        )
        
        if response.status_code == 200:
            task = response.json()
            
            status = task.get("status", "unknown")
            progress = task.get("progress", 0)
            message = task.get("message", "")
            posts_found = task.get("posts_found", 0)
            posts_saved = task.get("posts_saved", 0)
            
            print(f"\n📈 TASK STATUS:")
            print(f"   Status: {status.upper()}")
            print(f"   Progress: {progress}%")
            print(f"   Message: {message}")
            print(f"   Posts Found: {posts_found}")
            print(f"   Posts Saved: {posts_saved}")
            
            if status == "completed":
                print(f"\n✅ SCRAPING COMPLETE!")
                print(f"   {posts_saved} new posts saved successfully")
            
            return task
        else:
            print(f"❌ Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


def main():
    print("\n" + "="*70)
    print("🌐 VIGILIS EASY WEBSITE CONFIGURATION")
    print("="*70)
    print("Add any website, auto-configure, and scrape - NO CODING!")
    
    # Example: Add BBC News
    print("\n" + "="*70)
    print("💡 EXAMPLE: Add BBC News")
    print("="*70)
    
    name = "BBC News"
    url = "https://www.bbc.com/news"
    
    # Step 1: Add website
    source_id = add_website(name, url)
    if not source_id:
        print("Failed to add website")
        return
    
    # Step 2: Auto-detect selectors
    time.sleep(1)
    if not auto_detect_selectors(source_id):
        print("Auto-detection failed")
        return
    
    # Step 3: Validate selectors
    time.sleep(1)
    if not validate_selectors(source_id):
        print("Validation failed")
        return
    
    # Step 4: Start async scraping
    time.sleep(1)
    task_id = start_async_scrape(source_id)
    if not task_id:
        print("Failed to start scraping")
        return
    
    # Step 5: Check status
    print(f"\n{'='*70}")
    print("⏳ SCRAPING IN PROGRESS")
    print("="*70)
    time.sleep(2)
    check_task_status(task_id)
    
    print("\n✅ COMPLETE! You can now:")
    print(f"   1. Check progress: python check_scrape_status.py {task_id}")
    print(f"   2. View scraped posts in the dashboard")
    print(f"   3. Add more websites anytime")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Check task status
        if len(sys.argv) > 2:
            check_task_status(sys.argv[2])
        else:
            print("Usage: python easy_add_website.py check <task_id>")
    else:
        main()
