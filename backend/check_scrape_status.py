#!/usr/bin/env python
"""
Check Status of a Background Scraping Task
Usage: python check_scrape_status.py <task_id>
"""
import requests
import sys
import time
import json

BASE_URL = "http://localhost:8000/api"

def check_status(task_id: str, watch: bool = False):
    """Check task status"""
    try:
        response = requests.get(
            f"{BASE_URL}/tasks/{task_id}/status",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_scrape_status.py <task_id> [--watch]")
        sys.exit(1)
    
    task_id = sys.argv[1]
    watch = "--watch" in sys.argv
    
    if watch:
        print(f"Watching task {task_id}... (Press Ctrl+C to stop)")
        while True:
            status = check_status(task_id)
            if status and status.get("status") in ["completed", "failed"]:
                break
            time.sleep(2)
    else:
        check_status(task_id)
#!/usr/bin/env python
"""
Check Status of a Background Scraping Task
Usage: python check_scrape_status.py <task_id>
"""
import requests
import sys
import time
import json

BASE_URL = "http://localhost:8000/api"

def check_status(task_id: str, watch: bool = False):
    """Check task status"""
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
            elapsed = task.get("elapsed_seconds", 0)
            
            # Clear screen
            print("\033[H\033[J" if watch else "", end="")
            
            print(f"\n{'='*70}")
            print(f"📊 SCRAPE TASK STATUS")
            print(f"{'='*70}")
            print(f"Task ID: {task_id}")
            print(f"Status: {status.upper()}")
            print(f"Progress: {progress}%")
            print(f"Message: {message}")
            print(f"Posts Found: {posts_found}")
            print(f"Posts Saved: {posts_saved}")
            print(f"Elapsed: {elapsed:.1f}s")
            
            # Progress bar
            bar_length = 50
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\n[{bar}] {progress}%")
            
            if status == "completed":
                print(f"\n✅ SCRAPING COMPLETE!")
                print(f"   {posts_saved} new posts saved to database")
                return True
            elif status == "failed":
                print(f"\n❌ SCRAPING FAILED!")
                print(f"   Error: {task.get('error', 'Unknown error')}")
                return False
            else:
                print(f"\n⏳ Still scraping... (check again in 5 seconds)")
                return None
        
        elif response.status_code == 404:
            print(f"❌ Task not found: {task_id}")
            return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_scrape_status.py <task_id> [--watch]")
        print("\nExample:")
        print("  python check_scrape_status.py scrape_1_abc123")
        print("  python check_scrape_status.py scrape_1_abc123 --watch  (auto-refresh)")
        sys.exit(1)
    
    task_id = sys.argv[1]
    watch = "--watch" in sys.argv or "-w" in sys.argv
    
    if watch:
        print(f"Watching task: {task_id}")
        print("Press Ctrl+C to stop\n")
        try:
            while True:
                result = check_status(task_id, watch=True)
                if result is not None:  # Completed or failed
                    break
                time.sleep(3)
        except KeyboardInterrupt:
            print("\n\nStopped watching")
    else:
        check_status(task_id, watch=False)


if __name__ == "__main__":
    main()
