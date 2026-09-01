# PostgreSQL on Render - Setup Guide

## 📋 Summary of Changes Made

✅ Updated `database.py` to support PostgreSQL via environment variables  
✅ Added `psycopg2-binary` to `requirements.txt`  
✅ Created `.env` file with PostgreSQL credentials  
✅ Updated `.gitignore` to protect sensitive data  

---

## 🗄️ Database Credentials

```
Database Name: edunote
Username: edunote_0brb_user
Password: KnKSrQKZe4hZIctM0Rhv9eWZIze6lh4Q
Connection URL (Local): postgresql://edunote_0brb_user:KnKSrQKZe4hZIctM0Rhv9eWZIze6lh4Q@localhost:5432/edunote
```

---

## 🚀 Step-by-Step Render Deployment

### Step 1: Create a PostgreSQL Database on Render

1. Go to [Render.com](https://render.com)
2. Login to your Render account
3. Click **"New"** → Select **"PostgreSQL"**
4. Fill in the details:
   - **Name**: `edunote-db`
   - **Database**: `edunote`
   - **User**: `edunote_0brb_user`
   - **Region**: Choose closest to your location (e.g., `US East`)
   - **PostgreSQL Version**: `14` or `15` (latest recommended)
5. Click **"Create Database"**
6. Wait for the database to be created (2-3 minutes)
7. Copy the **Internal Database URL** (you'll need this)

### Step 2: Deploy Your Render Web Service

1. From Render dashboard, click **"New"** → **"Web Service"**
2. Connect your GitHub/GitLab repository:
   - Click **"Connect Repository"**
   - Select your Edunote repository
   - Click **"Connect"**

3. Configure the service:
   - **Name**: `edunote-api` (or your preferred name)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Select **"Free"** (or paid if needed)

4. Click **"Advanced"** and add Environment Variables:
   
   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | (Paste the Internal Database URL from Step 1) |
   | `RAZORPAY_KEY_ID` | (Your actual key) |
   | `RAZORPAY_KEY_SECRET` | (Your actual secret) |
   | `PAYU_MERCHANT_KEY` | `gtKFFx` |
   | `PAYU_MERCHANT_SALT` | `4R38IvwiV57FwVpsgOvTXBdLE4tHUXFW` |
   | `PAYU_MODE` | `test` |
   | `OPENROUTER_API` | (Your actual API key) |
   | `OPENROUTER_MODEL` | `nvidia/nemotron-3-ultra-550b-a55b:free` |

5. Click **"Create Web Service"**
6. Wait for deployment (3-5 minutes)

### Step 3: Verify the Connection

Once deployed:

1. Check the **Logs** tab in Render for any errors
2. Your app will be available at: `https://edunote-api.onrender.com` (or similar)
3. Test the endpoint: `https://edunote-api.onrender.com/docs` (FastAPI Swagger UI)

---

## 🔄 Local Development with PostgreSQL

If you want to test locally with PostgreSQL:

### On Windows:

1. **Install PostgreSQL**:
   ```powershell
   # Using Chocolatey
   choco install postgresql
   ```

2. **Create the database**:
   ```powershell
   psql -U postgres
   # Inside psql prompt:
   CREATE DATABASE edunote;
   CREATE USER edunote_0brb_user WITH PASSWORD 'KnKSrQKZe4hZIctM0Rhv9eWZIze6lh4Q';
   ALTER ROLE edunote_0brb_user SET client_encoding TO 'utf8';
   ALTER ROLE edunote_0brb_user SET default_transaction_isolation TO 'read committed';
   GRANT ALL PRIVILEGES ON DATABASE edunote TO edunote_0brb_user;
   \q
   ```

3. **Update `.env` for local development**:
   ```
   DATABASE_URL=postgresql://edunote_0brb_user:KnKSrQKZe4hZIctM0Rhv9eWZIze6lh4Q@localhost:5432/edunote
   ```

4. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

5. **Run the app**:
   ```powershell
   uvicorn app.main:app --reload
   ```

---

## 🔐 Security Considerations

### Important: Keep `.env` Safe

✅ `.env` is already in `.gitignore` - credentials won't be committed  
✅ Use `.env.example` for team reference only  
✅ **Never** share your `.env` file or database password  
✅ Change password regularly in production  

### Render Security

- Use **Internal Database URL** for your web service (private network)
- Only expose via environment variables, not in code
- Render automatically encrypts all environment variables

---

## 📊 Monitoring & Logs

### View Logs in Render:
1. Go to your Web Service on Render
2. Click **"Logs"** tab
3. Watch real-time output
4. Check for connection errors or startup issues

### Common Issues:

| Error | Solution |
|-------|----------|
| `Connection refused` | Database URL is incorrect or DB isn't running |
| `Password authentication failed` | Check username/password in `.env` |
| `database "edunote" does not exist` | Create database in Render PostgreSQL dashboard |
| `Module not found: psycopg2` | Ensure `psycopg2-binary` is in `requirements.txt` |

---

## 🔄 Updating Code After Deployment

1. **Make changes locally** (with local PostgreSQL for testing)
2. **Commit and push** to GitHub:
   ```powershell
   git add .
   git commit -m "Update database configuration for PostgreSQL"
   git push
   ```
3. **Render auto-deploys** (if connected to GitHub)
4. Check **Logs** in Render to verify deployment

---

## 📞 Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Test locally with PostgreSQL (if available)
3. ✅ Create PostgreSQL database on Render
4. ✅ Deploy Web Service on Render
5. ✅ Add environment variables to Render
6. ✅ Monitor logs and verify deployment

---

## 🆘 Support

- **Render Docs**: https://render.com/docs
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **SQLAlchemy + PostgreSQL**: https://docs.sqlalchemy.org/en/20/dialects/postgresql/

