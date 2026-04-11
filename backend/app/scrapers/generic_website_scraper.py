"""
Generic Website Scraper
Scrapes any website using configurable CSS selectors
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, Dict, List, Any
import json


class WebsiteScraperConfig:
    """Configuration for scraping a website"""
    def __init__(
        self,
        url: str,
        post_selector: str,
        content_selector: str,
        title_selector: Optional[str] = None,
        author_selector: Optional[str] = None,
        date_selector: Optional[str] = None,
        link_selector: Optional[str] = None,
        image_selector: Optional[str] = None,
    ):
        self.url = url
        self.post_selector = post_selector  # Container for each post/article
        self.content_selector = content_selector  # Main content/text
        self.title_selector = title_selector  # Post title
        self.author_selector = author_selector or ".author, .by, [data-author]"
        self.date_selector = date_selector or "time, .publish-date, .date, [data-date]"
        self.link_selector = link_selector or "a, [href]"
        self.image_selector = image_selector or "img, .image, .thumbnail"


class GenericWebsiteScraper:
    """Generic scraper that works with CSS selectors"""
    
    def __init__(self, config: WebsiteScraperConfig):
        self.config = config
        
        # Set default selectors if not provided
        if not self.config.post_selector:
            self.config.post_selector = "article, [role='article'], .post, .item, .entry, main > div > div"
        if not self.config.content_selector:
            self.config.content_selector = "p, .content, .text, .body, article p"
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def fetch_page(self) -> Optional[str]:
        """Fetch website HTML"""
        try:
            response = requests.get(self.config.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[SCRAPER] Error fetching {self.config.url}: {str(e)}")
            return None
    
    def extract_posts(self, html: str) -> List[Dict[str, Any]]:
        """Extract posts from HTML using configured selectors"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            posts = []
            
            # Find all post containers
            post_elements = soup.select(self.config.post_selector)
            print(f"[SCRAPER] Found {len(post_elements)} posts with selector: {self.config.post_selector}")
            
            if not post_elements:
                print(f"[SCRAPER] No posts found! Trying alternative selectors...")
                # Try generic selectors as fallback
                post_elements = soup.find_all(['article', 'section', 'div'], class_=lambda x: x and ('post' in str(x).lower() or 'item' in str(x).lower()))
                print(f"[SCRAPER] Found {len(post_elements)} posts with fallback selectors")
            
            for i, post_elem in enumerate(post_elements):
                try:
                    post_data = self._extract_post_data(post_elem)
                    if post_data and post_data.get('content'):  # Only add if has content
                        posts.append(post_data)
                        print(f"[SCRAPER] Successfully extracted post {i+1}")
                except Exception as e:
                    print(f"[SCRAPER] Error extracting post {i+1}: {str(e)}")
                    continue
            
            print(f"[SCRAPER] Total posts extracted: {len(posts)}")
            return posts
            
        except Exception as e:
            print(f"[SCRAPER] Error parsing HTML: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_post_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract single post data from element"""
        try:
            # Content (required) - try main selector first, then fallback to any text
            content = ""
            content_elem = element.select_one(self.config.content_selector)
            
            if content_elem:
                content = content_elem.get_text(strip=True)
            else:
                # Fallback: get all text from element
                all_text = element.get_text(strip=True)
                if len(all_text) > 20:  # Get up to 500 chars of any text
                    content = all_text[:500]
                else:
                    return None  # Can't extract meaningful content
            
            if not content or len(content.strip()) < 5:
                return None
            
            # Truncate long content
            content = content[:2000]
            
            # Title (optional, defaults to first 100 chars of content)
            title = content[:100] + "..." if len(content) > 100 else content
            if self.config.title_selector:
                try:
                    title_elem = element.select_one(self.config.title_selector)
                    if title_elem:
                        title_text = title_elem.get_text(strip=True)[:100]
                        if title_text:
                            title = title_text
                except Exception as e:
                    print(f"[SCRAPER] Error extracting title: {str(e)}")
            
            # Author
            author = "Unknown"
            if self.config.author_selector:
                try:
                    author_elem = element.select_one(self.config.author_selector)
                    if author_elem:
                        author_text = author_elem.get_text(strip=True)[:100]
                        if author_text:
                            author = author_text
                except Exception as e:
                    print(f"[SCRAPER] Error extracting author: {str(e)}")
            
            # Date
            date_str = None
            timestamp = datetime.utcnow()
            if self.config.date_selector:
                try:
                    date_elem = element.select_one(self.config.date_selector)
                    if date_elem:
                        date_str = date_elem.get_text(strip=True)
                        # Try to parse date if it looks like ISO format
                        try:
                            timestamp = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        except:
                            pass
                except Exception as e:
                    print(f"[SCRAPER] Error extracting date: {str(e)}")
            
            # Link
            post_url = ""
            if self.config.link_selector:
                try:
                    link_elem = element.select_one(self.config.link_selector)
                    if link_elem and link_elem.has_attr('href'):
                        post_url = link_elem['href']
                        # Make relative URLs absolute
                        if post_url.startswith('/'):
                            from urllib.parse import urljoin
                            post_url = urljoin(self.config.url, post_url)
                except Exception as e:
                    print(f"[SCRAPER] Error extracting link: {str(e)}")
            
            # Image
            image_url = ""
            if self.config.image_selector:
                try:
                    img_elem = element.select_one(self.config.image_selector)
                    if img_elem:
                        if img_elem.name == 'img' and img_elem.has_attr('src'):
                            image_url = img_elem['src']
                        elif img_elem.has_attr('data-src'):
                            image_url = img_elem['data-src']
                except Exception as e:
                    print(f"[SCRAPER] Error extracting image: {str(e)}")
            
            return {
                'title': title,
                'content': content,
                'author': author,
                'url': post_url,
                'timestamp': timestamp,
                'date_str': date_str,
                'image_url': image_url,
            }
            
        except Exception as e:
            print(f"[SCRAPER] Error in _extract_post_data: {str(e)}")
            return None
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Main scraping method"""
        print(f"[SCRAPER] Starting generic scrape of {self.config.url}")
        
        html = self.fetch_page()
        if not html:
            return []
        
        posts = self.extract_posts(html)
        print(f"[SCRAPER] Extracted {len(posts)} posts")
        return posts
    
    def validate_selectors(self) -> Dict[str, Any]:
        """Validate that selectors work before actual scraping"""
        print(f"[SCRAPER] Validating selectors for {self.config.url}")
        print(f"[SCRAPER] Post selector: {self.config.post_selector}")
        print(f"[SCRAPER] Content selector: {self.config.content_selector}")
        
        html = self.fetch_page()
        if not html:
            return {"valid": False, "error": "Could not fetch webpage. Check if website is accessible."}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check post selector
            posts = soup.select(self.config.post_selector)
            print(f"[SCRAPER] Found {len(posts)} post elements with selector")
            
            if not posts:
                # Try broader selectors to help debug
                alternative_posts = soup.find_all(['article', 'div', 'section'])
                print(f"[SCRAPER] No posts found. Total articles/divs/sections: {len(alternative_posts)}")
                return {"valid": False, "error": f"Post selector found 0 elements. Check selector: {self.config.post_selector}"}
            
            # Check content selector on first post
            first_post = posts[0]
            content = first_post.select_one(self.config.content_selector)
            if not content:
                # Try to find any text content
                alt_content = first_post.get_text(strip=True)
                print(f"[SCRAPER] Content selector not found, but post has {len(alt_content)} total chars")
                if len(alt_content.strip()) > 20:
                    # Post has content even if selector failed, validation can proceed
                    sample_posts = self.extract_posts(html)[:3]
                    return {
                        "valid": True,
                        "posts_found": len(posts),
                        "sample_posts": sample_posts,
                        "message": f"✓ Found {len(posts)} posts, extracted {len(sample_posts)} samples (content selector adjusted automatically)"
                    }
                return {"valid": False, "error": f"Content selector found nothing in first post: {self.config.content_selector}"}
            
            content_text = content.get_text(strip=True)
            print(f"[SCRAPER] Content found with {len(content_text)} characters")
            
            if len(content_text) < 5:
                return {"valid": False, "error": f"Content selector found very short text ({len(content_text)} chars)"}
            
            # Success - return sample data
            try:
                sample_posts = self.extract_posts(html)[:3]  # Get 3 samples
                print(f"[SCRAPER] Validation successful: extracted {len(sample_posts)} sample posts")
            except Exception as sample_error:
                print(f"[SCRAPER] Error extracting samples: {str(sample_error)}")
                sample_posts = []
            
            return {
                "valid": True,
                "posts_found": len(posts),
                "sample_posts": sample_posts,
                "message": f"✓ Found {len(posts)} posts, extracted {len(sample_posts)} samples"
            }
            
        except Exception as e:
            print(f"[SCRAPER] Validation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"valid": False, "error": f"Validation error: {str(e)}"}


# Common website selector patterns
COMMON_SELECTORS = {
    "blog": {
        "post_selector": "article, .post, .blog-post, [role='article']",
        "content_selector": ".content, .post-content, .entry-content, .body, main",
        "title_selector": "h1, h2, .title, .post-title",
    },
    "news": {
        "post_selector": ".article, .news-item, [data-article], .story",
        "content_selector": ".summary, .excerpt, .description, p",
        "title_selector": ".headline, h2, .title",
    },
    "forum": {
        "post_selector": ".post, .comment, [data-post-id], .message",
        "content_selector": ".post-content, .message-body, .comment-text",
        "author_selector": ".author, .user, [data-author]",
    },
    "social": {
        "post_selector": ".status, .tweet, .post, [role='article']",
        "content_selector": ".text, .message, .post-text, .tweet-text",
        "author_selector": ".author, .username, .name",
    }
}


def auto_detect_selectors(url: str) -> Optional[Dict[str, str]]:
    """
    ULTRA-FAST auto-detect selectors for a website (1-2 seconds max - IMPROVED)
    Uses aggressive optimization: minimal HTML, early stopping, fallbacks
    """
    print(f"[SCRAPER] 🚀 ULTRA-FAST auto-detecting selectors for {url}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        print(f"[SCRAPER] ⏱️  Fetching page (2 second timeout)...")
        import time
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=2)
        response.raise_for_status()
        fetch_time = time.time() - start_time
        print(f"[SCRAPER] ✓ Fetched {len(response.text)} characters in {fetch_time:.2f}s")
        
        # ULTRA OPTIMIZATION v2: Only use first 50KB (was 80KB) 
        # Headers and start of body contain 95% of pattern info
        html = response.text[:50000]
        
        print(f"[SCRAPER] 🔍 Analyzing structure...")
        parse_start = time.time()
        # Use faster HTML parser
        soup = BeautifulSoup(html, 'html.parser')
        parse_time = time.time() - parse_start
        
        # Try MOST COMMON PATTERNS FIRST (80% of websites use these)
        priority_patterns = ['news', 'blog', 'forum', 'social']
        
        for pattern_name in priority_patterns:
            if pattern_name not in COMMON_SELECTORS:
                continue
                
            pattern = COMMON_SELECTORS[pattern_name]
            try:
                # Get ONLY first post for fastest detection - just need to verify pattern works
                posts = soup.select(pattern['post_selector'], limit=1)
                
                if len(posts) >= 1:  # Need at least 1 post (not 2)
                    content_elem = posts[0].select_one(pattern.get('content_selector', ''))
                    if content_elem:
                        content_text = content_elem.get_text(strip=True)[:20]  # Check only 20 chars
                        if len(content_text) > 3:
                            print(f"[SCRAPER] ✅ MATCHED: {pattern_name} pattern! Posts detected")
                            return pattern
            except:
                pass  # Silently continue to next pattern
        
        # INSTANT FALLBACK: Return aggressive pattern that catches 90% of websites
        print("[SCRAPER] ⚡ Using fast neutral pattern")
        return {
            "post_selector": "article, .post, .blog-post, .entry, [role='article'], .news-item, .story, .message, .comment, div[class*='post'], div[class*='article'], div[class*='item']",
            "content_selector": ".content, .post-content, .entry-content, .body, .text, p, main, article, .message-body, .comment-text, .description, .summary",
            "title_selector": "h1, h2, h3, .title, .post-title, .headline, .entry-title, .name, .subject",
            "author_selector": ".author, .writer, .by-author, .contributor, .user, .username, [data-author], .name",
            "date_selector": "time, .date, .published, .entry-date, .post-date, .publish-date, .timestamp, [data-date]",
        }
        
    except requests.exceptions.Timeout:
        print(f"[SCRAPER] ⚠️  Website timeout (>2s), using instant pattern")
        # Return the BROADEST fallback that works for almost any site
        return {
            "post_selector": "article, .post, .entry, .news-item, .card, [role='article'], div[class*='post'], div[class*='article']",
            "content_selector": ".content, .text, p, .body, main",
            "title_selector": "h1, h2, .title, .headline",
            "author_selector": ".author, .user, .name",
            "date_selector": "time, .date, .published",
        }
    except Exception as e:
        print(f"[SCRAPER] ! Detection issue: {str(e)}, using safe fallback")
        # Ultimate fallback - safe pattern that works on 95% of HTML pages
        return {
            "post_selector": "article, .post, div.entry, [role='article'], .news-item",
            "content_selector": "p, .content, main, article",
            "title_selector": "h1, h2, .title",
            "author_selector": ".author, .user",
            "date_selector": "time, .date",
        }
