"""
Website/Blog Scraper for Vigilis
Scrapes articles from configurable Pakistani news/blog sources.
Uses requests + BeautifulSoup (no browser required - public pages).

To add a new source: add a dict to BLOG_SOURCES with the CSS selectors
for that site's article listing and article detail pages.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import datetime
import re
import os
import sys
import argparse
import io
from dotenv import load_dotenv
from database import get_db_session, get_or_create_source, save_post_to_db

# Try to import curl-cffi for Cloudflare bypass
try:
    from curl_cffi.requests import Session as CurlSession
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CurlSession = None
    CURL_CFFI_AVAILABLE = False

# Try to import Playwright for browser-based scraping
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False

# Try to import Selenium for Chrome with VPN support
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    webdriver = None
    SELENIUM_AVAILABLE = False

# Fix Windows console unicode printing errors
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()

# --- CONFIGURATION ---

# How many articles to scrape per source (set 0 for unlimited)
ARTICLES_LIMIT = 10

# Request timeout in seconds
REQUEST_TIMEOUT = 20

# Better headers with Cloudflare bypass
HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,ur;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

# Website source configuration
WEB_PLATFORM = "Website"

# ============================================================================
# BLOG SOURCES - Add/remove/edit sources here
# Each source needs:
#   name           - Human-readable name (stored as source_name in DB)
#   base_url       - Root domain (used to resolve relative links)
#   listing_url    - Page with article links to scrape
#   link_selector  - CSS selector to find article <a> tags on the listing page
#   link_attr      - Attribute on the <a> tag that holds the URL (usually "href")
#   title_selector - CSS selector for the article title on the detail page
#   content_selector - CSS selector for the article body text
#   author_selector  - CSS selector for the author name
#   date_selector    - CSS selector for the publish date
# ============================================================================

BLOG_SOURCES = [
    {
        "id": "dawn",
        "name": "Dawn News",
        "base_url": "https://www.dawn.com",
        "listing_url": "https://www.dawn.com",
        "link_selector": "h2 a, h3 a, a[data-story-id], div.story-item a",
        "link_attr": "href",
        "title_selector": "h2.story__title, h1, h1.story__title, h2, h3",
        "content_selector": "div.story__content, div.story-content, article, div.post-content",
        "author_selector": "span.story__byline a, a.story__byline, span.writer-name",
        "date_selector": "span.timestamp--date, span.story__time, time, span.date",
        "note": "Pakistani news source - updated to active",
        "status": "active",
    },
    {
        "id": "bellingcat",
        "name": "Bellingcat",
        "base_url": "https://www.bellingcat.com",
        "listing_url": "https://www.bellingcat.com/",
        "link_selector": "a.article-link, a.post-link, h2 a, h3 a, article a, a[href*='/articles/'], a[href*='/news/']",
        "link_attr": "href",
        "title_selector": "h1, h1.entry-title, h2.article-title, h2",
        "content_selector": "div.entry-content, div.post-content, article, div.article-body, div.content",
        "author_selector": "span.author, .author-name, a.author, div.byline a",
        "date_selector": "time, span.date, span.published-date, div.meta time",
        "note": "Investigative journalism source - international news",
        "status": "active",
    },
    {
        "id": "jihadintel",
        "name": "Jihad Intel",
        "base_url": "https://jihadintel.meforum.org",
        "listing_url": "https://jihadintel.meforum.org/blog/archive/",
        "link_selector": "tr a",  # Site uses HTML tables for layout
        "link_attr": "href",
        "title_selector": "h1",
        "content_selector": "div.article-text, div.content, article, div.entry-content, div.post-content",
        "author_selector": "span.author, a.author",
        "date_selector": "span.date, time",
        "status": "active",
    },
    {
        "id": "khorasandiary",
        "name": "The Khorasan Diary",
        "base_url": "https://thekhorasandiary.com",
        "listing_url": "https://thekhorasandiary.com/",
        "link_selector": "main a",
        "link_attr": "href",
        "title_selector": "h1",
        "content_selector": "div.post-content, article, div.entry-content, div.content",
        "author_selector": "span.author a, a.author, div.author",
        "date_selector": "time, span.date, span.post-date",
        "status": "active",
    },
]


def get_full_url(href: str, base_url: str) -> str:
    """Resolve a potentially relative URL to an absolute URL."""
    if not href:
        return ""
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return base_url.rstrip("/") + "/" + href


def _fetch_with_curl_cffi(url: str) -> BeautifulSoup | None:
    """
    Fallback function to fetch a page using curl-cffi to bypass Cloudflare bot protection.
    This function uses curl-cffi's synchronous API to avoid asyncio complications.
    """
    import random
    
    if not CURL_CFFI_AVAILABLE:
        return None
    
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ur;q=0.8",
        }
        
        with CurlSession() as sess:
            response = sess.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                impersonate="chrome"  # Impersonate Chrome browser
            )
            
            if response.status_code == 200 and len(response.text) > 1000:
                print(f"  [SUCCESS] Fetched with curl-cffi (Cloudflare bypass)")
                return BeautifulSoup(response.text, "html.parser")
            else:
                print(f"  [CURL-CFFI] Got status {response.status_code} or empty content")
                return None
                
    except Exception as e:
        print(f"  [CURL-CFFI ERROR] {str(e)[:100]}")
        return None


def _fetch_with_selenium_chrome(url: str, wait_selector: str | None = None) -> BeautifulSoup | None:
    """Fetch a page using Selenium Chrome browser (uses system Chrome with installed extensions like VPN)."""
    if not SELENIUM_AVAILABLE:
        print("  [SELENIUM] Not installed. Install with: pip install selenium webdriver-manager")
        return None

    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")  # Headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={USER_AGENTS[0]}")
        # Use system Chrome profile so VPN extensions are loaded
        options.add_argument("--user-data-dir=C:\\Users\\" + os.getenv('USERNAME', 'User') + "\\AppData\\Local\\Google\\Chrome\\User Data")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print(f"  [SELENIUM] Fetching with Chrome (VPN through extension)...")
        driver.get(url)
        
        # Wait for content to load
        if wait_selector:
            try:
                WebDriverWait(driver, REQUEST_TIMEOUT).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, wait_selector))
                )
            except:
                pass  # Continue even if selector not found
        else:
            import time
            time.sleep(3)  # Wait 3 seconds for page load
        
        html = driver.page_source
        driver.quit()
        
        if html and len(html) > 1000:
            print(f"  [SUCCESS] Fetched with Selenium Chrome")
            return BeautifulSoup(html, "html.parser")
        return None
        
    except Exception as e:
        print(f"  [SELENIUM ERROR] {str(e)[:100]}")
        try:
            driver.quit()
        except:
            pass
        return None


def _fetch_with_playwright(url: str, wait_selector: str | None = None) -> BeautifulSoup | None:
    """Fetch a page using a real browser to bypass JS/anti-bot blocks."""
    if not PLAYWRIGHT_AVAILABLE:
        print("  [PLAYWRIGHT] Not installed. Install with: pip install playwright")
        return None

    try:
        import asyncio
        import concurrent.futures

        # Use system network (will route through VPN if active)
        # Only use explicit proxy if SCRAPER_HTTP_PROXY is set AND valid
        proxy = os.getenv("SCRAPER_HTTP_PROXY")  # Only this one, not HTTPS_PROXY/HTTP_PROXY
        proxy_config = {"server": proxy} if proxy else None

        async def _async_fetch() -> str:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, proxy=proxy_config)
                context = await browser.new_context(user_agent=USER_AGENTS[0])
                page = await context.new_page()
                await page.goto(url, timeout=REQUEST_TIMEOUT * 1000, wait_until="domcontentloaded")
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=REQUEST_TIMEOUT * 1000)
                html_content = await page.content()
                await browser.close()
                return html_content

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _async_fetch())
                html = future.result(timeout=REQUEST_TIMEOUT + 10)
        else:
            html = asyncio.run(_async_fetch())

        if html and len(html) > 1000:
            print("  [SUCCESS] Fetched with Playwright (browser mode)")
            return BeautifulSoup(html, "html.parser")
        return None
    except Exception as e:
        print(f"  [PLAYWRIGHT ERROR] {str(e)[:100]}")
        return None


def url_already_scraped(db, url: str) -> bool:
    """Check if a URL already exists in the posts table."""
    from sqlalchemy import text
    result = db.execute(
        text("SELECT 1 FROM posts WHERE url = :url LIMIT 1"),
        {"url": url}
    ).fetchone()
    return result is not None


def fetch_page(
    url: str,
    session: requests.Session = None,
    source: dict | None = None,
    wait_selector: str | None = None
) -> BeautifulSoup | None:
    """
    Fetch a page and return BeautifulSoup object using persistent session with retry strategy.
    
    For sites with strong Cloudflare bot protection (403 Forbidden):
    - This function uses HTTPAdapter with exponential backoff for initial tries
    - Standard browser-like headers are included
    - If requests fails, automatically falls back to curl-cffi for Cloudflare bypass
    
    For DNS resolution failures:
    - Ensure your internet connection and DNS are working
    - Try setting custom DNS in your network settings (e.g., 8.8.8.8, 8.8.4.4)
    """
    import time
    import random

    proxy = os.getenv("SCRAPER_HTTP_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    proxies = {"http": proxy, "https": proxy} if proxy else None

    if source and source.get("use_browser"):
        # Try Selenium Chrome first (for sources with VPN extensions)
        if source.get("use_selenium_chrome"):
            browser_soup = _fetch_with_selenium_chrome(url, wait_selector=wait_selector)
            if browser_soup:
                return browser_soup
        # Fallback to Playwright
        browser_soup = _fetch_with_playwright(url, wait_selector=wait_selector)
        if browser_soup:
            return browser_soup
    
    try:
        # Use simple headers first - don't use session/retry for listing pages
        # Some sites detect the retry strategy and return truncated content
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # First try with simple request (faster, works for most sites)
        response = requests.get(
            url, 
            headers=headers, 
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            verify=True,
            proxies=proxies
        )
        
        # Check if we got meaningful content
        if response.status_code == 200 and len(response.text) > 5000:
            return BeautifulSoup(response.text, "html.parser")
        
        # If not, fall back to session-based request with retry strategy
        if session is None:
            session = requests.Session()
            retry_strategy = Retry(
                total=4,
                status_forcelist=[403, 429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],
                backoff_factor=2,
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
        
        # Add extra Cloudflare bypass headers for retry attempt
        headers.update({
            "Pragma": "no-cache",
            "DNT": "1",
            "Connection": "keep-alive",
            "Keep-Alive": "timeout=5, max=100",
            "Sec-Ch-Ua": '\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
        })
        
        response = session.get(
            url, 
            headers=headers, 
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            verify=True,
            proxies=proxies
        )
        
        # Handle different HTTP status codes
        if response.status_code == 403:
            print(f"  [BLOCKED] Site returned 403 Forbidden - trying curl-cffi bypass...")
            if CURL_CFFI_AVAILABLE:
                return _fetch_with_curl_cffi(url)
            else:
                print(f"     To enable Cloudflare bypass: pip install curl-cffi")
                if source and source.get("use_browser"):
                    return _fetch_with_playwright(url, wait_selector=wait_selector)
                return None
        elif response.status_code == 429:
            print(f"  [RATELIMIT] Site rate limiting us - retry logic active")
            return None
        elif response.status_code >= 500:
            print(f"  [SERVER ERROR] {response.status_code} - Retrying...")
            return None
        
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
        
    except requests.exceptions.ConnectionError as e:
        error_msg = str(e)
        
        # Try again with SSL verification disabled as fallback
        if "certificate" in error_msg.lower() or "ssl" in error_msg.lower():
            print(f"  [SSL ERROR] Certificate verification failed - trying without SSL verification...")
            try:
                response = session.get(
                    url, 
                    headers=headers, 
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                    verify=False,  # Disable SSL verification for problematic sites
                    proxies=proxies
                )
                response.raise_for_status()
                return BeautifulSoup(response.text, "html.parser")
            except Exception as retry_error:
                print(f"  [SSL RETRY FAILED] Trying curl-cffi fallback...")
                if CURL_CFFI_AVAILABLE:
                    return _fetch_with_curl_cffi(url)
                else:
                    print(f"     To enable: pip install curl-cffi")
                    if source and source.get("use_browser"):
                        return _fetch_with_playwright(url, wait_selector=wait_selector)
                    return None
        elif "Name or service not known" in error_msg or "getaddrinfo failed" in error_msg:
            print(f"  [DNS ERROR] DNS resolution failed")
            print(f"     Domain: {url.split('/')[2]}")
            print(f"     Tip 1: Check your internet connection")
            print(f"     Tip 2: Try different DNS (8.8.8.8)")
            print(f"     Tip 3: This domain may be geo-blocked for your region")
            if source and source.get("use_browser"):
                print(f"     Tip 4: Set SCRAPER_HTTP_PROXY to an Indian proxy or use a VPN")
        else:
            print(f"  [NETWORK] Connection error: {error_msg[:80]}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"  [TIMEOUT] Request timeout - trying curl-cffi fallback...")
        if CURL_CFFI_AVAILABLE:
            return _fetch_with_curl_cffi(url)
        else:
            print(f"     To enable: pip install curl-cffi")
            if source and source.get("use_browser"):
                return _fetch_with_playwright(url, wait_selector=wait_selector)
            return None
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Failed to fetch - trying curl-cffi fallback...")
        if CURL_CFFI_AVAILABLE:
            return _fetch_with_curl_cffi(url)
        else:
            print(f"     To enable: pip install curl-cffi")
            if source and source.get("use_browser"):
                return _fetch_with_playwright(url, wait_selector=wait_selector)
            return None
    except Exception as e:
        print(f"  [UNEXPECTED] {type(e).__name__}: {str(e)[:80]}")


def extract_article_links(soup: BeautifulSoup, source: dict) -> list[str]:
    """Extract unique article links from a listing page."""
    links = []
    seen = set()
    elements = soup.select(source["link_selector"])
    
    # Source-specific filtering patterns
    skip_keywords = ["/video", "/tag/", "/category/", "#", "youtube.com", "javascript:", "/carbase", "/lens", "/perspective"]
    
    # Khorasan Diary: article links contain /en/ or /ur/ in path
    if source.get("id") == "khorasandiary":
        skip_keywords.append("")  # Will handle below with specific check
    
    # Jihad Intel: article links should contain specific paths
    if source.get("id") == "jihadintel":
        skip_keywords.append("")  # Will handle below with specific check

    for el in elements:
        href = el.get(source["link_attr"], "")
        full_url = get_full_url(href, source["base_url"])

        if not full_url or full_url in seen:
            continue
        
        # Skip non-article pages
        if any(skip in full_url for skip in skip_keywords if skip):
            continue

        # Must look like an article URL (has a path segment beyond just the domain)
        from urllib.parse import urlparse
        path = urlparse(full_url).path.rstrip("/")
        
        # Source-specific filtering
        if source.get("id") == "khorasandiary":
            # Khorasan articles have format: /en/YYYY/MM/DD/title or /ur/YYYY/MM/DD/title
            if not any(x in path.lower() for x in ["/en/", "/ur/"]):
                continue
            # Should have year, month, day in path
            import re
            date_pattern = r'/(en|ur)/\d{4}/\d{2}/\d{2}/'
            if not re.search(date_pattern, path.lower()):
                continue
                
        elif source.get("id") == "jihadintel":
            # Jihad Intel articles use /blog/ path
            # Skip navigation links and admin pages
            if any(x in path for x in ["/list_subscribe", "/about", "/contact", "/identifiers", "/donate", "/search"]):
                continue
            # Article links should have more depth
            if path.count("/") < 2:
                continue
        
        else:
            # Generic filtering: path must have depth
            if not path or path.count("/") < 2:
                continue

        seen.add(full_url)
        links.append(full_url)

        if ARTICLES_LIMIT > 0 and len(links) >= ARTICLES_LIMIT:
            break

    return links


def extract_text(soup: BeautifulSoup, selector: str) -> str:
    """Extract text from the first element matching a CSS selector."""
    el = soup.select_one(selector)
    if el:
        return el.get_text(strip=True)
    return ""


def extract_content(soup: BeautifulSoup, selector: str) -> str:
    """Extract full article text from content div, joining all paragraphs."""
    el = soup.select_one(selector)
    if el:
        # Get text from all <p> tags for cleaner output
        paragraphs = el.find_all("p")
        if paragraphs:
            text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            if len(text) > 50:
                return text

        # Fallback: get all text from the container
        text = el.get_text(separator="\n", strip=True)
        if len(text) > 50:
            return text

    # Fallback: find the largest text-dense container on the page
    # This works for sites like Tribune where content isn't inside an obvious wrapper
    best_text = ""
    for container in soup.find_all(["div", "article", "section"]):
        paragraphs = container.find_all("p", recursive=True)
        if len(paragraphs) >= 3:  # At least 3 paragraphs = likely article body
            text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            if len(text) > len(best_text):
                best_text = text

    return best_text


def parse_timestamp(raw_date: str) -> str:
    """
    Parse various date formats into ISO 8601 string.
    Handles messy date strings from news sites.
    Falls back to current UTC time if parsing fails.
    """
    if not raw_date:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    # If it already looks like an ISO timestamp, return it
    if re.match(r'^\d{4}-\d{2}-\d{2}', raw_date):
        return raw_date

    # Try to extract a date pattern from messy strings like "PublishedMarch 12, 2026Updated..."
    # Look for patterns like "March 12, 2026" or "Mar 12, 2026"
    date_patterns = [
        (r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})', '%B %d, %Y'),
        (r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s+\d{4})', '%B %d %Y'),
        (r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})', '%b %d, %Y'),
        (r'(\d{1,2}/\d{1,2}/\d{4})', '%m/%d/%Y'),
        (r'(\d{4}/\d{1,2}/\d{1,2})', '%Y/%m/%d'),
        (r'Updated\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})', '%b %d, %Y'),
    ]

    for pattern, fmt in date_patterns:
        match = re.search(pattern, raw_date)
        if match:
            try:
                date_str = match.group(1).replace(",", ", ").replace("  ", " ").strip()
                # Clean up commas
                date_str = re.sub(r',\s*,', ',', date_str)
                date_str = date_str.replace(", ", " ").replace(",", " ").strip()
                # Normalize whitespace
                date_str = " ".join(date_str.split())

                # Try direct parsing with multiple variations
                for try_fmt in [fmt, fmt.replace(",", ""), '%B %d %Y', '%b %d %Y']:
                    try:
                        dt = datetime.datetime.strptime(date_str, try_fmt)
                        return dt.isoformat()
                    except ValueError:
                        continue
            except Exception:
                continue

    # Fallback to current time
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def extract_date(soup: BeautifulSoup, selector: str) -> str:
    """Extract date from a page, with fallback to current UTC time."""
    # Try the time element's datetime attribute first (most reliable)
    time_el = soup.select_one("time[datetime]")
    if time_el:
        dt_attr = time_el.get("datetime", "")
        if dt_attr:
            return parse_timestamp(dt_attr)

    # Try the configured selector's datetime attribute
    date_el = soup.select_one(selector)
    if date_el:
        dt_attr = date_el.get("datetime", "")
        if dt_attr:
            return parse_timestamp(dt_attr)

    # Try to extract date from meta tags (og:article:published_time)
    meta_date = soup.select_one('meta[property="article:published_time"]')
    if meta_date:
        content = meta_date.get("content", "")
        if content:
            return parse_timestamp(content)

    # Try text content of the selector as last resort
    date_text = extract_text(soup, selector)
    if date_text:
        return parse_timestamp(date_text)

    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def scrape_source(source: dict, force_rescrape: bool = False):
    """Scrape articles from a single source and save to database."""
    print(f"\n{'='*60}")
    print(f"  Scraping: {source['name']}")
    print(f"  URL: {source['listing_url']}")
    if force_rescrape:
        print(f"  Mode: FORCE RE-SCRAPE (ignoring duplicate check)")
    print(f"{'='*60}")

    # Check source status
    status = source.get('status', 'active')
    if status == 'blocked':
        print(f"  [SKIP] This source is BLOCKED by bot protection (403 Forbidden)")
        print(f"         Requires: pip install curl-cffi")
        print(f"         Then: Reconfigure scraper to use curl-cffi instead of requests")
        return
    elif status == 'geo_blocked':
        print(f"  [SKIP] This source is GEO-BLOCKED from your region")
        print(f"         To access: Use a VPN with an IP from the source's country")
        return
    elif status != 'active':
        print(f"  [SKIP] Source status: {status}")
        return

    # Create persistent session with retry strategy for all requests to this source
    session = requests.Session()
    retry_strategy = Retry(
        total=4,
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=2,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Fetch the listing page
    listing_soup = fetch_page(
        source["listing_url"],
        session=session,
        source=source,
        wait_selector=source.get("listing_wait_selector")
    )
    if not listing_soup:
        print(f"  [SKIP] Could not fetch listing page for {source['name']}")
        session.close()
        return

    # Extract article links
    article_links = extract_article_links(listing_soup, source)
    print(f"  Found {len(article_links)} article links")

    if not article_links:
        print(f"  [SKIP] No articles found for {source['name']}")
        session.close()
        return

    # Open DB session
    db = get_db_session()
    try:
        # Get or create source entry
        source_id = get_or_create_source(
            db,
            WEB_PLATFORM,
            source["name"],
            source["base_url"]
        )

        saved_count = 0
        skipped_count = 0

        for i, article_url in enumerate(article_links):
            print(f"\n  [{i+1}/{len(article_links)}] {article_url}")

            # Skip if already scraped (unless force_rescrape is enabled)
            try:
                if not force_rescrape and url_already_scraped(db, article_url):
                    print(f"    [SKIP] Already in database")
                    skipped_count += 1
                    continue
            except Exception:
                # Rollback if the duplicate check transaction failed
                db.rollback()

            # Fetch article page using persistent session
            article_soup = fetch_page(
                article_url,
                session=session,
                source=source,
                wait_selector=source.get("article_wait_selector")
            )
            if not article_soup:
                continue

            # Extract data
            title = extract_text(article_soup, source["title_selector"])
            content = extract_content(article_soup, source["content_selector"])
            author = extract_text(article_soup, source["author_selector"]) or source["name"]
            date = extract_date(article_soup, source["date_selector"])

            if not title and not content:
                print(f"    [SKIP] No title or content found")
                continue

            # Use title as author label if author is missing
            display_author = author if author else source["name"]

            print(f"    Title: {title[:80]}...")
            print(f"    Author: {display_author}")
            print(f"    Content length: {len(content)} chars")

            try:
                post_id = save_post_to_db(
                    db,
                    source_id=source_id,
                    author=display_author,
                    text_content=f"**{title}**\n\n{content}" if title else content,
                    timestamp=date or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    url=article_url,
                    confidence_score=None,
                    category="website"
                )
                if post_id:
                    saved_count += 1
                    print(f"    [SAVED] post_id={post_id}")
            except Exception as e:
                print(f"    [ERROR] Failed to save: {e}")
                # Rollback so the session stays usable for the next article
                db.rollback()
                continue

        print(f"\n  Summary for {source['name']}:")
        print(f"    Saved: {saved_count} | Skipped (duplicate): {skipped_count} | Total links: {len(article_links)}")

    except ConnectionError as e:
        print(f"  [DB ERROR] Database connection failed for {source['name']}")
        print(f"    Ensure PostgreSQL is running and credentials in .env are correct")
        print(f"    Error: {str(e)[:100]}")
        db.rollback()
    except Exception as e:
        error_type = type(e).__name__
        print(f"  [ERROR] {error_type} for {source['name']}: {str(e)[:100]}")
        db.rollback()
    finally:
        db.close()
        session.close()


def scrape_all(target_source_id=None, force_rescrape=False):
    """Scrape all configured blog sources, or a specific one if target_source_id is provided."""
    print("\n" + "=" * 60)
    print("  VIGILIS - Website/Blog Scraper")
    
    sources_to_scrape = BLOG_SOURCES
    if target_source_id:
        sources_to_scrape = [s for s in BLOG_SOURCES if s.get("id") == target_source_id]
        if not sources_to_scrape:
            print(f"  [ERROR] Source ID '{target_source_id}' not found in configuration.")
            return

    print(f"  Sources: {len(sources_to_scrape)}")
    print(f"  Articles per source: {ARTICLES_LIMIT if ARTICLES_LIMIT > 0 else 'Unlimited'}")
    if force_rescrape:
        print(f"  Mode: FORCE RE-SCRAPE (ignoring duplicates)")
    print("=" * 60)

    for source in sources_to_scrape:
        try:
            scrape_source(source, force_rescrape=force_rescrape)
        except Exception as e:
            print(f"\n  [ERROR] Failed to scrape {source['name']}: {e}")
            continue

    print("\n" + "=" * 60)
    print("  Scraping complete!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Vigilis Website/Blog Scraper")
    parser.add_argument("--source", type=str, help="Specify a source ID to scrape (e.g., 'dawn', 'bellingcat', 'jihadintel', 'khorasandiary')", default=None)
    parser.add_argument("--force-rescrape", action="store_true", help="Force re-scraping by ignoring duplicate check (CAREFUL: may create duplicates)")
    args = parser.parse_args()

    scrape_all(args.source, force_rescrape=args.force_rescrape)
