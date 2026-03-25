# 🚀 Vigilis - Local Setup Guide

Complete guide to setup and run the Vigilis project locally from scratch.

---

## 📋 Prerequisites

Before starting, ensure you have installed:

1. **Python 3.10+**
   - Download from https://www.python.org/downloads/
   - Verify: `python --version`

2. **Node.js (v16+) & npm**
   - Download from https://nodejs.org/
   - Verify: `node --version` and `npm --version`

3. **PostgreSQL 12+**
   - Download from https://www.postgresql.org/download/
   - Create a database user and database
   - Verify: `psql --version`

4. **Git** (optional, for version control)
   - Download from https://git-scm.com/

---

## 📁 Project Structure

After extracting the zip file, you should have:

```
vigilis/
├── backend/                    # FastAPI backend
│   ├── app/
│   ├── alembic/               # Database migrations
│   ├── main.py
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/                  # Electron + React frontend
│   ├── renderer/              # React app
│   ├── main.js
│   ├── package.json
│   └── preload.js
├── scrapers/                  # Twitter scraper
│   └── scrapper/
│       ├── x_scrapper.py
│       ├── database.py
│       └── requirements.txt
└── LOCAL_SETUP_GUIDE.md       # This file
```

---

## 🗄️ Database Setup

### Step 1: Create PostgreSQL Database

Open PostgreSQL terminal or use `psql`:

```bash
# Login to PostgreSQL
psql -U postgres

# Inside psql, run:
CREATE DATABASE vigilis_db;
CREATE USER vigilis_user WITH PASSWORD 'your_secure_password';
ALTER ROLE vigilis_user SET client_encoding TO 'utf8';
ALTER ROLE vigilis_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE vigilis_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE vigilis_db TO vigilis_user;
\q
```

### Step 2: Note Your Database Credentials

You'll need these later:
- **Database Name**: `vigilis_db`
- **Username**: `postgres`
- **Password**: `admin`
- **Host**: `localhost`
- **Port**: `5432`

### Step 3: Create Environment Files

#### Backend Environment (`.env` in `backend/` folder)

```bash
# Database
DATABASE_URL=postgresql://admin:admin@localhost:5432/vigilis_db

# Backend
BACKEND_URL=http://localhost:8000
SECRET_KEY=your_secret_key_here_change_this
ALGORITHM=HS256

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

#### Scraper Environment (`.env` in `scrapers/scrapper/` folder)

```bash
# Database
DATABASE_URL=postgresql://vigilis_user:your_secure_password@localhost:5432/vigilis_db

# Scraper settings
HEADLESS=true
INCOGNITO=true
```

---

## 💻 Backend Setup

### Step 1: Navigate to Backend Folder

```bash
cd vigilis/backend
```

### Step 2: Create Python Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database (Run Migrations)

```bash
# Apply migrations
alembic upgrade head

# If migrations don't exist, create them:
# alembic revision --autogenerate -m "initial schema"
# alembic upgrade head
```

### Step 5: Verify Backend Setup

```bash
python -c "import sqlalchemy; print('✅ SQLAlchemy installed')"
python -c "from app.db.session import SessionLocal; db = SessionLocal(); print('✅ Database connected'); db.close()"
```

---

## 🎨 Frontend Setup

### Step 1: Navigate to Frontend Folder

```bash
cd vigilis/frontend/renderer
```

### Step 2: Install Node Dependencies

```bash
npm install
```

### Step 3: Verify Frontend Setup

```bash
npm list react
```

---

## 🕷️ Scraper Setup

### Step 1: Navigate to Scraper Folder

```bash
cd vigilis/scrapers/scrapper
```

### Step 2: Create Python Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Playwright Browsers (One-time)

```bash
python -m playwright install
```

This downloads necessary browser binaries (~442 MB).

### Step 5: Verify Scraper Setup

```bash
python -c "import playwright; print('✅ Playwright installed')"
python -c "from database import get_db_session; db = get_db_session(); print('✅ Scraper database configured'); db.close()"
```

---

## 🚀 Running the Project

### Terminal 1: Backend Server

```bash
cd vigilis/backend

# Activate venv if not already active
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Start backend
python -m uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

✅ Backend ready at: `http://localhost:8000`

---

### Terminal 2: Frontend Development Server

```bash
cd vigilis/frontend/renderer

npm run dev
```

**Expected output:**
```
VITE v5.0.0 running at:
  ➜ http://localhost:5173/
```

✅ Frontend ready at: `http://localhost:5173`

---

### Terminal 3: Twitter Scraper

```bash
cd vigilis/scrapers/scrapper

# Activate venv if not already active
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

python x_scrapper.py
```

**Expected output:**
```
Launching browser with persistent context...
Navigating to https://x.com/home...
Starting active scrape loop...
--> Successfully saved 15 posts to database
```

✅ Scraper collecting posts

---

## 🔗 Access the Application

1. Open browser: `http://localhost:5173`
2. Login with credentials (check backend admin setup)
3. View dashboard with stats
4. Check "Flagged Posts" for scraped Twitter posts
5. Check "Sources" for scraper status
6. Monitor real-time data as scraper collects posts

---

## 📊 Verify Everything Works

### Checklist:

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] PostgreSQL database connected
- [ ] Can login to Vigilis
- [ ] Scraper running and collecting posts
- [ ] Posts appear in Flagged Posts tab
- [ ] Sources tab shows Twitter scraper status

### Test API Endpoints:

```bash
# In PowerShell/Terminal (with backend running):

# Get all posts
curl "http://localhost:8000/api/post"

# Get scraped posts only
curl "http://localhost:8000/api/post/scraped"

# Check health
curl "http://localhost:8000/docs"  # View Swagger docs
```

---

## 🛠️ Troubleshooting

### Backend Issues

**Error: "ModuleNotFoundError: No module named 'sqlalchemy'"**
- Solution: Ensure venv is activated and run `pip install -r requirements.txt`

**Error: "Could not connect to database"**
- Solution: Check DATABASE_URL in `.env` is correct
- Verify PostgreSQL is running: `psql -U postgres -c "SELECT version();"`

**Error: "Port 8000 already in use"**
- Solution: Change port: `python -m uvicorn app.main:app --reload --port 8001`

---

### Frontend Issues

**Error: "npm: command not found"**
- Solution: Install Node.js from https://nodejs.org/

**Error: "Module not found" in browser console**
- Solution: Run `npm install` again, then `npm run dev`

**CORS errors in console**
- Solution: Ensure backend CORS_ORIGINS includes `http://localhost:5173`

---

### Scraper Issues

**Error: "Executable doesn't exist at ms-playwright/chromium"**
- Solution: Run `python -m playwright install`

**Error: "Database connection failed"**
- Solution: Verify DATABASE_URL in scraper `.env`
- Check PostgreSQL is running and database exists

**Error: "No module named 'playwright'"**
- Solution: Activate venv and run `pip install -r requirements.txt`

---

### Database Issues

**Cannot login to PostgreSQL**
- Solution: 
  ```bash
  # Reset password if forgotten
  psql -U postgres
  ALTER USER vigilis_user WITH PASSWORD 'new_password';
  ```

**Database migrations not working**
- Solution:
  ```bash
  cd backend
  alembic upgrade head
  ```

---

## 📝 Default Login

After setup completes, use:
- **Username**: `admin`
- **Password**: `admin` (Change in production!)

---

## 🔐 Environment Variables Summary

### Backend (backend/.env)
```
DATABASE_URL=postgresql://vigilis_user:your_password@localhost:5432/vigilis_db
BACKEND_URL=http://localhost:8000
SECRET_KEY=change_me_in_production
ALGORITHM=HS256
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### Scraper (scrapers/scrapper/.env)
```
DATABASE_URL=postgresql://vigilis_user:your_password@localhost:5432/vigilis_db
HEADLESS=true
INCOGNITO=true
```

---

## 📦 Dependencies Summary

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL driver (psycopg2-binary)
- Python-dotenv
- Uvicorn

### Frontend
- React 18+
- TypeScript
- Vite
- TanStack Query
- Wouter (routing)
- Tailwind CSS
- shadcn/ui

### Scraper
- Playwright
- SQLAlchemy
- PostgreSQL driver
- Python-dotenv

---

## 🎯 Quick Reference

### Commands Cheat Sheet

```bash
# Backend
cd vigilis/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend
cd vigilis/frontend/renderer
npm install
npm run dev

# Scraper
cd vigilis/scrapers/scrapper
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install
python x_scrapper.py
```

---

## ✅ Setup Complete!

Your Vigilis monitoring system is ready to use locally.

**Next Steps:**
1. Ensure all three services are running (Backend, Frontend, Scraper)
2. Open http://localhost:5173 in your browser
3. Login and start monitoring
4. Check scraped posts in real-time

**For Production:**
- Change all default passwords
- Use environment-specific `.env` files
- Set up HTTPS
- Configure proper CORS origins
- Use production PostgreSQL instance

---

## 📞 Support

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Verify all prerequisites are installed
3. Ensure all three services are running
4. Check console/terminal for error messages
5. Verify database connection with sample queries

---

**Happy monitoring! 🎉**
