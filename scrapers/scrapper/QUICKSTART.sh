#!/bin/bash
# Quick Start Guide for Scraper Integration

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       X/Twitter Scraper - Database Integration Setup           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Navigate to scraper directory${NC}"
echo "cd d:\\V-Project\\vigilis\\scrapers\\scrapper"
echo ""

echo -e "${BLUE}Step 2: Install required packages${NC}"
echo "pip install -r requirements.txt"
echo ""
echo "Or install manually:"
echo "pip install sqlalchemy psycopg2-binary python-dotenv playwright playwright-stealth"
echo ""

echo -e "${BLUE}Step 3: Verify PostgreSQL connection${NC}"
echo "Make sure PostgreSQL is running:"
echo "- Host: localhost"
echo "- Port: 5432"
echo "- Database: vigilis_db"
echo "- User: postgres"
echo ""

echo -e "${YELLOW}Optional Step 4: Update .env file${NC}"
echo "Create .env file with:"
echo "DATABASE_URL=postgresql://postgres:CHERRY718hf@localhost:5432/vigilis_db"
echo ""

echo -e "${GREEN}Step 5: Run the scraper${NC}"
echo "python x_scrapper.py"
echo ""

echo -e "${YELLOW}What to expect:${NC}"
echo "1. Browser launches with persistent context"
echo "2. Page navigates to https://x.com/home"
echo "3. If logged out: Manual login required (60 seconds wait)"
echo "4. If logged in: Starts scrolling and collecting tweets"
echo "5. Tweets saved to database: 'posts' table"
echo "6. Output: 'Successfully saved X posts to database'"
echo ""

echo -e "${BLUE}Verify data in database:${NC}"
echo "SELECT post_id, author, text_content, timestamp FROM posts WHERE category='twitter' ORDER BY post_id DESC LIMIT 10;"
echo ""

echo -e "${GREEN}Integration Status:${NC}"
echo "✅ database.py - Database operations module"
echo "✅ x_scrapper.py - Updated to use new database module"
echo "✅ scraper_config.py - Configuration and constants"
echo "✅ DATABASE_INTEGRATION.md - Full documentation"
echo ""

echo -e "${YELLOW}Files Created:${NC}"
echo "- scrapers/scrapper/database.py"
echo "- scrapers/scrapper/scraper_config.py"
echo "- scrapers/scrapper/DATABASE_INTEGRATION.md"
echo ""

echo -e "${YELLOW}Files Modified:${NC}"
echo "- scrapers/scrapper/x_scrapper.py (added database integration)"
echo ""

echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "Ready to run: python x_scrapper.py"
