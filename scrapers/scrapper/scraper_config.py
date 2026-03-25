"""
Scraper Configuration and Utilities
This module handles the integration between the X/Twitter scraper and the vigilis database.
The scraped data is stored directly in the 'posts' table without creating additional tables.
"""

# Source configuration for Twitter/X posts
TWITTER_SOURCE_CONFIG = {
    "platform": "Twitter/X",
    "source_name": "X Feed",
    "url": "https://x.com/home",
    "category": "twitter"
}

# Post table fields mapping from scraped data
POST_FIELD_MAPPING = {
    "author": "author",           # Twitter handle/username
    "content": "text_content",    # Tweet text
    "timestamp": "timestamp",     # Tweet timestamp
    "handle": "metadata",         # Store handle in existing fields if needed
}

print("""
╔════════════════════════════════════════════════════════════════╗
║         X/Twitter Scraper - Database Integration               ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║ Scraped data is stored in the 'posts' table:                  ║
║  - source_id: References the Twitter/X source                 ║
║  - author: Username/handle of the tweet author                ║
║  - text_content: Full tweet text                              ║
║  - timestamp: When the tweet was posted                       ║
║  - category: Set to 'twitter' for identification              ║
║  - flagged: Default false (can be updated by analysis)        ║
║  - confidence_score: Available for AI analysis results        ║
║                                                                ║
║ NOTE: No separate 'scraped_tweets' table is created          ║
║ The existing 'posts' table is used for all scraped content    ║
║                                                                ║
║ Login/Logout functionality: UNCHANGED                         ║
║ Scraping logic: Uses database.py module for DB operations     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")
