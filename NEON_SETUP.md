# PostgreSQL on Neon - Setup Guide

## 📋 Summary of Changes Made

✅ Updated `database.py` to support PostgreSQL via environment variables  
✅ Database configuration now works with Neon's PostgreSQL  
✅ `.env` file with Neon database credentials  
✅ `.gitignore` updated to protect sensitive data  

---

## 🗄️ Neon Database Setup

Neon is a serverless PostgreSQL platform that provides:
- **Free tier** with generous limits
- **Auto-scaling** for production
- **Branching** for development/testing
- **Connection pooling** via Neon's pooler

---

## 🚀 Step-by-Step Neon Deployment

### Step 1: Create a Neon PostgreSQL Project

1. Go to [Neon Console](https://console.neon.tech)
2. Sign up or login with your account
3. Click **"New Project"**
4. Configure your project:
   - **Project Name**: `edunote`
   - **Database Name**: `edunote`
   - **Region**: Choose closest to your deployment region
   - **Compute Size**: Starter ($0/month) for free tier
5. Click **"Create Project"**
6. You'll be redirected to the project dashboard

### Step 2: Get Your Database Connection String

1. In the Neon Console, navigate to your project
2. Click **"Connection string"** or **"Database"**
3. You'll see multiple connection options:
   - **PostgreSQL** (standard): `postgresql://[user]:[password]@[host]/[database]`
   - **PostgreSQL with pooler** (recommended): Uses connection pooling
4. Copy the **PostgreSQL with pooler** connection string (recommended)

**Connection String Format:**
```
postgresql://[user]:[password]@[host]/[database]?sslmode=require
```

**Example:**
```
postgresql://neon_user:abc123@ep-small-wind-123456.us-east-1.aws.neon.tech/edunote?sslmode=require
```

### Step 3: Set Up Local Environment Variables

1. Create or update `.env` file in the project root:

```env
# Database Configuration for Neon
DATABASE_URL=postgresql://[your-neon-user]:[your-password]@[your-neon-host]/edunote?sslmode=require

# Payment Gateway Keys
RAZORPAY_KEY_ID=your_actual_key_id
RAZORPAY_KEY_SECRET=your_actual_secret

# PayU Configuration
PAYU_MERCHANT_KEY=gtKFFx
PAYU_MERCHANT_SALT=4R38IvwiV57FwVpsgOvTXBdLE4tHUXFW
PAYU_MODE=test

# OpenRouter AI Configuration
OPENROUTER_API=your_actual_api_key
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Test locally:
```bash
uvicorn app.main:app --reload
```

### Step 4: Deploy to Your Hosting Provider

#### Option A: Deploy to Render

1. Push your code to GitHub (or GitLab)
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **"New"** → **"Web Service"**
4. Connect your GitHub repository
5. Configure the service:
   - **Name**: `edunote-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Click **"Advanced"** and add Environment Variables:
   - `DATABASE_URL`: (Paste your Neon connection string)
   - `RAZORPAY_KEY_ID`: (Your actual key)
   - `RAZORPAY_KEY_SECRET`: (Your actual secret)
   - `PAYU_MERCHANT_KEY`: `gtKFFx`
   - `PAYU_MERCHANT_SALT`: `4R38IvwiV57FwVpsgOvTXBdLE4tHUXFW`
   - `PAYU_MODE`: `test`
   - `OPENROUTER_API`: (Your actual API key)
   - `OPENROUTER_MODEL`: `nvidia/nemotron-3-ultra-550b-a55b:free`
7. Click **"Create Web Service"**
8. Wait for deployment (3-5 minutes)

#### Option B: Deploy to Railway

1. Go to [Railway Dashboard](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Connect your GitHub repository
4. Add environment variables:
   - `DATABASE_URL`: (Paste your Neon connection string)
   - Other keys as listed above
5. Set build and start commands:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### Option C: Deploy to Vercel (Serverless)

For serverless deployment with Vercel, additional setup may be needed. Refer to Vercel's documentation for FastAPI deployments.

### Step 5: Verify the Connection

Once deployed:

1. Check the **Logs** in your hosting provider for any database connection errors
2. Your app will be available at the provided URL
3. Test the endpoint: `https://your-app-domain.com/docs` (FastAPI Swagger UI)
4. Monitor database connections in Neon Console:
   - Navigate to **"Monitoring"** tab
   - Check active connections and query performance

---

## 🔄 Local Development with Neon

You can test locally with your Neon database:

### Setup

1. Update your `.env` file with the Neon connection string
2. Run your FastAPI app:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 🔐 Security Best Practices

### Neon Security

1. **Connection Pooling**: Neon provides built-in connection pooling via their pooler
2. **SSL/TLS**: Neon requires SSL connections (`?sslmode=require`)
3. **IP Allowlisting**: Configure IP restrictions in Neon Console if needed
4. **Secrets Management**: Use environment variables for credentials

### Application Security

1. **Environment Variables**: Store `DATABASE_URL` in environment variables only
2. **Git Security**: Never commit `.env` file (already in `.gitignore`)
3. **Credentials Rotation**: Periodically rotate database passwords in Neon Console

---

## 📊 Neon Monitoring & Maintenance

### View Database Statistics

1. Log into [Neon Console](https://console.neon.tech)
2. Navigate to your project
3. Click **"Monitoring"** tab to view:
   - Active connections
   - Query performance
   - Storage usage
   - CPU usage

### Backup & Recovery

1. Neon automatically backs up your data
2. To restore from a backup:
   - Go to **"Backups"** in Neon Console
   - Select a backup point
   - Click **"Restore"**

### Performance Tuning

1. Use Neon's **"Advisor"** for optimization suggestions
2. Check slow query logs in Monitoring tab
3. Consider upgrading compute size if hitting resource limits

---

## ❌ Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `could not translate host name` | Check your connection string is correct; verify Neon project is active |
| `FATAL: too many connections` | Enable connection pooling in Neon; increase connection limit |
| `SSL certificate verification failed` | Ensure `?sslmode=require` is in connection string |
| `permission denied for schema "public"` | Verify user privileges in Neon Console; reset user if needed |
| `database does not exist` | Create database via Neon Console or using `psql` |

---

## 📝 Database Connection String Components

For reference, your Neon connection string contains:

```
postgresql://[user]:[password]@[host]/[database]?sslmode=require
         └──────────────────┬──────────────────┘  └────┬─────┘
                      Connection Details           SSL Mode
```

- **user**: Database username (provided by Neon)
- **password**: Database password (provided by Neon)
- **host**: Neon endpoint hostname (e.g., `ep-small-wind-123456.us-east-1.aws.neon.tech`)
- **database**: Database name (`edunote`)
- **sslmode=require**: SSL/TLS encryption (required by Neon)

---

## 🚀 Deployment Checklist

Before deploying to production:

1. ✅ Create Neon project and get connection string
2. ✅ Test locally with Neon connection string in `.env`
3. ✅ Update `.env` with all required API keys
4. ✅ Run `pip install -r requirements.txt` successfully
5. ✅ Test all key features locally (books, videos, payments, etc.)
6. ✅ Push code to GitHub/GitLab
7. ✅ Deploy to hosting provider (Render, Railway, etc.)
8. ✅ Add `DATABASE_URL` and other env vars to hosting provider
9. ✅ Verify deployment logs show successful database connection
10. ✅ Test live application with `/docs` endpoint

---

## 📖 Useful Links

- [Neon Documentation](https://neon.tech/docs)
- [Neon Connection String Formats](https://neon.tech/docs/connect/connection-details)
- [SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [Psycopg Documentation](https://www.psycopg.org/psycopg3/docs/)

---

## 🔄 Migrating from Render to Neon

If you were using Render PostgreSQL previously:

1. **Export data from Render** (optional):
   ```bash
   pg_dump "postgres://[render-user]:[render-pass]@[render-host]/[db]" > backup.sql
   ```

2. **Import data to Neon** (optional):
   ```bash
   psql "postgresql://[neon-user]:[neon-pass]@[neon-host]/[db]" < backup.sql
   ```

3. **Update environment variables**:
   - Replace `DATABASE_URL` with your Neon connection string
   - Update in `.env` locally
   - Update in your hosting provider's environment settings

4. **Test and deploy**:
   - Run locally to verify connection works
   - Deploy to hosting provider with new `DATABASE_URL`

---

**Happy deploying!** 🎉
