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
HEADLESS_MODE = False  # Always show browser window for debugging
USER_DATA_DIR = "./user_data"
TARGET_URL = "https://www.facebook.com/"

# Facebook source configuration
FB_PLATFORM = "Facebook"
FB_SOURCE_NAME = "Facebook Feed"
FB_URL = "https://www.facebook.com/"

# Adjustable limit: 0 for infinite, or any positive integer
POSTS_LIMIT = 30


def save_posts_to_db(posts):
    """
    Save scraped posts to the database
    """
    if not posts:
        return

    db = get_db_session()
    try:
        # Get or create the Facebook source
        source_id = get_or_create_source(
            db, 
            FB_PLATFORM, 
            FB_SOURCE_NAME, 
            FB_URL
        )

        saved_count = 0
        for p in posts:
            try:
                post_id = save_post_to_db(
                    db,
                    source_id=source_id,
                    author=p["author"],
                    text_content=p["content"],
                    timestamp=p["timestamp"],
                    url=p.get("url"),
                    confidence_score=None,
                    category="facebook"
                )
                if post_id:
                    saved_count += 1
            except Exception as e:
                print(f"Error saving post from {p['author']}: {e}")
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

        page = context.pages[0] if context.pages else await context.new_page()

        await Stealth(
            navigator_user_agent_override=user_agent
        ).apply_stealth_async(page)

        print(f"Navigating to {TARGET_URL}...")
        await page.goto(TARGET_URL)

        # Check for login requirement
        try:
            await page.wait_for_selector(
                'input[name="email"], input[name="pass"], div[role="feed"], div[role="main"]',
                timeout=15000
            )
        except:
            print("Page load timeout.")
            await context.close()
            return

        # Simple heuristic to detect if we need to login
        if await page.query_selector('input[name="email"]') or await page.query_selector('button[name="login"]'):
            print("\n!!! LOGIN REQUIRED !!!")
            print("Please log in to Facebook manually in the opened browser window.")
            print("Waiting 60 seconds for manual login...")
            await page.wait_for_timeout(60000)
            
            # Re-check if still not logged in, wait another 60 seconds
            if await page.query_selector('input[name="email"]'):
                 print("Still not logged in. Waiting another 60 seconds...")
                 await page.wait_for_timeout(60000)

        # Ensure we are on the feed
        print("Waiting for feed to load...")
        try:
            # Facebook feed role is typically "feed" or posts have role "article"
            await page.wait_for_selector('div[role="feed"], div[data-pagelet*="FeedUnit"]', timeout=30000)
        except:
             print("Warning: Could not strictly find the feed container, but will try searching for posts anyway.")

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
        
        cookie_file_path = "facebook_cookies.txt"
        with open(cookie_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(cookie_lines))

        print("Starting active scrape loop...")
        posts_seen = set()
        total_extracted = 0

        # Max iterations to prevent infinite loop just in case, or we run until POSTS_LIMIT
        max_iterations = 100 
        iteration = 0

        while True:
            iteration += 1
            if iteration > max_iterations and POSTS_LIMIT > 0:
                 break

            if POSTS_LIMIT > 0 and total_extracted >= POSTS_LIMIT:
                print(f"Reached the target limit of {POSTS_LIMIT} posts.")
                break

            # Find post text elements first, then get their parent containers
            message_elems = await page.query_selector_all('div[data-ad-preview="message"], div[dir="auto"]')
            
            post_elements = []
            for msg in message_elems:
                # Get the overarching post container wrapper
                wrapper_handle = await msg.evaluate_handle(
                    'el => el.closest(\'div[data-pagelet^="FeedUnit_"]\') || el.closest(\'div[role="article"]\') || el.parentElement.parentElement.parentElement.parentElement'
                )
                element = wrapper_handle.as_element()
                if element:
                    post_elements.append(element)

            print(f"Found {len(post_elements)} post wrappers on page.")

            batch_data = []

            for post in post_elements:
                if POSTS_LIMIT > 0 and total_extracted + len(batch_data) >= POSTS_LIMIT:
                    break # Stop processing if batch will exceed limit

                try:
                    # Extract Author (Improved logic for Groups & Anonymous)
                    author = "Unknown"
                    try:
                        extracted_author = await post.evaluate('''el => {
                            let text = "";
                            // Often headers h2, h3, h4 contain the author and group info
                            const headers = el.querySelectorAll('h2, h3, h4');
                            for (const h of headers) {
                                if (h.innerText && h.innerText.length > 2 && !h.innerText.includes('Suggested') && !h.innerText.includes('Sponsored')) {
                                    text = h.innerText.trim();
                                    break;
                                }
                            }
                            
                            // If no header, look for strong tags
                            if (!text) {
                                const strongs = el.querySelectorAll('strong');
                                let parts = [];
                                for (const s of strongs) {
                                    if (s.innerText && s.innerText.length > 2 && !s.innerText.includes('Suggested') && !s.innerText.includes('Sponsored')) {
                                        parts.push(s.innerText.trim());
                                        if (parts.length >= 2) break; // only care about first two (Author and Group)
                                    }
                                }
                                if (parts.length > 0) {
                                    if (parts.length >= 2) {
                                        text = parts[0] + " \\n " + parts[1];
                                    } else {
                                        text = parts[0];
                                    }
                                }
                            }

                            if (!text) {
                                const aria = el.querySelector('a[aria-label]');
                                if(aria) text = aria.getAttribute('aria-label');
                            }

                            if (!text) return "Unknown";

                            // Clean up text if it contains newlines (like "John Doe \\n Group Name")
                            let lines = text.split('\\n').map(p => p.trim()).filter(p => p.length > 0 && !p.includes('d') && !p.includes('h')); // roughly ignore date lines
                            
                            // Fallback if split fails or has junk
                            if (lines.length === 0) return "Unknown";
                            
                            let cleaned = lines[0];
                            if (lines.length > 1 && lines[1] !== lines[0]) {
                                // Ignore random dots or single characters
                                if (lines[1] !== '·' && lines[1].length > 1) {
                                    cleaned += " (" + lines[1] + ")";
                                }
                            }

                            // Replace common separators with brackets if they represent group posts
                            if (cleaned.includes(' > ')) {
                                let parts = cleaned.split(' > ');
                                cleaned = parts[0].trim() + " (" + parts[1].trim() + ")";
                            } else if (cleaned.includes(' · ')) {
                                let parts = cleaned.split(' · ');
                                if (parts[1] && parts[1].length > 1 && parts[1].trim() !== '·') {
                                    cleaned = parts[0].trim() + " (" + parts[1].trim() + ")";
                                } else {
                                    cleaned = parts[0].trim();
                                }
                            }
                            
                            // Catch specific edge case for anonymous
                            if (cleaned.toLowerCase().includes('anonymous member') || cleaned.toLowerCase().includes('anonymous')) {
                                // ensure we group it right
                                if (!cleaned.includes('(')) {
                                   let groupSearch = el.querySelector('a[href*="/groups/"]');
                                   if (groupSearch) {
                                       let possibleGroup = groupSearch.innerText;
                                       if(possibleGroup && possibleGroup.length > 2) {
                                           return "Anonymous Member (" + possibleGroup.trim() + ")";
                                       }
                                   }
                                }
                            }

                            return cleaned;
                        }''')
                        if extracted_author:
                            author = extracted_author
                    except Exception as e:
                        print(f"Failed to extract author: {e}")

                    # Extract Content
                    # Post text is usually inside a div with data-ad-preview="message" or similar
                    content_elem = await post.query_selector('div[data-ad-preview="message"]')
                    if not content_elem:
                         content_elem = await post.query_selector('div[dir="auto"]') # simple fallback
                         
                    # Click 'See more' if it exists to expand the full post text
                    try:
                        # Find buttons with text 'See more' or 'See More'
                        see_more_btns = await post.query_selector_all('div[role="button"]')
                        for btn in see_more_btns:
                            btn_text = await btn.inner_text()
                            if btn_text and btn_text.strip().lower() == "see more":
                                await btn.evaluate('el => el.click()') # safer than playwright click sometimes
                                await page.wait_for_timeout(800)  # Wait for text to expand
                    except Exception as e:
                        print(f"Failed to click 'See more': {e}")

                    content = await content_elem.inner_text() if content_elem else "[Media/No Text]"
                    
                    # Manual fallback: if the button failed or left text, string-replace "See more" or "... See more"
                    content = content.replace("... See more", "").replace(" See more", "").replace("See more", "").strip()

                    # Filter out small UI artifacts
                    if len(content) < 5 and (content == author or "..." in content):
                        continue 

                    # Extract URL
                    post_url = None
                    try:
                        # Find the permalink by searching for a[role="link"] that looks like a timestamp/permalink
                        # Evaluate in browser context to avoid messy Python DOM traversal
                        extracted_url = await post.evaluate('''el => {
                            // FB often puts the permalink on the timestamp anchor
                            const links = Array.from(el.querySelectorAll('a[href]'));
                            
                            // Strategy 1: Look for explicit post/video links
                            for (const link of links) {
                                const href = link.getAttribute('href');
                                if (href && (href.includes('/posts/') || href.includes('fbid=') || href.includes('/videos/') || href.includes('/permalink/') || href.includes('/story.php'))) {
                                    return href;
                                }
                            }
                            
                            // Strategy 2: Look for typical timestamp link shapes (role="link" with tabindex="0")
                            const timestampLinks = Array.from(el.querySelectorAll('a[role="link"][tabindex="0"]'));
                            for (const link of timestampLinks) {
                                const href = link.getAttribute('href');
                                if (href && href !== '#' && !href.includes('/groups/') && !href.includes('/user/')) {
                                     if(href.includes('?__cft__')) return href.split('?__cft__')[0];
                                     return href;
                                }
                            }
                            
                            // Strategy 3: Grab the very first external href that isn't a hashtag or blank
                            for (const link of links) {
                                const href = link.getAttribute('href');
                                if (href && href !== '#' && !href.startsWith('javascript:')) {
                                     if(href.includes('?__cft__')) return href.split('?__cft__')[0];
                                     return href;
                                }
                            }
                            return null;
                        }''')
                        
                        if extracted_url:
                            # Clean up the URL format
                            if extracted_url.startswith('/'):
                                post_url = f"https://www.facebook.com{extracted_url}"
                            elif extracted_url.startswith('http'):
                                post_url = extracted_url
                            else:
                                post_url = f"https://{extracted_url}"
                            
                            # remove trailing query params cleanly if needed
                            if '?__cft__' in post_url:
                                post_url = post_url.split('?__cft__')[0]

                    except Exception as e:
                        print(f"Error parsing URL: {e}")

                    # Extract timestamp or generate one
                    timestamp = datetime.datetime.utcnow().isoformat()
                    
                    # Extract Media (Images for now)
                    media_items = []
                    img_elems = await post.query_selector_all('img[src*="scontent"]')
                    for img in img_elems:
                        src = await img.get_attribute("src")
                        if src:
                            # Heuristic to ignore tiny profile pics/icons from scontent
                            if "/p40x40/" in src or "/p36x36/" in src or "/p100x100/" in src or "/emoji.php/" in src:
                                continue
                            
                            local_path = download_media(src, "facebook", "image")
                            if local_path:
                                media_items.append({
                                    "type": "image",
                                    "url": src,
                                    "local_path": local_path
                                })
                                
                    # Extract Video 
                    # If FB post has a video or interactive video player, feed URL to yt-dlp
                    has_video = await post.query_selector('video') or await post.query_selector('div[data-pagelet="MediaViewer"]')
                    if has_video and post_url:
                        video_local_path = download_video(post_url, "facebook", cookie_file_path)
                        if video_local_path:
                            media_items.append({
                                "type": "video",
                                "url": post_url,
                                "local_path": video_local_path
                            })

                    # unique signature based on author and content
                    unique_sig = f"{author}-{content[:20]}"

                    if unique_sig not in posts_seen and content != "[Media/No Text]":
                        posts_seen.add(unique_sig)
                        batch_data.append({
                            "author": author,
                            "content": content,
                            "timestamp": timestamp,
                            "url": post_url,
                            "media_items": media_items
                        })

                except Exception as e:
                    print(f"Error parsing post: {e}")
                    continue

            if batch_data:
                save_posts_to_db(batch_data)
                total_extracted += len(batch_data)
                print(f"Extracted {len(batch_data)} new posts... (Total: {total_extracted}/{POSTS_LIMIT if POSTS_LIMIT > 0 else 'Infinite'})")

            # Scroll down to load more
            await page.mouse.wheel(0, 1500)
            wait_time = random.uniform(2500, 5000)
            print(f"Scrolling... waiting {wait_time / 1000:.2f}s")
            await page.wait_for_timeout(wait_time)

        await context.close()
        print("Scraping finished.")

if __name__ == "__main__":
    asyncio.run(scrape_feed())
