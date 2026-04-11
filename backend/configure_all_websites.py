#!/usr/bin/env python
"""
Configure all recently added website sources
Auto-detect CSS selectors for each website
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

# Recently added websites
WEBSITES = [
    {"id": 9, "name": "BBC News", "url": "https://www.bbc.com/news"},
]

# Older websites to configure
OLDER_WEBSITES = [
    {"id": 7, "name": "Dawn News", "url": "https://www.dawn.com"},
    {"id": 8, "name": "Bellingcat", "url": "https://www.bellingcat.com"},
]

def configure_website(website_id: int, name: str, url: str):
    """Configure a website with auto-detect"""
    print(f"\n{'='*70}")
    print(f"🔧 CONFIGURING: {name} (ID: {website_id})")
    print(f"   URL: {url}")
    print(f"{'='*70}")
    
    try:
        # Step 1: Validate website configuration
        response = requests.post(
            f"{BASE_URL}/sources/validate-config",
            json={"website_id": website_id, "url": url},
            timeout=30
        )
        
        if response.status_code == 200:
            config = response.json()
            
            if config.get("success"):
                print(f"✅ Configuration successful!")
                print(f"   Posts found: {config.get('posts_count', 0)}")
                print(f"   Sample posts shown")
                return True
            else:
                print(f"❌ Configuration failed: {config.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌐 BULK WEBSITE CONFIGURATION TOOL")
    print("="*70)
    
    success_count = 0
    
    # Configure recent websites
    for website in WEBSITES:
        if configure_website(website["id"], website["name"], website["url"]):
            success_count += 1
        time.sleep(1)
    
    # Configure older websites
    for website in OLDER_WEBSITES:
        if configure_website(website["id"], website["name"], website["url"]):
            success_count += 1
        time.sleep(1)
    
    print(f"\n{'='*70}")
    print(f"✅ CONFIGURATION COMPLETE: {success_count}/{len(WEBSITES) + len(OLDER_WEBSITES)} websites configured")
    print(f"{'='*70}\n")
