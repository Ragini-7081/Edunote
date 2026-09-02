# Student Dashboard & Access Control Guide

## 🎯 Overview

Your Edunote app now has a complete student dashboard system with:

✅ **Purchased Books & Videos** - Shows only what the student bought  
✅ **Free Books & Videos** - Auto-grants access to free content  
✅ **Access Control** - Verifies purchase before allowing viewing  
✅ **My Library** - "My Books" and "My Videos" sections in dashboard  
✅ **One-Click Access** - Free items grant access instantly  

---

## 📊 New API Endpoints

### 1. **Get Student Dashboard**
```
GET /student/{user_id}
```
Shows dashboard with links to purchased and free content.

**Response includes:**
- User profile
- Purchase count
- URLs to books/videos/purchases

---

### 2. **Get Student's Books** (Purchased + Free)
```
GET /student/{user_id}/books
```

**Returns:**
```json
[
  {
    "id": 1,
    "title": "Python 101",
    "author_name": "John Doe",
    "price": 0,
    "is_free": true,
    "has_access": true,
    "description": "...",
    "category": "Programming"
  },
  {
    "id": 2,
    "title": "Advanced Python",
    "author_name": "Jane Smith",
    "price": 299.99,
    "is_free": false,
    "has_access": true,
    "description": "..."
  }
]
```

---

### 3. **Get Student's Videos** (Purchased + Free)
```
GET /student/{user_id}/videos
```

Returns all videos accessible to the student (purchased + free).

---

### 4. **Get Student's Purchases**
```
GET /student/{user_id}/purchases
```

Returns a list of purchased items with dates.

---

### 5. **Check Access to Item**
```
GET /api/check-access/{item_type}/{item_id}?user_id={user_id}
```

**Parameters:**
- `item_type`: `book` or `video`
- `item_id`: ID of the book/video
- `user_id`: Student's ID

**Response:**
```json
{
  "item_type": "book",
  "item_id": 1,
  "is_free": true,
  "price": 0,
  "has_access": true,
  "user_id": 5
}
```

---

### 6. **Grant Access to Free Book**
```
POST /student/{user_id}/access-free-book/{book_id}
```

Creates a free purchase record for instant access.

**Response:**
```json
{
  "success": true,
  "message": "Access granted to free book",
  "redirect": "/read/1?user_id=5"
}
```

---

### 7. **Grant Access to Free Video**
```
POST /student/{user_id}/access-free-video/{video_id}
```

Creates a free purchase record for instant access.

---

### 8. **Confirm Book Purchase**
```
POST /student/{user_id}/buy-book/{book_id}/confirm
```

Creates a paid purchase record (or free if price is 0).

**Form Data:**
```
payment_method: "Razorpay" | "PayU" | "UPI"
```

---

### 9. **Confirm Video Purchase**
```
POST /student/{user_id}/buy-video/{video_id}/confirm
```

Creates a paid purchase record (or free if price is 0).

---

## 🔄 Access Flow

### For Paid Items
```
Student clicks "Buy" 
  → Process Payment (Razorpay/PayU)
  → Payment succeeds
  → Create Purchase record (active=True)
  → Redirect to item with user_id
  → Check access via API
  → Grant viewing access
```

### For Free Items
```
Student clicks "Read" / "Watch"
  → POST /student/{user_id}/access-free-book/{book_id}
  → Create Purchase record with amount=0
  → Redirect to item with user_id
  → Check access via API
  → Grant viewing access
```

---

## 🧪 Testing Scenario

### 1. Login as Student (user_id: 5)

### 2. View Dashboard
```
GET /student/5
```

### 3. Get My Books
```
GET /student/5/books
```
Should return free books and purchased books.

### 4. Access Free Book
```
POST /student/5/access-free-book/3
```
Grants instant access to book ID 3 (if free).

### 5. Check Access
```
GET /api/check-access/book/3?user_id=5
```
Should return `"has_access": true`

### 6. View Book
```
GET /read/3?user_id=5
```
Should display book content.

---

## 💰 Purchase Logic

### Free Items (price = 0)
- **No payment needed**
- Click button → instant access
- Creates purchase record with amount=0
- No payment_id required

### Paid Items (price > 0)
- **Payment required**
- Click "Buy" → Show payment form
- Process payment
- On success → Create purchase record
- Redirect to content

---

## 📝 Database Update

### Purchase Table
```
id: Primary Key
user_id: Student who purchased
amount: Amount paid (0 for free)
book_id: Book ID (if book purchase)
video_id: Video ID (if video purchase)
payment_id: Payment record ID (null for free)
active: True/False (access status)
purchased_at: Timestamp
```

---

## 🎨 Frontend Integration

### Show Books/Videos in Dashboard

```javascript
// Fetch student's books
const response = await fetch(`/student/${user_id}/books`);
const books = await response.json();

// Fetch student's videos
const response = await fetch(`/student/${user_id}/videos`);
const videos = await response.json();

// Check access before viewing
const access = await fetch(`/api/check-access/book/1?user_id=${user_id}`);
const { has_access } = await access.json();

if (has_access) {
  // Show content
} else {
  // Show buy button
}
```

---

## ⚙️ Configuration

### Free Books/Videos Setup

1. **Create a book/video with price = 0**
   - Author: Set price = 0
   - Status: Published

2. **Student accesses it**
   - Dashboard shows it in "My Books/Videos"
   - Auto-grants access

3. **Purchase record created**
   - Amount: 0
   - payment_id: null
   - active: True

---

## 🔐 Security

### Access Verification
- Always check `has_access` before showing content
- Verify `user_id` matches in URL
- Check purchase record exists and is active
- Use `/api/check-access/` endpoint

### Prevent Unauthorized Access
- Use access control middleware
- Verify purchase in `/read/{book_id}` route
- Verify purchase in `/video/{video_id}` route
- Return 403 Forbidden if no access

---

## 🐛 Troubleshooting

### "Book/Video not showing in My Library"
**Check:**
1. Is it published? (status = "Published")
2. Is it free (price = 0) or did student purchase?
3. Check database Purchase record exists

### "Access denied when trying to view"
**Check:**
1. Purchase record exists for this user + item
2. Purchase is active (active = True)
3. User ID in URL matches logged-in user
4. Check `/api/check-access/` returns has_access: true

### "Free item not auto-granting access"
**Check:**
1. Price is exactly 0 (not null)
2. Status is "Published"
3. POST endpoint for access is working
4. Check database for Purchase record

---

## 📚 Next Steps

1. **Test the flows** - Use the testing scenario above
2. **Update templates** - Show "My Books" and "My Videos"
3. **Add access checks** - Verify before showing content
4. **Deploy** - Push changes to Render

---

## 🚀 Example: Complete Student Flow

```
1. Student visits /student/5 (dashboard)
   ↓
2. Dashboard shows FREE books and PURCHASED books
   ↓
3. Student clicks "Read Book" (free book)
   → POST /student/5/access-free-book/3
   → Creates Purchase(user_id=5, book_id=3, amount=0)
   → Returns redirect: /read/3?user_id=5
   ↓
4. Student views book at /read/3?user_id=5
   → Check: GET /api/check-access/book/3?user_id=5
   → Response: has_access: true
   → Display book content ✅
```

---

## 📋 API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/student/{id}` | GET | View dashboard |
| `/student/{id}/books` | GET | Get my books |
| `/student/{id}/videos` | GET | Get my videos |
| `/student/{id}/purchases` | GET | Get purchase history |
| `/api/check-access/{type}/{id}` | GET | Verify access |
| `/student/{id}/access-free-book/{id}` | POST | Grant free book access |
| `/student/{id}/access-free-video/{id}` | POST | Grant free video access |
| `/student/{id}/buy-book/{id}/confirm` | POST | Purchase/access book |
| `/student/{id}/buy-video/{id}/confirm` | POST | Purchase/access video |

---

## 💡 Key Features

✅ **One endpoint for books** - Returns both purchased and free  
✅ **One endpoint for videos** - Returns both purchased and free  
✅ **Smart access checking** - Knows about free vs paid  
✅ **Free auto-access** - Zero-price items grant instant access  
✅ **Purchase tracking** - All items tracked in database  
✅ **Fallback support** - Works with or without Cloudinary  

Your app now has a professional student dashboard! 🎓
