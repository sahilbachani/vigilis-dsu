#!/usr/bin/env python
"""
Configure website selectors manually with known patterns
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

# Website configurations with common CSS selector patterns
WEBSITE_CONFIGS = [
    {
        "id": 9,
        "name": "BBC News",
        "selectors": {
            "post_selector": "article, [data-testid*='internal-link']",
            "content_selector": "p, [data-testid*='internal-link'] p, .sc-d6d6a30-6",
            "title_selector": "h2, h3, a[data-testid*='internal-link'] h2, a[data-testid*='internal-link'] h3",
            "author_selector": ".contributor, [data-testid*='byline']",
            "date_selector": "time, [data-testid*='published-at']",
            "link_selector": "a[href*='/news/'], a[data-testid*='internal-link']"
        }
    },
    {
        "id": 7,
        "name": "Dawn News",
        "selectors": {
            "post_selector": ".story-item, article, .post",
            "content_selector": ".story-text, .news-content, p",
            "title_selector": ".story-title, h2, h3, a.story-link",
            "author_selector": ".story-author, .by-author, .author-name",
            "date_selector": ".story-date, time, .publish-date",
            "link_selector": ".story-link, article a"
        }
    },
]

def apply_selectors(website_id: int, name: str, selectors: dict):
    """Apply CSS selectors to a website"""
    print(f"\n{'='*70}")
    print(f"🎯 APPLYING SELECTORS: {name} (ID: {website_id})")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sources/{website_id}/configure",
            json={"selectors": selectors},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Selectors applied!")
            print(f"   Response: {result}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🛠️  MANUAL WEBSITE SELECTOR CONFIGURATION")
    print("="*70)
    
    for config in WEBSITE_CONFIGS:
        apply_selectors(config["id"], config["name"], config["selectors"])
        time.sleep(1)
    
    print(f"\n{'='*70}")
    print(f"✅ ALL CONFIGURATIONS COMPLETE")
    print(f"{'='*70}\n")
