# Integration Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VIGILIS PLATFORM                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────┐              ┌──────────────────────┐   │
│  │   FRONTEND (React)   │              │   BACKEND (FastAPI)  │   │
│  │                      │              │                      │   │
│  │  - Dashboard         │              │  - API Routes        │   │
│  │  - FlaggedPosts      │              │  - Auth (JWT)        │   │
│  │  - FlaggedVideos     │              │  - Post Management   │   │
│  │  - Settings          │──────HTTP────┤  - Video Management  │   │
│  │                      │              │  - SQLAlchemy ORM    │   │
│  └──────────────────────┘              └──────┬───────────────┘   │
│                                               │                    │
│                                               │ (DB Connection)    │
│                                               │                    │
│                         ┌─────────────────────▼────────────┐       │
│                         │   PostgreSQL Database            │       │
│                         │  (vigilis_db)                    │       │
│                         │                                  │       │
│                         │  Tables:                         │       │
│                         │  - users                         │       │
│                         │  - sources                       │       │
│                         │  - posts ◄──── SCRAPER WRITES   │       │
│                         │  - videos                        │       │
│                         │  - tags_keywords                 │       │
│                         └──────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    X/TWITTER SCRAPER MODULE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  x_scrapper.py                                               │ │
│  │  ├─ Playwright + Stealth (Browser Automation)               │ │
│  │  ├─ X.com Navigation & Auth (Manual Login)                  │ │
│  │  ├─ Tweet Extraction (author, content, timestamp)           │ │
│  │  └─ Batch Collection & save_posts_to_db()                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                          │                         │
│                                          │ (Import)                │
│                                          ▼                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  database.py  ◄─── NEW MODULE (SQLAlchemy)                 │ │
│  │                                                               │ │
│  │  Functions:                                                  │ │
│  │  ├─ get_db_session() → SessionLocal                         │ │
│  │  ├─ get_or_create_source(db, platform, name, url)          │ │
│  │  ├─ save_post_to_db(db, source_id, author, content...)     │ │
│  │  └─ add_tags_to_post(db, post_id, source_id, tags)         │ │
│  │                                                               │ │
│  │  Database URL:                                               │ │
│  │  postgresql://postgres:****@localhost:5432/vigilis_db       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                          │                         │
│                                          │ (DB Connection)        │
│                                          ▼                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  scraper_config.py  ◄─── Configuration & Constants          │ │
│  │  - TWITTER_PLATFORM = "Twitter/X"                           │ │
│  │  - TWITTER_SOURCE_NAME = "X Feed"                           │ │
│  │  - Field mapping documentation                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
X.com Feed
   │
   ▼
┌─────────────────────────┐
│   Browser Automation    │
│  (Playwright + Stealth) │
└────────────┬────────────┘
             │
             ▼
   ┌──────────────────┐
   │  Tweet Elements  │
   │                  │
   │ <article ...>    │
   │  - author        │
   │  - content       │
   │  - timestamp     │
   │  - handle        │
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────────────┐
   │  Extract Tweet Data     │
   │                         │
   │  {                      │
   │    "author": "...",     │
   │    "content": "...",    │
   │    "timestamp": "...",  │
   │    "handle": "@..."     │
   │  }                      │
   └────────┬────────────────┘
            │
            ▼
   ┌──────────────────────────────┐
   │  Batch Collection            │
   │  (Per scroll iteration)       │
   │                              │
   │  [tweet1, tweet2, tweet3...] │
   └────────┬─────────────────────┘
            │
            ▼
   ┌────────────────────────────────────┐
   │  save_posts_to_db(tweets)          │
   │                                    │
   │  For each tweet:                   │
   │  ├─ get_or_create_source()         │
   │  │  └─ source_id (Twitter/X)       │
   │  │                                 │
   │  └─ save_post_to_db(               │
   │     source_id, author, content...) │
   │     └─ post_id (auto)              │
   └────────┬─────────────────────────┘
            │
            ▼
   ┌──────────────────────┐
   │  SQLAlchemy Session  │
   │  (database.py)       │
   │                      │
   │  INSERT INTO posts   │
   │  INSERT INTO sources │
   │  (if new source)     │
   └────────┬─────────────┘
            │
            ▼
   ┌──────────────────────────────────┐
   │  PostgreSQL Connection           │
   │  vigilis_db                      │
   │                                  │
   │  DB Commits:                     │
   │  ├─ Post inserted (posts table)  │
   │  └─ Source confirmed (sources)   │
   └────────┬─────────────────────────┘
            │
            ▼
   ┌──────────────────────────────────┐
   │  Database Storage                │
   │                                  │
   │  posts table:                    │
   │  ┌────────────────────────────┐  │
   │  │ post_id | source_id | ... │  │
   │  ├────────────────────────────┤  │
   │  │  1001  │      5      │ ... │  │
   │  │  1002  │      5      │ ... │  │
   │  │  1003  │      5      │ ... │  │
   │  └────────────────────────────┘  │
   │                                  │
   │  sources table:                  │
   │  ┌────────────────────────────┐  │
   │  │ source_id | platform | ... │  │
   │  ├────────────────────────────┤  │
   │  │    5      │ Twitter/X │ ...│  │
   │  └────────────────────────────┘  │
   └──────────────────────────────────┘
            │
            ▼
   ┌──────────────────────────────────┐
   │  Ready for API Consumption       │
   │                                  │
   │  - Backend /posts endpoint       │
   │  - Filter by category='twitter'  │
   │  - Analysis & Flagging           │
   │  - Display in Dashboard          │
   └──────────────────────────────────┘
```

## Database Schema Mapping

```
Scraped Tweet Data
┌──────────────────┐
│  {               │
│    "author": "John Doe"
│    "content": "Tweet text..."
│    "timestamp": "2026-01-17T10:30:00Z"
│    "handle": "@johndoe"
│  }               │
└────────┬─────────┘
         │
         ▼ maps to ▼
         
posts table fields:
┌──────────────────────────────────────────────────────────┐
│ Column             │ Value              │ Source          │
├────────────────────┼────────────────────┼─────────────────┤
│ post_id            │ auto-increment     │ PostgreSQL PK   │
│ source_id          │ 5                  │ get_or_create   │
│ author             │ "John Doe"         │ tweet.author    │
│ text_content       │ "Tweet text..."    │ tweet.content   │
│ timestamp          │ 2026-01-17T...     │ tweet.timestamp │
│ url                │ NULL               │ (not used)      │
│ confidence_score   │ NULL               │ (for AI)        │
│ flagged            │ FALSE              │ default         │
│ category           │ "twitter"          │ static          │
└──────────────────────────────────────────────────────────┘
```

## Module Dependencies

```
x_scrapper.py
│
├─ asyncio (Python stdlib)
├─ random (Python stdlib)
├─ datetime (Python stdlib)
├─ os (Python stdlib)
├─ playwright.async_api (third-party)
├─ playwright_stealth (third-party)
│
└─ database.py ◄──── NEW IMPORT
   │
   ├─ sqlalchemy
   ├─ sqlalchemy.orm
   ├─ datetime (Python stdlib)
   ├─ os (Python stdlib)
   └─ dotenv (third-party)
```

## Authentication Flow (Unchanged)

```
scraper runs
   │
   ▼
Browser launches
   │
   ▼
Navigate to X.com/home
   │
   ▼
Check: Login required?
   │
   ├─ YES ──────────────────────────────┐
   │                                    │
   │  Print: "!!! LOGIN REQUIRED !!!"   │
   │  Wait: 60 seconds                  │
   │  User manually logs in via browser │
   │                                    │
   └──────────────────┬─────────────────┘
                      │
   ├─ NO ────────────┘
   │
   ▼
Already authenticated
   │
   ▼
Wait for tweet articles
   │
   ▼
Start scraping & scrolling
   │
   ▼
Save to database
```

## What Changed vs What Didn't

```
BEFORE                              AFTER
────────────────────────────────────────────────────────────

scraped_tweets.sql file        →    Direct DB insertion
  (appended to)

save_to_sql()                  →    save_posts_to_db()
  (wrote SQL strings)                (uses SQLAlchemy)

Manual SQL execution needed    →    Automatic DB connection
                                    (via database.py)

❌ No source management         →    ✅ Automatic source
                                    management

❌ No error handling            →    ✅ Per-post error
                                    handling

✅ Login/logout unchanged      ✅    Login/logout unchanged
✅ Scraping logic unchanged    ✅    Scraping logic unchanged
✅ No impact on backend        ✅    No impact on backend
✅ No impact on frontend       ✅    No impact on frontend
```

---

**Integration Date**: 2026-01-17  
**Status**: ✅ Complete & Ready for Use
