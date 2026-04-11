#!/usr/bin/env python3
"""
Master Scraper Runner - Run any or all scrapers for Vigilis
Supports: X/Twitter, TikTok, Facebook, Website/Blogs

Usage:
    python run_scraper.py x                    # Run X/Twitter scraper
    python run_scraper.py tiktok               # Run TikTok scraper
    python run_scraper.py facebook             # Run Facebook scraper
    python run_scraper.py web                  # Run Website/Blog scraper
    python run_scraper.py all                  # Run all scrapers sequentially
    python run_scraper.py --help               # Show all options
"""

import asyncio
import sys
import argparse
import importlib.util
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')

# Scraper mapping
SCRAPERS = {
    "x": {
        "module": "x_scrapper",
        "function": "scrape_feed",
        "description": "X/Twitter Feed Scraper",
        "async": True
    },
    "twitter": {
        "module": "x_scrapper",
        "function": "scrape_feed",
        "description": "X/Twitter Feed Scraper",
        "async": True
    },
    "tiktok": {
        "module": "tiktok_scrapper",
        "function": "run_tiktok_scraper",
        "description": "TikTok Feed Scraper",
        "async": True
    },
    "facebook": {
        "module": "fb_scrapper",
        "function": "scrape_feed",
        "description": "Facebook Feed Scraper",
        "async": True
    },
    "fb": {
        "module": "fb_scrapper",
        "function": "scrape_feed",
        "description": "Facebook Feed Scraper (Original)",
        "async": True
    },
    "fb-simple": {
        "module": "fb_scrapper_simple",
        "function": "scrape_facebook",
        "description": "Facebook Feed Scraper (Simplified - Recommended)",
        "async": True
    },
    "web": {
        "module": "web_scrapper",
        "function": "scrape_all",
        "description": "Website/Blog Scraper",
        "async": False
    },
    "website": {
        "module": "web_scrapper",
        "function": "scrape_all",
        "description": "Website/Blog Scraper",
        "async": False
    },
    "blog": {
        "module": "web_scrapper",
        "function": "scrape_all",
        "description": "Website/Blog Scraper",
        "async": False
    },
}


def load_scraper_module(module_name):
    """Dynamically load a scraper module"""
    try:
        module_path = Path(__file__).parent / f"{module_name}.py"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"❌ Error loading {module_name}: {e}")
        return None


async def run_async_scraper(scraper_name, scraper_info):
    """Run an async scraper"""
    print(f"\n{'='*60}")
    print(f"🔄 Starting {scraper_info['description']}")
    print(f"{'='*60}\n")
    
    try:
        module = load_scraper_module(scraper_info["module"])
        if not module:
            print(f"❌ Failed to load {scraper_name} scraper\n")
            return False
        
        scraper_func = getattr(module, scraper_info["function"], None)
        if not scraper_func:
            print(f"❌ Function {scraper_info['function']} not found in {scraper_info['module']}\n")
            return False
        
        await scraper_func()
        print(f"\n✅ {scraper_info['description']} completed successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Error running {scraper_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_sync_scraper(scraper_name, scraper_info):
    """Run a synchronous scraper"""
    print(f"\n{'='*60}")
    print(f"🔄 Starting {scraper_info['description']}")
    print(f"{'='*60}\n")
    
    try:
        module = load_scraper_module(scraper_info["module"])
        if not module:
            print(f"❌ Failed to load {scraper_name} scraper\n")
            return False
        
        scraper_func = getattr(module, scraper_info["function"], None)
        if not scraper_func:
            print(f"❌ Function {scraper_info['function']} not found in {scraper_info['module']}\n")
            return False
        
        scraper_func()
        print(f"\n✅ {scraper_info['description']} completed successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Error running {scraper_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_scrapers():
    """Run all scrapers sequentially"""
    print("\n🚀 VIGILIS MASTER SCRAPER - Running all scrapers\n")
    
    results = {}
    scraper_order = ["x", "tiktok", "facebook", "web"]
    
    for scraper_name in scraper_order:
        if scraper_name not in SCRAPERS:
            continue
        
        scraper_info = SCRAPERS[scraper_name]
        
        if scraper_info["async"]:
            success = await run_async_scraper(scraper_name, scraper_info)
        else:
            success = run_sync_scraper(scraper_name, scraper_info)
        
        results[scraper_name] = "✅ SUCCESS" if success else "❌ FAILED"
        print()
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 SCRAPING SUMMARY")
    print(f"{'='*60}")
    for scraper_name, status in results.items():
        print(f"  {SCRAPERS[scraper_name]['description']:<30} {status}")
    print(f"{'='*60}\n")


async def main():
    parser = argparse.ArgumentParser(
        description="Vigilis Master Scraper Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py x              # Run X/Twitter scraper
  python run_scraper.py tiktok         # Run TikTok scraper
  python run_scraper.py facebook       # Run Facebook scraper
  python run_scraper.py web --source dawn  # Run website scraper for specific source
  python run_scraper.py all            # Run all scrapers

Available scrapers: x, tiktok, facebook, web, all
        """
    )
    
    parser.add_argument(
        "scraper",
        nargs="?",
        default="all",
        help="Scraper to run: x, tiktok, facebook, web, or all"
    )
    
    parser.add_argument(
        "--source",
        type=str,
        help="For website scraper: specify source (dawn, toi, jihadintel, etc.)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available scrapers"
    )
    
    args = parser.parse_args()
    
    # List scrapers
    if args.list:
        print("\n📋 Available Scrapers:")
        print("="*50)
        seen = set()
        for scraper_name, info in SCRAPERS.items():
            if scraper_name not in seen:
                print(f"  • {scraper_name:<12} - {info['description']}")
                seen.add(info['module'])
        print("  • all            - Run all scrapers sequentially")
        print("="*50 + "\n")
        return
    
    scraper_name = args.scraper.lower()
    
    # Run all scrapers
    if scraper_name == "all":
        await run_all_scrapers()
        return
    
    # Run specific scraper
    if scraper_name not in SCRAPERS:
        print(f"❌ Unknown scraper: {scraper_name}")
        print("Use --list to see available scrapers")
        sys.exit(1)
    
    scraper_info = SCRAPERS[scraper_name]
    
    # Handle web scraper with source argument
    if scraper_name in ["web", "website", "blog"]:
        try:
            module = load_scraper_module(scraper_info["module"])
            scraper_func = getattr(module, scraper_info["function"])
            
            if args.source:
                print(f"\n{'='*60}")
                print(f"🔄 Starting {scraper_info['description']} (source: {args.source})")
                print(f"{'='*60}\n")
                scraper_func(args.source)
            else:
                print(f"\n{'='*60}")
                print(f"🔄 Starting {scraper_info['description']} (all sources)")
                print(f"{'='*60}\n")
                scraper_func()
            
            print(f"\n✅ {scraper_info['description']} completed!")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        if scraper_info["async"]:
            await run_async_scraper(scraper_name, scraper_info)
        else:
            run_sync_scraper(scraper_name, scraper_info)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping interrupted by user")
        sys.exit(0)
