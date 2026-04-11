import asyncio
import os
import datetime
from urllib.parse import urlparse
from playwright.async_api import async_playwright
try:
    from playwright_stealth import stealth_async as Stealth
except ImportError:
    # Fallback if stealth is missing
    class Stealth:
        def __init__(self, **kwargs): pass
        async def apply_stealth_async(self, page): pass

from dotenv import load_dotenv
from database import get_db_session, get_or_create_source, save_post_to_db
from media_downloader import download_media
from video_downloader import download_video

load_dotenv()

# We will scrape the explore/foryou page
TARGET_URL = "https://www.tiktok.com/explore"

# Chrome profile directory to reuse session (bypasses captchas if logged in manually once)
USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiktok_user_data")
os.makedirs(USER_DATA_DIR, exist_ok=True)

# Limit to 50 posts per scrape session
POSTS_LIMIT = 50

async def setup_tiktok_cookies(context):
    cookies = await context.cookies()
    cookie_lines = ["# Netscape HTTP Cookie File\n"]
    for c in cookies:
        domain = c.get('domain', '')
        include_subdomains = 'TRUE' if domain.startswith('.') else 'FALSE'
        path = c.get('path', '/')
        secure = 'TRUE' if c.get('secure', False) else 'FALSE'
        expires = str(int(c.get('expires', 0))) if c.get('expires', -1) > 0 else '0'
        name = c.get('name', '')
        value = c.get('value', '')
        cookie_lines.append(f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expires}\t{name}\t{value}")
    
    cookie_file_path = "tiktok_cookies.txt"
    with open(cookie_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(cookie_lines))
    return cookie_file_path

async def run_tiktok_scraper():
    print("Starting TikTok Scraper...")
    
    db = get_db_session()
    platform_id = "tiktok"
    source_name = "TikTok Foryou"
    source_id = get_or_create_source(db, platform_id, source_name, TARGET_URL)

    async with async_playwright() as p:
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )

        print("Launching browser with persistent context...")
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled", 
                "--start-maximized",
                "--no-sandbox"
            ],
            user_agent=user_agent,
            viewport={"width": 1280, "height": 720}
        )

        page = context.pages[0] if context.pages else await context.new_page()

        try:
             # Ensure stealth is applied to bypass TikTok captchas
             await Stealth(navigator_user_agent_override=user_agent).apply_stealth_async(page)
        except Exception as e:
             print("Stealth failed to apply, continuing anyway:", e)

        print(f"Navigating to {TARGET_URL}...")
        
        # TikTok heavily rate-limits. Use domcontentloaded to avoid waiting on stuck tracking scripts.
        try:
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"Initial navigation paused/timed out, continuing: {e}")

        # Wait for either captcha or content
        print("Waiting for feed or captchas...")
        await page.wait_for_timeout(5000)

        # Look for Captcha 
        captcha = await page.query_selector('div[class*="captcha"]') or await page.query_selector('div#captcha-verify')
        if captcha:
             print("!!! TIKTOK CAPTCHA DETECTED !!!")
             print("Please open the scraper visually or bypass the puzzle manually.")
             # We will try to proceed anyway if it's passive

        cookie_file_path = await setup_tiktok_cookies(context)
        
        posts_seen = set()
        total_extracted = 0
        scroll_attempts = 0

        while total_extracted < POSTS_LIMIT and scroll_attempts < 10:
            scroll_attempts += 1
            print(f"\n[SCRAPE] Scroll attempt {scroll_attempts}/10")
            
            try:
                # Check if page is still valid
                if page.is_closed():
                    print("[ERROR] Page was closed!")
                    break
                
                # TikTok Explorer uses slightly varying classes, but generally a items grid or feed container.
                # a tags containing '/video/' are the actual post links
                try:
                    video_links = await page.query_selector_all('a[href*="/video/"]')
                except Exception as e:
                    print(f"[WARN] Could not find video links: {e}")
                    video_links = []
                
                if not video_links:
                    print("[WARN] No video links found, scrolling...")
                    await page.mouse.wheel(0, 3000)
                    await page.wait_for_timeout(3000)
                    continue
                
                print(f"[SCRAPE] Found {len(video_links)} video links")
                batch_data = []

                for link_idx, link in enumerate(video_links):
                    if total_extracted + len(batch_data) >= POSTS_LIMIT:
                        break
                    
                    try:
                        post_url = await link.get_attribute("href")
                        if not post_url or post_url in posts_seen:
                            continue
                            
                        if post_url.startswith('/'):
                            post_url = f"https://www.tiktok.com{post_url}"

                        posts_seen.add(post_url)
                        
                        # Extract Author from URL (e.g. https://www.tiktok.com/@username/video/1234)
                        author = "Unknown"
                        parsed = urlparse(post_url)
                        path_parts = parsed.path.split('/')
                        if len(path_parts) > 2 and path_parts[1].startswith('@'):
                            author = path_parts[1].replace('@', '')

                        # For description, climb DOM tree and hunt for title
                        # TikTok explores page typically uses div title props or image alts
                        content = "[TikTok Video/No Caption]"
                        try:
                            # Try finding image inside link to get alt text
                            img = await link.query_selector('img')
                            if img:
                                alt_text = await img.get_attribute('alt')
                                if alt_text:
                                    content = alt_text
                        except Exception:
                            pass

                        timestamp = datetime.datetime.utcnow().isoformat()
                        
                        media_items = []
                        
                        # Offload directly to yt-dlp to bypass DOM complexities
                        print(f"  [TikTok] Downloading: {post_url}")
                        video_local_path = download_video(post_url, "tiktok", cookie_file_path)
                        
                        if video_local_path:
                            media_items.append({
                                "type": "video",
                                "url": post_url,
                                "local_path": video_local_path
                            })

                        batch_data.append({
                            "author": author,
                            "content": content,
                            "timestamp": timestamp,
                            "url": post_url,
                            "media_items": media_items
                        })

                    except Exception as e:
                        print(f"  [ERROR] Error extracting video {link_idx}: {e}")
                        continue

                if batch_data:
                    saved = 0
                    for p in batch_data:
                        try:
                            post_id = save_post_to_db(
                                db=db,
                                source_id=source_id,
                                author=p["author"],
                                text_content=p["content"],
                                timestamp=p["timestamp"],
                                url=p.get("url"),
                                confidence_score=None,
                                category="tiktok"
                            )
                            if post_id:
                                saved += 1
                                print(f"  [SAVED] Post {total_extracted + saved}/{POSTS_LIMIT}")
                        except Exception as e:
                            print(f"  [ERROR] Failed to save post: {e}")
                    
                    total_extracted += saved
                    print(f"[SCRAPE] Batch complete: {saved}/{len(batch_data)} saved")

                # Scroll down to load more
                if total_extracted < POSTS_LIMIT:
                    print("[SCROLL] Scrolling down...")
                    try:
                        await page.mouse.wheel(0, 3000)
                        await page.wait_for_timeout(3000)
                    except Exception as e:
                        print(f"[ERROR] Scroll failed: {e}")
                        break
            
            except Exception as e:
                print(f"[ERROR] Iteration {scroll_attempts} failed: {e}")
                await page.wait_for_timeout(1000)
                continue

        print(f"Finished TikTok scrape. Total unique posts saved: {total_extracted}")
        await context.close()
        
        # Close database session to ensure all commits are flushed
        db.close()

if __name__ == "__main__":
    asyncio.run(run_tiktok_scraper())
