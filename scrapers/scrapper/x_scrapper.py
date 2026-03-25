import asyncio
import random
import datetime
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from dotenv import load_dotenv
from database import get_db_session, get_or_create_source, save_post_to_db
from media_downloader import download_media
from video_downloader import download_video

load_dotenv()

# --- CONFIGURATION ---
HEADLESS_MODE = os.getenv("HEADLESS", "false").lower() == "true"
USER_DATA_DIR = "./user_data"
TARGET_URL = "https://x.com/home"

# Twitter source configuration
TWITTER_PLATFORM = "Twitter/X"
TWITTER_SOURCE_NAME = "X Feed"
TWITTER_URL = "https://x.com/home"


def save_posts_to_db(tweets):
    """
    Save scraped tweets to the database
    Does NOT modify login/logout functionality
    """
    if not tweets:
        return

    db = get_db_session()
    try:
        # Get or create the Twitter/X source
        source_id = get_or_create_source(
            db, 
            TWITTER_PLATFORM, 
            TWITTER_SOURCE_NAME, 
            TWITTER_URL
        )

        saved_count = 0
        for t in tweets:
            try:
                post_id = save_post_to_db(
                    db,
                    source_id=source_id,
                    author=t["author"],
                    text_content=t["content"],
                    timestamp=t["timestamp"],
                    url=t.get("url"),  # Now saves the actual extracted URL
                    confidence_score=None,
                    category="twitter",
                    media_items=t.get("media_items", [])
                )
                if post_id:
                    saved_count += 1
            except Exception as e:
                print(f"Error saving post from {t['author']}: {e}")
                continue
        
        print(f"--> Successfully saved {saved_count} posts to database")
    
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        db.close()



async def scrape_feed():
    lockfile_path = os.path.join(USER_DATA_DIR, "lockfile")
    if os.path.exists(lockfile_path):
        try:
            os.remove(lockfile_path)
            print("Removed stale lockfile.")
        except OSError:
            print("Could not remove lockfile.")

    async with async_playwright() as p:
        # Use a more recent User Agent
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )

        print("Launching browser with persistent context...")
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=HEADLESS_MODE,
            args=[
                "--disable-blink-features=AutomationControlled", 
                "--start-maximized",
                "--no-sandbox",
                "--disable-infobars"
            ],
            user_agent=user_agent,
            viewport=None
        )

        # Removed manual webdriver override as playwright-stealth handles it better

        page = context.pages[0] if context.pages else await context.new_page()

        await Stealth(
            navigator_user_agent_override=user_agent
        ).apply_stealth_async(page)

        print(f"Navigating to {TARGET_URL}...")
        await page.goto(TARGET_URL)

        try:
            await page.wait_for_selector(
                'div[data-testid="tweetTextarea_0"], input[autocomplete="username"]',
                timeout=10000
            )
        except:
            print("Page load timeout.")
            await context.close()
            return

        if await page.query_selector('input[autocomplete="username"]'):
            print("\n!!! LOGIN REQUIRED !!!")
            await page.wait_for_timeout(60000)

        try:
            await page.wait_for_selector('article[data-testid="tweet"]')
        except:
            print("No tweets found.")
            await context.close()
            return

        # Export Cookies for yt-dlp to bypass video download blocking
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
        
        cookie_file_path = "twitter_cookies.txt"
        with open(cookie_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(cookie_lines))

        print("Starting active scrape loop...")
        tweets_seen = set()

        for _ in range(10):
            tweet_elements = await page.query_selector_all(
                'article[data-testid="tweet"]'
            )

            batch_data = []

            for tweet in tweet_elements:
                try:
                    author_elem = await tweet.query_selector(
                        'div[data-testid="User-Name"] a span'
                    )
                    author = await author_elem.inner_text() if author_elem else "Unknown"

                    handle_elem = await tweet.query_selector(
                        'div[data-testid="User-Name"] a'
                    )
                    handle_href = await handle_elem.get_attribute("href") if handle_elem else ""
                    handle = handle_href.replace("/", "@") if handle_href else "Unknown"

                    time_elem = await tweet.query_selector('time')
                    timestamp = (
                        await time_elem.get_attribute("datetime")
                        if time_elem else datetime.datetime.utcnow().isoformat()
                    )

                    # Extract Content
                    content_elem = await tweet.query_selector(
                        'div[data-testid="tweetText"]'
                    )
                    content = (
                        await content_elem.inner_text()
                        if content_elem else "[Media/No Text]"
                    )

                    # Extract URL
                    post_url = None
                    if time_elem:
                        # Time element parent holds the permalink
                        permalink_elem = await time_elem.evaluate_handle('el => el.parentElement')
                        if permalink_elem:
                            href = await permalink_elem.get_attribute('href')
                            if href:
                                post_url = f"https://x.com{href}"

                    # Extract Media (Images for now)
                    media_items = []
                    img_elems = await tweet.query_selector_all('img[src*="pbs.twimg.com/media"]')
                    for img in img_elems:
                        src = await img.get_attribute("src")
                        if src:
                            # Clean up Twitter image URLs (they often end with ?format=jpg&name=...) 
                            # We can just download the raw URL
                            local_path = download_media(src, "twitter", "image")
                            if local_path:
                                media_items.append({
                                    "type": "image",
                                    "url": src,
                                    "local_path": local_path
                                })
                                
                    # Extract Video 
                    # If this tweet has a video player, feed the post_url to yt-dlp
                    has_video = await tweet.query_selector('video') or await tweet.query_selector('div[data-testid="videoPlayer"]')
                    if has_video and post_url:
                        video_local_path = download_video(post_url, "twitter", cookie_file_path)
                        if video_local_path:
                            # It's better to store the permalink as the media URL since blob streams expire anyway
                            media_items.append({
                                "type": "video",
                                "url": post_url,
                                "local_path": video_local_path
                            })

                    unique_sig = f"{handle}-{timestamp}"

                    if unique_sig not in tweets_seen:
                        tweets_seen.add(unique_sig)
                        batch_data.append({
                            "author": author,
                            "handle": handle,
                            "content": content,
                            "timestamp": timestamp,
                            "url": post_url,
                            "media_items": media_items
                        })

                except Exception as e:
                    print(f"Error parsing tweet: {e}")
                    continue

            if batch_data:
                save_posts_to_db(batch_data)

            await page.mouse.wheel(0, 1000)
            wait_time = random.uniform(2000, 5000)
            print(f"Scrolling... waiting {wait_time / 1000:.2f}s")
            await page.wait_for_timeout(wait_time)

        await context.close()
        print("Scraping finished.")


if __name__ == "__main__":
    asyncio.run(scrape_feed())
