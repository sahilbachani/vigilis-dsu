import asyncio
import os
import datetime
import sys
from pathlib import Path
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
from database import get_db_session, get_or_create_source, save_video_to_db
from ai_pipeline.video.pipeline import get_video_pipeline
from media_downloader import download_media
from video_downloader import download_video
from thumbnail_extractor import extract_video_thumbnail, get_thumbnail_path, get_thumbnail_url

load_dotenv()

# Add ai_pipeline to path for AI analysis
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import AI pipeline lazily so scraper can still run without ML dependencies.
AI_PIPELINE_AVAILABLE = False
AIAnalysisPipeline = None

def load_ai_pipeline():
    """Lazy load AI pipeline only when needed."""
    global AI_PIPELINE_AVAILABLE, AIAnalysisPipeline
    if AI_PIPELINE_AVAILABLE or AIAnalysisPipeline:
        return AIAnalysisPipeline

    try:
        from ai_pipeline.integration import AIAnalysisPipeline as Pipeline
        AIAnalysisPipeline = Pipeline
        AI_PIPELINE_AVAILABLE = True
        return AIAnalysisPipeline
    except Exception as e:
        print(f"⚠️ Warning: AI Pipeline not available ({e})")
        AI_PIPELINE_AVAILABLE = False
        return None

# We will scrape explore first, then fallback to foryou if needed
TARGET_URLS = [
    "https://www.tiktok.com/explore",
    "https://www.tiktok.com/foryou",
]

# Chrome profile directory to reuse session (bypasses captchas if logged in manually once)
USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiktok_user_data")
os.makedirs(USER_DATA_DIR, exist_ok=True)

# Limit to 50 posts per scrape session
POSTS_LIMIT = 50

# Helper function for URL deduplication with database persistence
def get_seen_urls_from_db(db, source_id) -> set:
    """Load previously scraped URLs from database to avoid duplicates across runs."""
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT url FROM posts WHERE source_id = :source_id"), {"source_id": source_id})
        return {row[0] for row in result.fetchall() if row[0]}
    except Exception as e:
        print(f"[WARN] Could not load seen URLs from DB: {e}")
        return set()

async def retry_with_backoff(func, max_retries=3, initial_delay=1):
    """Retry a function with exponential backoff."""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"  [RETRY] Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
            delay *= 2

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
    source_name = "TikTok Explore"
    source_id = get_or_create_source(db, platform_id, source_name, TARGET_URLS[0])

    # Initialize AI Pipeline if available
    ai_pipeline = None
    video_pipeline = None
    AIAnalysisPipeline_class = load_ai_pipeline()

    if AIAnalysisPipeline_class:
        try:
            print("=" * 60)
            print("Initializing AI Pipeline...")
            print("=" * 60)
            from ai_pipeline.models_loader import ModelsLoader
            models_loader = ModelsLoader()
            ai_pipeline = AIAnalysisPipeline_class(models_loader)
            print("✓ AI Pipeline initialized for real-time analysis\n")
        except Exception as e:
            print(f"⚠️ Failed to initialize AI Pipeline: {e}")
            print("   Continuing without real-time analysis...\n")
            ai_pipeline = None

    try:
        video_pipeline = get_video_pipeline()
    except Exception as e:
        print(f"⚠️ Failed to initialize video pipeline: {e}")
        video_pipeline = None

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

        async def try_accept_cookies() -> None:
            try:
                await page.locator("button:has-text('Accept')").first.click(timeout=1500)
            except Exception:
                pass
            try:
                await page.locator("button:has-text('Allow')").first.click(timeout=1500)
            except Exception:
                pass

        async def navigate_to(url: str, max_retries: int = 2) -> bool:
            """Navigate to URL with retry logic. Returns True on success."""
            for attempt in range(max_retries):
                try:
                    print(f"Navigating to {url}... (attempt {attempt + 1}/{max_retries})")
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await try_accept_cookies()
                    return True
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"[ERROR] Navigation failed after {max_retries} attempts: {e}")
                        return False
                    print(f"[RETRY] Navigation attempt {attempt + 1} failed: {e}. Retrying...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            return False

        if not await navigate_to(TARGET_URLS[0]):
            print("[ERROR] Failed to navigate to initial URL, aborting scraper")
            db.close()
            await context.close()
            return

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
        if not cookie_file_path or not os.path.exists(cookie_file_path):
            print("⚠️ Warning: Cookie file not created, continuing without saved cookies")
        
        # Load previously scraped URLs to prevent duplicates across runs
        posts_seen = get_seen_urls_from_db(db, source_id)
        print(f"[DEDUP] Loaded {len(posts_seen)} previously scraped URLs from database")
        
        total_extracted = 0
        scroll_attempts = 0

        async def extract_video_urls() -> list[str]:
            urls: list[str] = []

            try:
                anchors = await page.query_selector_all('a[href*="/video/"]')
                for a in anchors:
                    href = await a.get_attribute("href")
                    if href:
                        urls.append(href)
            except Exception:
                pass

            if not urls:
                try:
                    anchors = await page.query_selector_all('a[data-e2e*="video"]')
                    for a in anchors:
                        href = await a.get_attribute("href")
                        if href:
                            urls.append(href)
                except Exception:
                    pass

            if not urls:
                try:
                    html = await page.content()
                    import re
                    urls.extend(re.findall(r"https?://www\.tiktok\.com/@[^\"\']+/video/\d+", html))
                except Exception:
                    pass

            # Normalize
            normalized = []
            for url in urls:
                if url.startswith('/'):
                    url = f"https://www.tiktok.com{url}"
                if url not in normalized:
                    normalized.append(url)
            return normalized

        empty_link_cycles = 0
        current_target_index = 0

        while total_extracted < POSTS_LIMIT and scroll_attempts < 10:
            scroll_attempts += 1
            print(f"\n[SCRAPE] Scroll attempt {scroll_attempts}/10")
            
            try:
                # Check if page is still valid
                if page.is_closed():
                    print("[ERROR] Page was closed!")
                    break
                
                # TikTok Explorer uses varying classes; collect URLs via multiple strategies.
                video_urls = await extract_video_urls()

                if not video_urls:
                    print("[WARN] No video links found, scrolling...")
                    await page.mouse.wheel(0, 3000)
                    await page.wait_for_timeout(3000)
                    empty_link_cycles += 1

                    if empty_link_cycles >= 3 and current_target_index + 1 < len(TARGET_URLS):
                        current_target_index += 1
                        print(f"[INFO] Switching to fallback feed: {TARGET_URLS[current_target_index]}")
                        await navigate_to(TARGET_URLS[current_target_index])
                        empty_link_cycles = 0
                    continue

                empty_link_cycles = 0

                print(f"[SCRAPE] Found {len(video_urls)} video links")
                batch_data = []

                for link_idx, post_url in enumerate(video_urls):
                    if total_extracted + len(batch_data) >= POSTS_LIMIT:
                        break
                    
                    try:
                        if not post_url or post_url in posts_seen:
                            continue

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
                            # Try finding image nearby by searching the page for matching URL
                            locator = page.locator(f'a[href="{post_url}"] img')
                            if await locator.count() > 0:
                                alt_text = await locator.first.get_attribute('alt')
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
                            if ai_pipeline:
                                analysis_result = ai_pipeline.analyzer.analyze_text(p["content"])
                                if analysis_result.flagged:
                                    post_id = ai_pipeline.db_ops.save_analyzed_post(
                                        db=db,
                                        source_id=source_id,
                                        author=p["author"],
                                        text_content=p["content"],
                                        timestamp=datetime.datetime.fromisoformat(p["timestamp"]),
                                        analysis_result=analysis_result,
                                        url=p.get("url"),
                                        category="tiktok"
                                    )
                                    if post_id:
                                        saved += 1
                                        print(f"  [SAVED] Post {total_extracted + saved}/{POSTS_LIMIT}")
                                else:
                                    print("  [SKIP] Not flagged")
                            else:
                                print("  [SKIP] AI Pipeline unavailable (flagged-only mode)")

                            if video_pipeline and p.get("media_items"):
                                for media in p["media_items"]:
                                    if media.get("type") != "video" or not media.get("local_path"):
                                        continue

                                    try:
                                        video_abs_path = os.path.join(
                                            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                            "backend",
                                            media["local_path"].lstrip("/")
                                        )

                                        if not os.path.exists(video_abs_path):
                                            print(f"  [WARN] Video file not found: {video_abs_path}")
                                            continue

                                        # Validate video file is not corrupted
                                        if os.path.getsize(video_abs_path) < 1024:
                                            print(f"  [WARN] Video file too small (possibly corrupted): {video_abs_path}")
                                            continue

                                        video_result = video_pipeline.analyze_video(
                                            video_url=video_abs_path,
                                            source_id=source_id,
                                            platform="tiktok",
                                        )

                                        audio_score = 0.0
                                        visual_score = 0.0
                                        if video_result.audio_scores:
                                            audio_score = max(
                                                video_result.audio_scores.get("emotion_anger", 0.0),
                                                video_result.audio_scores.get("emotion_fear", 0.0),
                                                video_result.audio_scores.get("emotion_disgust", 0.0),
                                            )
                                        if video_result.visual_scores:
                                            visual_score = max(
                                                video_result.visual_scores.get("violence_score", 0.0),
                                                video_result.visual_scores.get("emotion_anger", 0.0),
                                                video_result.visual_scores.get("emotion_fear", 0.0),
                                                video_result.visual_scores.get("emotion_disgust", 0.0),
                                            )

                                        # Extract thumbnail if video is flagged
                                        thumbnail_url = None
                                        if video_result.flagged:
                                            try:
                                                import hashlib
                                                url_hash = hashlib.md5((media.get("url") or p.get("url")).encode()).hexdigest()
                                                thumbnail_path = get_thumbnail_path("tiktok", url_hash)
                                                
                                                if extract_video_thumbnail(video_abs_path, thumbnail_path):
                                                    thumbnail_url = get_thumbnail_url("tiktok", url_hash)
                                                    print(f"  [THUMBNAIL] Generated: {thumbnail_url}")
                                            except Exception as thumb_err:
                                                print(f"  [WARN] Failed to extract thumbnail: {thumb_err}")

                                        save_video_to_db(
                                            db=db,
                                            source_id=source_id,
                                            url=media.get("url") or p.get("url"),
                                            video_path=media.get("local_path"),
                                            transcript=video_result.transcript,
                                            overall_score=video_result.overall_score,
                                            confidence_score=video_result.confidence,
                                            audio_emotion_score=audio_score,
                                            visual_emotion_score=visual_score,
                                            flagged=video_result.flagged,
                                            analysis_timestamp=datetime.datetime.utcnow(),
                                            platform="tiktok",
                                            title=p.get("content"),
                                            thumbnail_url=thumbnail_url,
                                        )
                                        if video_result.flagged:
                                            print(f"  [VIDEO SAVED] Flagged video saved to database")
                                    except Exception as e:
                                        print(f"  [ERROR] Failed to analyze video: {e}")
                                        import traceback
                                        traceback.print_exc()
                                        continue
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
