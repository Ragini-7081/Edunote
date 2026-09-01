# Quick Reference - Render PostgreSQL Setup

## Your Credentials
```
Database: edunote
User: edunote_0brb_user
Password: KnKSrQKZe4hZIctM0Rhv9eWZIze6lh4Q
```

## Files Updated ✅
- ✅ `app/database.py` - Now supports PostgreSQL via environment variables
- ✅ `requirements.txt` - Added `psycopg2-binary==2.9.9`
- ✅ `.env` - Contains DATABASE_URL configuration
- ✅ `.env.example` - Template for team reference
- ✅ `.gitignore` - Already protects `.env` files
- ✅ `RENDER_SETUP.md` - Complete step-by-step deployment guide

## What Your Code Does Now

Your `database.py` will:
1. Load `.env` file using `python-dotenv`
2. Check for `DATABASE_URL` environment variable
3. If found → Use PostgreSQL (Render)
4. If not found → Fall back to SQLite (local dev)

## Immediate Actions Required

1. **Read the full guide**:
   Open `RENDER_SETUP.md` for detailed instructions

2. **Local Testing** (optional):
   Install PostgreSQL locally and test before deploying

3. **Deploy to Render**:
   Follow the 3-step process in `RENDER_SETUP.md`:
   - Create PostgreSQL database
   - Deploy Web Service
   - Add environment variables

## Keep Your Credentials Safe ⚠️
- Never commit `.env` to git (it's in `.gitignore`)
- Keep `.env` file on your computer only
- Use `.env.example` for team collaboration
- Only share credentials with authorized team members

## Start Command for Render
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Need Help?
See `RENDER_SETUP.md` for troubleshooting section
