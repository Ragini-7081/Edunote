# Quick Reference - Neon PostgreSQL Setup

## Neon Database Configuration

**What is Neon?**
- Serverless PostgreSQL platform
- Free tier with generous limits
- Auto-scaling for production
- Connection pooling included
- Zero maintenance required

## Files Updated ✅
- ✅ `app/database.py` - Now supports Neon PostgreSQL via environment variables
- ✅ `.env` - Contains DATABASE_URL configuration (from Neon)
- ✅ `.env.example` - Template for team reference
- ✅ `.gitignore` - Already protects `.env` files
- ✅ `NEON_SETUP.md` - Complete step-by-step deployment guide

## What Your Code Does Now

Your `database.py` will:
1. Load `.env` file using `python-dotenv`
2. Check for `DATABASE_URL` environment variable
3. If found → Use PostgreSQL (Neon)
4. If not found → Fall back to SQLite (local dev)

## Immediate Actions Required

1. **Create Neon Project**:
   - Go to [Neon Console](https://console.neon.tech)
   - Create new project named "edunote"
   - Get your connection string

2. **Set Up Local Environment**:
   - Update `.env` with your Neon connection string
   - Run `pip install -r requirements.txt`

3. **Test Locally**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Deploy to Hosting** (Render, Railway, etc.):
   - Follow the 3-step process in `NEON_SETUP.md`:
     - Push code to GitHub
     - Connect to hosting provider
     - Add DATABASE_URL and other env vars

## Your Neon Connection String Format
```
postgresql://[user]:[password]@[host]/edunote?sslmode=require
```

**Example from Neon Console:**
```
postgresql://neon_user:abc123@ep-small-wind-123456.us-east-1.aws.neon.tech/edunote?sslmode=require
```

## Keep Your Credentials Safe ⚠️
- Never commit `.env` to git (it's in `.gitignore`)
- Keep `.env` file on your computer only
- Use `.env.example` for team collaboration
- Only share credentials with authorized team members
- Rotate passwords periodically in Neon Console

## Start Command for Production
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Read the Full Guide
Open `NEON_SETUP.md` for:
- Step-by-step Neon setup
- Local development instructions
- Production deployment options (Render, Railway, etc.)
- Security best practices
- Monitoring and maintenance
- Troubleshooting guide
- Migration from Render (if applicable)

## Need Help?
See `RENDER_SETUP.md` for troubleshooting section
