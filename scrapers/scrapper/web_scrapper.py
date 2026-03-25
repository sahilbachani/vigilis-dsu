"""
Website/Blog Scraper for Vigilis
Scrapes articles from configurable Pakistani news/blog sources.
Uses requests + BeautifulSoup (no browser required - public pages).

To add a new source: add a dict to BLOG_SOURCES with the CSS selectors
for that site's article listing and article detail pages.
"""

import requests
from bs4 import BeautifulSoup
import datetime
import re
import os
import sys
import argparse
import io
from dotenv import load_dotenv
from database import get_db_session, get_or_create_source, save_post_to_db

# Fix Windows console unicode printing errors
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()

# --- CONFIGURATION ---

# How many articles to scrape per source (set 0 for unlimited)
ARTICLES_LIMIT = 10

# Request timeout in seconds
REQUEST_TIMEOUT = 15

# Common headers to mimic a real browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

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
        "link_selector": "h2 a[href*='/news/'], h3 a[href*='/news/']",
        "link_attr": "href",
        "title_selector": "h2.story__title, h1.story__title",
        "content_selector": "div.story__content",
        "author_selector": "span.story__byline a, a.story__byline",
        "date_selector": "span.timestamp--date, span.story__time",
    },
    {
        "id": "toi",
        "name": "Times of India",
        "base_url": "https://timesofindia.indiatimes.com",
        "listing_url": "https://timesofindia.indiatimes.com/",
        "link_selector": "a[href*='/articleshow/'], a[href*='/news/'], figcaption a",
        "link_attr": "href",
        "title_selector": "h1, .Hwnh1",
        "content_selector": "div._s30J, div.article_content, div[data-articlebody]",
        "author_selector": "div.xf8Ll a, div.byline a",
        "date_selector": "div.xf8Ll span, time",
    },
    {
        "id": "jihadintel",
        "name": "Jihad Intel",
        "base_url": "https://jihadintel.meforum.org",
        "listing_url": "https://jihadintel.meforum.org/blog/archive/",
        "link_selector": "a[href*='/jihadintel.meforum.org/'], a[href*='/blog/'], .post-title a",
        "link_attr": "href",
        "title_selector": "h1",
        "content_selector": "div.article-text, div.content, article, div.entry-content",
        "author_selector": "span.author, a.author",
        "date_selector": "span.date, time",
    },
    {
        "id": "khorasandiary",
        "name": "The Khorasan Diary",
        "base_url": "https://thekhorasandiary.com",
        "listing_url": "https://thekhorasandiary.com/",
        "link_selector": "a[href*='thekhorasandiary.com/'], .post-title a, h2 a, h3 a",
        "link_attr": "href",
        "title_selector": "h1",
        "content_selector": "div.post-content, article, div.entry-content",
        "author_selector": "span.author a, a.author",
        "date_selector": "time, span.date",
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


def url_already_scraped(db, url: str) -> bool:
    """Check if a URL already exists in the posts table."""
    from sqlalchemy import text
    result = db.execute(
        text("SELECT 1 FROM posts WHERE url = :url LIMIT 1"),
        {"url": url}
    ).fetchone()
    return result is not None


def fetch_page(url: str) -> BeautifulSoup | None:
    """Fetch a page and return BeautifulSoup object, or None on failure."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None


def extract_article_links(soup: BeautifulSoup, source: dict) -> list[str]:
    """Extract unique article links from a listing page."""
    links = []
    seen = set()
    elements = soup.select(source["link_selector"])

    for el in elements:
        href = el.get(source["link_attr"], "")
        full_url = get_full_url(href, source["base_url"])

        if not full_url or full_url in seen:
            continue

        # Basic validation: skip non-article pages
        if any(skip in full_url for skip in ["/video", "/tag/", "/category/", "#", "youtube.com", "javascript:", "/carbase", "/lens", "/perspective"]):
            continue

        # Must look like an article URL (has a path segment beyond just the domain)
        from urllib.parse import urlparse
        path = urlparse(full_url).path.rstrip("/")
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


def scrape_source(source: dict):
    """Scrape articles from a single source and save to database."""
    print(f"\n{'='*60}")
    print(f"  Scraping: {source['name']}")
    print(f"  URL: {source['listing_url']}")
    print(f"{'='*60}")

    # Fetch the listing page
    listing_soup = fetch_page(source["listing_url"])
    if not listing_soup:
        print(f"  [SKIP] Could not fetch listing page for {source['name']}")
        return

    # Extract article links
    article_links = extract_article_links(listing_soup, source)
    print(f"  Found {len(article_links)} article links")

    if not article_links:
        print(f"  [SKIP] No articles found for {source['name']}")
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

            # Skip if already scraped
            try:
                if url_already_scraped(db, article_url):
                    print(f"    [SKIP] Already in database")
                    skipped_count += 1
                    continue
            except Exception:
                # Rollback if the duplicate check transaction failed
                db.rollback()

            # Fetch article page
            article_soup = fetch_page(article_url)
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

    except Exception as e:
        print(f"  [ERROR] Database error for {source['name']}: {e}")
        db.rollback()
    finally:
        db.close()


def scrape_all(target_source_id=None):
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
    print("=" * 60)

    for source in sources_to_scrape:
        try:
            scrape_source(source)
        except Exception as e:
            print(f"\n  [ERROR] Failed to scrape {source['name']}: {e}")
            continue

    print("\n" + "=" * 60)
    print("  Scraping complete!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Vigilis Website/Blog Scraper")
    parser.add_argument("--source", type=str, help="Specify a source ID to scrape (e.g., 'dawn', 'toi', 'jihadintel')", default=None)
    args = parser.parse_args()

    scrape_all(args.source)
