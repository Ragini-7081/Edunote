# Cloudinary Setup Guide - Free Video Storage

## 🎯 Overview

Edunote now supports **Cloudinary** for video storage! This gives you:

✅ **25 GB/month free** - plenty for small to medium apps  
✅ **CDN included** - fast video delivery worldwide  
✅ **Auto-optimization** - videos compressed automatically  
✅ **No server storage needed** - videos don't disappear on restart  
✅ **Easy integration** - just add environment variables  

---

## 📋 Step 1: Create Cloudinary Account

1. Go to [https://cloudinary.com](https://cloudinary.com)
2. Click **Sign up for free**
3. Choose **Free** tier
4. Complete registration
5. You'll be directed to the dashboard

---

## 🔑 Step 2: Get Your Credentials

1. In Cloudinary Dashboard, go to **Settings** (gear icon)
2. Click on **API Keys** tab
3. You'll see:
   - **Cloud Name** (e.g., `dxxx8yyyyy`)
   - **API Key** (e.g., `123456789...`)
   - **API Secret** (e.g., `aBcDeFg...`)

⚠️ **Keep API Secret private!** Never share it.

---

## 📝 Step 3: Update .env File

Add these to your `.env` file:

```env
# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here

# Other existing variables...
DATABASE_URL=postgresql://...
RAZORPAY_KEY_ID=...
```

**Example:**
```env
CLOUDINARY_CLOUD_NAME=dxxx8yyyyy
CLOUDINARY_API_KEY=123456789000111
CLOUDINARY_API_SECRET=aBcDeFgHiJkLmNoPqRsTuVwXyZ
```

---

## 📦 Step 4: Install Dependencies

```bash
pip install cloudinary

# Or update all dependencies
pip install -r requirements.txt
```

---

## 🧪 Step 5: Test Locally

```bash
python -m uvicorn app.main:app --reload
```

Then:
1. Go to http://localhost:8000
2. Login as a seller
3. Upload a video
4. Video should be uploaded to Cloudinary ✅
5. Check Cloudinary dashboard to see your uploaded files

---

## 🚀 Step 6: Deploy to Render

### Update Environment Variables on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your **edunote** service
3. Click **Environment** tab
4. Add the three variables:

```
CLOUDINARY_CLOUD_NAME = your_cloud_name
CLOUDINARY_API_KEY = your_api_key
CLOUDINARY_API_SECRET = your_api_secret
```

5. Click **Save**
6. Service will auto-redeploy

### Push Code Updates

```bash
git add requirements.txt app/main.py
git commit -m "Add Cloudinary video storage integration"
git push origin main
```

Render will automatically pull and deploy.

---

## ✅ Verification Checklist

- [x] Cloudinary account created
- [x] API credentials copied
- [x] `.env` file updated locally
- [x] `requirements.txt` has cloudinary
- [x] Videos uploading successfully
- [x] Render environment variables set
- [x] App deployed with Cloudinary enabled

---

## 📊 Monitoring

### Check Upload Quota

1. Go to Cloudinary Dashboard
2. Click **Usage** tab
3. See how much bandwidth/storage used this month
4. Free tier: 25 GB/month total

### View Uploaded Videos

1. Cloudinary Dashboard → **Media Library**
2. Videos in folder: `edunote/videos/`
3. Thumbnails in folder: `edunote/thumbnails/`

---

## 🔄 Fallback Behavior

If Cloudinary credentials are missing/invalid:
- ✅ App still works (uses local filesystem)
- ⚠️ Videos stored locally (lost on restart on Render)
- 💡 Recommend always setting Cloudinary credentials

**How to disable Cloudinary:**
Just remove/comment out `CLOUDINARY_*` variables in `.env`

---

## 🆘 Troubleshooting

### "Cloudinary not enabled"
**Solution:** Check `.env` has all three variables and they're correct

### Videos uploading but not appearing in Cloudinary
**Solution:** Check API credentials are correct in Render environment variables

### Getting "API signature invalid" error
**Solution:** Make sure `CLOUDINARY_API_SECRET` is set (not just key and name)

### Storage quota exceeded
**Solution:** Delete old test videos from Cloudinary Media Library

---

## 🎁 Free Tier Limits

| Feature | Limit |
|---------|-------|
| **Storage** | 25 GB/month |
| **Bandwidth** | 25 GB/month |
| **Transformations** | Unlimited |
| **Requests** | Unlimited |
| **File Size** | 100 MB per file |

Perfect for educational content! 📚

---

## 💰 When You Need More

If you exceed free tier:
- **Pay-as-you-go** at $0.04/GB storage, $0.05/GB bandwidth
- **Pro plans** starting at $99/month with more features
- Or use another provider (Supabase, Bunny CDN, etc.)

---

## 📚 Useful Links

- [Cloudinary Docs](https://cloudinary.com/documentation)
- [Video Upload API](https://cloudinary.com/documentation/video_upload_api_reference)
- [Transformations Guide](https://cloudinary.com/documentation/image_transformation_reference)
- [Pricing](https://cloudinary.com/pricing)

---

## ✨ What's Next?

Your app now has:
- ✅ Free persistent video storage
- ✅ Global CDN for fast playback
- ✅ Auto video optimization
- ✅ Works with Neon database
- ✅ Survives server restarts

Ready to scale! 🚀
