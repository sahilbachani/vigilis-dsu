@echo off
REM Quick Start Guide for Scraper Integration (Windows)

echo.
echo ════════════════════════════════════════════════════════════════
echo        X/Twitter Scraper - Database Integration Setup
echo ════════════════════════════════════════════════════════════════
echo.

echo [Step 1] Navigate to scraper directory
echo cd d:\V-Project\vigilis\scrapers\scrapper
echo.

echo [Step 2] Install required packages
echo pip install sqlalchemy psycopg2-binary python-dotenv playwright playwright-stealth
echo.

echo [Step 3] Verify PostgreSQL is running
echo - Host: localhost
echo - Port: 5432
echo - Database: vigilis_db
echo - User: postgres
echo.

echo [Step 4] Optional - Create .env file
echo DATABASE_URL=postgresql://postgres:CHERRY718hf@localhost:5432/vigilis_db
echo.

echo [Step 5] Run the scraper
echo python x_scrapper.py
echo.

echo ════════════════════════════════════════════════════════════════
echo                      What to Expect:
echo ════════════════════════════════════════════════════════════════
echo.
echo 1. Browser launches with persistent context
echo 2. Page navigates to https://x.com/home
echo 3. If logged out: Manual login required (60 seconds)
echo 4. Starts scrolling and collecting tweets
echo 5. Tweets automatically saved to 'posts' table
echo 6. Output: "Successfully saved X posts to database"
echo.

echo ════════════════════════════════════════════════════════════════
echo                      Integration Files:
echo ════════════════════════════════════════════════════════════════
echo.
echo CREATED:
echo   - scrapers/scrapper/database.py
echo   - scrapers/scrapper/scraper_config.py
echo   - scrapers/scrapper/DATABASE_INTEGRATION.md
echo.
echo MODIFIED:
echo   - scrapers/scrapper/x_scrapper.py
echo.

echo ════════════════════════════════════════════════════════════════
echo Ready to run: python x_scrapper.py
echo ════════════════════════════════════════════════════════════════
echo.

pause
