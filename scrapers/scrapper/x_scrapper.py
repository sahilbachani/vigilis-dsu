import asyncio
import random
import datetime
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
import sys
from pathlib import Path

from database import get_db_session, get_or_create_source, save_post_to_db

# Add ai_pipeline to path for AI analysis
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import AI pipeline (may be None if not available) - lazy load to avoid issues
AI_PIPELINE_AVAILABLE = False
AIAnalysisPipeline = None

def load_ai_pipeline():
    """Lazy load AI pipeline only when needed"""
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
        print("   Posts will be saved without analysis")
        AI_PIPELINE_AVAILABLE = False
        return None

# --- CONFIGURATION ---
HEADLESS_MODE = False
USER_DATA_DIR = "./user_data"
TARGET_URL = "https://x.com/home"

# Twitter source configuration
TWITTER_PLATFORM = "Twitter/X"
TWITTER_SOURCE_NAME = "X Feed"
TWITTER_URL = "https://x.com/home"


def save_posts_to_db(tweets, ai_pipeline=None):
    """
    Save scraped tweets to the database with AI analysis
    
    Args:
        tweets: List of tweet dicts with keys: author, handle, content, timestamp
        ai_pipeline: Optional AIAnalysisPipeline instance for real-time analysis
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
        analyzed_count = 0
        flagged_count = 0
        
        for t in tweets:
            try:
                # Perform AI analysis if pipeline available
                if ai_pipeline:
                    try:
                        analysis_result = ai_pipeline.analyzer.analyze_text(t["content"])
                        analyzed_count += 1
                        
                        if analysis_result.flagged:
                            flagged_count += 1
                            print(f"\n🚩 FLAGGED POST by {t['author']}")
                            print(f"   Hate Score: {analysis_result.hate_score:.2f}")
                            print(f"   Extremism Score: {analysis_result.extremism_score:.2f}")
                            print(f"   Misinformation Score: {analysis_result.misinformation_score:.2f}")
                            print(f"   Confidence: {analysis_result.confidence_score:.2f}")
                        
                        # Save with analysis results
                        post_id = ai_pipeline.db_ops.save_analyzed_post(
                            db=db,
                            source_id=source_id,
                            author=t["author"],
                            text_content=t["content"],
                            timestamp=datetime.datetime.fromisoformat(t["timestamp"]),
                            analysis_result=analysis_result,
                            url=None,
                            category="twitter"
                        )
                        
                        if post_id:
                            saved_count += 1
                            
                    except Exception as ai_error:
                        print(f"⚠️ AI Analysis failed for {t['author']}: {ai_error}")
                        # Fall back to saving without analysis
                        post_id = save_post_to_db(
                            db,
                            source_id=source_id,
                            author=t["author"],
                            text_content=t["content"],
                            timestamp=t["timestamp"],
                            url=None,
                            confidence_score=None,
                            category="twitter"
                        )
                        if post_id:
                            saved_count += 1
                else:
                    # No AI pipeline - save without analysis
                    post_id = save_post_to_db(
                        db,
                        source_id=source_id,
                        author=t["author"],
                        text_content=t["content"],
                        timestamp=t["timestamp"],
                        url=None,
                        confidence_score=None,
                        category="twitter"
                    )
                    if post_id:
                        saved_count += 1
                    
            except Exception as e:
                print(f"Error saving post from {t['author']}: {e}")
                continue
        
        print(f"\n--- Processing Summary ---")
        print(f"Saved: {saved_count} posts")
        if ai_pipeline:
            print(f"Analyzed: {analyzed_count} posts")
            print(f"Flagged: {flagged_count} posts")
    
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        db.close()



async def scrape_feed():
    # Initialize AI Pipeline if available
    ai_pipeline = None
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
    
    lockfile_path = os.path.join(USER_DATA_DIR, "lockfile")
    if os.path.exists(lockfile_path):
        try:
            os.remove(lockfile_path)
            print("Removed stale lockfile.")
        except OSError:
            print("Could not remove lockfile.")

    async with async_playwright() as p:
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        print("Launching browser with persistent context...")
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=HEADLESS_MODE,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
            user_agent=user_agent,
            viewport=None
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

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

                    content_elem = await tweet.query_selector(
                        'div[data-testid="tweetText"]'
                    )
                    content = (
                        await content_elem.inner_text()
                        if content_elem else "[Media/No Text]"
                    )

                    unique_sig = f"{handle}-{timestamp}"

                    if unique_sig not in tweets_seen:
                        tweets_seen.add(unique_sig)
                        batch_data.append({
                            "author": author,
                            "handle": handle,
                            "content": content,
                            "timestamp": timestamp
                        })

                except:
                    continue

            if batch_data:
                # Pass AI pipeline to save_posts_to_db
                save_posts_to_db(batch_data, ai_pipeline)

            await page.mouse.wheel(0, 1000)
            wait_time = random.uniform(2000, 5000)
            print(f"Scrolling... waiting {wait_time / 1000:.2f}s")
            await page.wait_for_timeout(wait_time)

        await context.close()
        print("Scraping finished.")


if __name__ == "__main__":
    asyncio.run(scrape_feed())
