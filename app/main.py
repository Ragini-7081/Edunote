import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    Request,
    Form,
    Depends,
    UploadFile,
    File,
    Body,
    HTTPException
)

from fastapi.responses import (
    HTMLResponse,
    RedirectResponse
)

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy.orm import Session

from pathlib import Path

import threading
import webbrowser
import shutil
import uuid

from .database import (
    Base,
    engine,
    get_db,
    initialize_database
)

from . import crud
from . import models
from . import schemas

from .schemas import (
    RegisterUser,
    LoginUser,
    CommentCreate,
    BookCreate
)


# ==================================================
# LOAD ENV FILES FROM PROJECT ROOT
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BASE_DIR / ".env")


# ==================================================
# DATABASE
# ==================================================

initialize_database()

models.create_tables(engine)


# ==================================================
# APP
# ==================================================

load_dotenv()

app = FastAPI(
    title="EduNote"
)

try:
    import razorpay
except ImportError:  # pragma: no cover
    razorpay = None

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")


def razorpay_enabled():
    return bool(
        razorpay is not None and
        RAZORPAY_KEY_ID and
        RAZORPAY_KEY_SECRET
    )


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    if not razorpay_enabled() or not signature:
        return False

    payload = f"{order_id}|{payment_id}".encode("utf-8")
    generated = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated, signature)


PAYU_MERCHANT_KEY = os.getenv("PAYU_MERCHANT_KEY", "gtKFFx")
PAYU_MERCHANT_SALT = os.getenv("PAYU_MERCHANT_SALT", "4R38IvwiV57FwVpsgOvTXBdLE4tHUXFW")
PAYU_MODE = os.getenv("PAYU_MODE", "test").lower()
PAYU_ACTION_URL = "https://test.payu.in/_payment" if PAYU_MODE == "test" else "https://secure.payu.in/_payment"


def generate_payu_hash(txnid: str, amount: str, productinfo: str, firstname: str, email: str, udf1: str = "") -> str:
    # Standard PayU Hash: key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||SALT
    hash_str = f"{PAYU_MERCHANT_KEY}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|{udf1}||||||||||{PAYU_MERCHANT_SALT}"
    return hashlib.sha512(hash_str.encode("utf-8")).hexdigest().lower()



def verify_payu_hash(data: dict) -> bool:
    received_hash = (data.get("hash") or "").lower()
    if not received_hash:
        return False

    status = data.get("status", "")
    txnid = data.get("txnid", "")
    amount = data.get("amount", "")
    productinfo = data.get("productinfo", "")
    firstname = data.get("firstname", "")
    email = data.get("email", "")
    udf1 = data.get("udf1", "")
    udf2 = data.get("udf2", "")
    udf3 = data.get("udf3", "")
    udf4 = data.get("udf4", "")
    udf5 = data.get("udf5", "")
    key = data.get("key", PAYU_MERCHANT_KEY)
    additional_charges = data.get("additionalCharges")

    if additional_charges:
        hash_str = f"{additional_charges}|{PAYU_MERCHANT_SALT}|{status}||||||{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|{email}|{firstname}|{productinfo}|{amount}|{txnid}|{key}"
    else:
        hash_str = f"{PAYU_MERCHANT_SALT}|{status}||||||{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|{email}|{firstname}|{productinfo}|{amount}|{txnid}|{key}"

    computed_hash = hashlib.sha512(hash_str.encode("utf-8")).hexdigest().lower()
    return hmac.compare_digest(computed_hash, received_hash)


# ==================================================
# SESSION MIDDLEWARE
# ==================================================

app.add_middleware(
    SessionMiddleware,
    secret_key="edunote-secret-key-change-this-later"
)


# ==================================================
# OPEN BROWSER AUTOMATICALLY
# ==================================================

def open_browser():
    webbrowser.open(
        "http://127.0.0.1:8000"
    )


threading.Timer(
    1.5,
    open_browser
).start()


# ==================================================
# PATHS
# ==================================================

UPLOADS_DIR = BASE_DIR / "static" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
# ==================================================
# STATIC FILES
# ==================================================

app.mount(
    "/static",
    StaticFiles(
        directory=BASE_DIR / "static"
    ),
    name="static"
)


# Compatibility for older templates/records
app.mount(
    "/uploads",
    StaticFiles(
        directory=BASE_DIR / "static" / "uploads"
    ),
    name="uploads"
)


# ==================================================
# UPLOADS PATH
# ==================================================

UPLOADS_PATH = (
    BASE_DIR /
    "static" /
    "uploads"
)

UPLOADS_PATH.mkdir(
    parents=True,
    exist_ok=True
)


# ==================================================
# VIDEO UPLOAD DIRECTORIES
# ==================================================

VIDEO_UPLOAD_DIR = (
    BASE_DIR /
    "static" /
    "uploads" /
    "videos"
)

THUMBNAIL_UPLOAD_DIR = (
    BASE_DIR /
    "static" /
    "uploads" /
    "thumbnails"
)

VIDEO_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

THUMBNAIL_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==================================================
# TEMPLATES
# ==================================================

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# ==================================================
# LOGIN PAGE
# ==================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
def login_page(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


# ==================================================
# REGISTER PAGE
# ==================================================

@app.get(
    "/register",
    response_class=HTMLResponse
)
def register_page(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


# ==================================================
# REGISTER
# ==================================================

@app.post("/register")
def register(

    full_name: str = Form(...),

    username: str = Form(...),

    email: str = Form(...),

    password: str = Form(...),

    role: str = Form(...),

    db: Session = Depends(get_db)

):

    full_name = full_name.strip()
    username = username.strip()
    email = email.strip().lower()
    password = password.strip()

    role_value = str(role).strip().lower()

    role_map = {
        "student": "student",
        "author": "author",

        "video_seller": "video_seller",
        "video seller": "video_seller",
        "video-seller": "video_seller",
        "videoseller": "video_seller",

        "seller": "seller"
    }

    normalized_role = role_map.get(
        role_value
    )

    allowed_roles = {
        "student",
        "author",
        "video_seller",
        "seller"
    }

    if normalized_role not in allowed_roles:
        return {
            "success": False,
            "message": "Invalid role selected"
        }

    existing_email = crud.get_user_by_email(
        db,
        email
    )

    if existing_email:
        return {
            "success": False,
            "message": "Email already exists"
        }

    existing_username = crud.get_user_by_username(
        db,
        username
    )

    if existing_username:
        return {
            "success": False,
            "message": "Username already exists"
        }

    try:

        user_data = RegisterUser(
            full_name=full_name,
            username=username,
            email=email,
            password=password,
            role=normalized_role
        )

        new_user = crud.create_user(
            db,
            user_data
        )

        if new_user:

            new_user.role = normalized_role

            db.commit()
            db.refresh(new_user)

    except Exception as e:

        db.rollback()

        print("====================================")
        print("REGISTRATION ERROR")
        print("====================================")
        print(type(e).__name__)
        print(str(e))
        print("====================================")

        return {
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }

    return RedirectResponse(
        "/",
        status_code=303
    )


# ==================================================
# LOGIN
# ==================================================

@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    user = crud.get_user_by_email(
        db,
        email.strip().lower()
    )

    if not user or user.password != password:

        return templates.TemplateResponse(
            name="login.html",
            request=request,
            context={
                "error": "Invalid email or password"
            },
            status_code=401
        )

    request.session["user_id"] = user.id
    request.session["email"] = user.email
    request.session["username"] = user.username
    request.session["full_name"] = user.full_name
    request.session["role"] = user.role

    user_role = str(
        user.role or ""
    ).strip().lower()

    user_role = (
        user_role
        .replace("_", " ")
        .replace("-", " ")
    )

    user_role = " ".join(
        user_role.split()
    )

    if user_role in [
        "student",
        "students"
    ]:

        return RedirectResponse(
            url=f"/student/{user.id}",
            status_code=303
        )

    elif user_role in [
        "author",
        "authors"
    ]:

        return RedirectResponse(
            url=f"/author/{user.id}",
            status_code=303
        )

    elif user_role in [
        "video seller",
        "video sellers",
        "videoseller",
        "videosellers",
        "seller"
    ]:

        return RedirectResponse(
            url="/video-seller",
            status_code=303
        )

    return templates.TemplateResponse(
        name="login.html",
        request=request,
        context={
            "error": "Invalid user role: " + str(user.role)
        },
        status_code=400
    )


# ==================================================
# AUTHOR DASHBOARD
# ==================================================

@app.get(
    "/author/{user_id}",
    response_class=HTMLResponse
)
def author_dashboard(

    user_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    user = db.query(
        models.User
    ).filter(
        models.User.id == user_id
    ).first()

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="author.html",
        context={
            "user": user
        }
    )


# ==================================================
# VIDEO SELLER DASHBOARD
# ==================================================

@app.get(
    "/video-seller",
    response_class=HTMLResponse
)
def video_seller_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:
        return RedirectResponse(
            url="/",
            status_code=303
        )

    user = crud.get_user_by_id(
        db,
        user_id
    )

    if not user:

        request.session.clear()

        return RedirectResponse(
            url="/",
            status_code=303
        )

    user_role = str(
        user.role or ""
    ).strip().lower()

    user_role = (
        user_role
        .replace("_", " ")
        .replace("-", " ")
    )

    user_role = " ".join(
        user_role.split()
    )

    if user_role not in [
        "video seller",
        "video sellers",
        "videoseller",
        "videosellers",
        "seller"
    ]:

        return RedirectResponse(
            url="/",
            status_code=303
        )

    videos = crud.get_seller_videos(
        db,
        user.id
    )

    statistics = crud.get_seller_video_statistics(
        db,
        user.id
    )

    return templates.TemplateResponse(
        name="seller.html",
        request=request,
        context={
            "user": user,
            "videos": videos,
            "statistics": statistics
        }
    )


# ==================================================
# AUTHOR STATS
# ==================================================

@app.get(
    "/author/{user_id}/stats"
)
def author_stats(
    user_id: int,
    db: Session = Depends(get_db)
):

    return crud.author_stats(
        db,
        user_id
    )


# ==================================================
# AUTHOR BOOKS
# ==================================================

@app.get(
    "/author/{user_id}/books"
)
def author_books(
    user_id: int,
    db: Session = Depends(get_db)
):

    books = crud.get_books_by_author(
        db,
        user_id
    )

    return [
        serialize_book(b)
        for b in books
    ]


# ==================================================
# AUTHOR ANALYTICS
# ==================================================

@app.get(
    "/author/{user_id}/analytics"
)
def author_analytics(
    user_id: int,
    db: Session = Depends(get_db)
):

    return crud.author_analytics(
        db,
        user_id
    )


# ==================================================
# AUTHOR COMMENTS
# ==================================================

@app.get(
    "/author/{user_id}/comments"
)
def author_comments(
    user_id: int,
    db: Session = Depends(get_db)
):

    return crud.get_author_comments(
        db,
        user_id
    )


# ==================================================
# STUDENT DASHBOARD
# ==================================================

@app.get(
    "/student/{user_id}",
    response_class=HTMLResponse
)
def student_dashboard(

    user_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    user = db.query(
        models.User
    ).filter(
        models.User.id == user_id
    ).first()

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="student.html",
        context={
            "user": user
        }
    )


# ==================================================
# WRITE BOOK PAGE
# ==================================================

@app.get(
    "/write-book",
    response_class=HTMLResponse
)
def write_book_page(
    request: Request,
    author_id: int = 0,
    book_id: int = 0
):

    return templates.TemplateResponse(
        request=request,
        name="book.html",
        context={
            "author_id": author_id,
            "book_id": book_id
        }
    )


# ==================================================
# SAVE BOOK
# ==================================================

@app.post("/books")
def create_book(

    book: BookCreate,

    db: Session = Depends(get_db)

):

    new_book = crud.create_book(
        db,
        book
    )

    return {
        "success": True,
        "message": "Book saved successfully",
        "book_id": new_book.id
    }


# ==================================================
# ALL BOOKS
# ==================================================

@app.get("/books")
def get_books(
    db: Session = Depends(get_db)
):

    books = crud.get_all_books(
        db
    )

    return [
        serialize_book(b)
        for b in books
    ]


# ==================================================
# SINGLE BOOK
# ==================================================

@app.get(
    "/book/{book_id}"
)
def get_single_book(

    book_id: int,

    db: Session = Depends(get_db)

):

    book = crud.get_book(
        db,
        book_id
    )

    if not book:
        return {
            "error": "Book not found"
        }

    return serialize_book(
        book
    )


# ==================================================
# SERIALIZE BOOK
# ==================================================

def serialize_book(b):

    return {

        "id": b.id,

        "title": b.title,

        "description": (
            b.description or ""
        ),

        "content": (
            b.content or ""
        ),

        "category": (
            b.category or ""
        ),

        "cover_image": (
            b.cover_image or ""
        ),

        "book_file": (
            getattr(
                b,
                "book_file",
                ""
            ) or ""
        ),

        "price": (
            b.price or 0
        ),

        "status": (
            b.status or "Draft"
        ),

        "author_id": b.author_id,

        "views": (
            b.views or 0
        ),

        "likes": (
            b.likes or 0
        ),

        "comments": (
            b.comments or 0
        ),

        "sales": (
            b.sales or 0
        ),

        "created_at": (
            b.created_at.isoformat()
            if b.created_at
            else ""
        ),

        "author_name": (
            b.author.full_name
            if b.author
            else "Unknown"
        )
    }


# ==================================================
# DELETE BOOK
# ==================================================

@app.delete(
    "/book/{book_id}"
)
def delete_book(

    book_id: int,

    db: Session = Depends(get_db)

):

    deleted = crud.delete_book(
        db,
        book_id
    )

    if not deleted:

        return {
            "success": False,
            "message": "Book not found"
        }

    return {
        "success": True,
        "message": "Book deleted successfully"
    }


# ==================================================
# BOOK COMMENTS
# ==================================================

@app.post("/comments")
def add_comment(

    comment: CommentCreate,

    db: Session = Depends(get_db)

):

    return crud.create_comment(
        db,
        comment
    )


# ==================================================
# AI ASSISTANT
# ==================================================

# ==================================================
# AI WRITING ASSISTANT ENGINE
# ==================================================

import re

def _clean_topic(text: str, remove_words: list) -> str:
    cleaned = text
    for w in remove_words:
        cleaned = re.sub(rf"(?i)\b{re.escape(w)}\b", "", cleaned)
    cleaned = re.sub(r"[^\w\s\-\:\.\,]", "", cleaned).strip()
    return cleaned if len(cleaned) > 2 else "your book topic"

def _matches_any(text: str, keywords: list) -> bool:
    for kw in keywords:
        if len(kw) <= 4:
            if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE):
                return True
        else:
            if kw.lower() in text.lower():
                return True
    return False

def _call_openrouter_for_book(message: str, context: dict | None = None) -> str:
    api_key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API")
    if not api_key:
        raise RuntimeError("OPENROUTER_API is not set")

    book_title = (context or {}).get("title") or "Untitled Book"
    book_category = (context or {}).get("category") or "General"

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are EduNote AI, a professional educational book-writing assistant. "
                    "Write polished, useful, author-friendly responses with clear structure, practical examples, "
                    "and engaging tone."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Book title: {book_title}\n"
                    f"Category: {book_category}\n\n"
                    f"User request: {message}\n\n"
                    "Write a strong response suitable for a book author. Be clear, practical, and engaging."
                )
            }
        ],
        "temperature": 0.7,
        "max_tokens": 700
    }

    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:8000",
            "X-Title": "EduNote"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    choices = result.get("choices") or []
    if not choices:
        raise ValueError("OpenRouter returned no choices")

    content = choices[0].get("message", {}).get("content")
    if isinstance(content, list):
        text = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
        )
    else:
        text = content or ""

    cleaned = str(text).strip()
    if not cleaned:
        raise ValueError("OpenRouter returned empty content")
    return cleaned


@app.post("/ai-chat")
def ai_chat(
    data: dict = Body(...)
):
    # Extract message from various possible key names
    raw_message = (
        data.get("message")
        or data.get("prompt")
        or data.get("text")
        or data.get("query")
        or data.get("content")
        or ""
    ).strip()

    context = data.get("context") or {}

    if OPENROUTER_API_KEY:
        try:
            generated_reply = _call_openrouter_for_book(raw_message, context)
            if generated_reply:
                return {"reply": generated_reply}
        except Exception as exc:  # pragma: no cover - graceful fallback if API fails
            print(f"[AI] OpenRouter request failed: {exc}")

    if not raw_message:
        return {
            "reply": (
                "👋 Hello! I am **EduNote AI** — your smart author and writing assistant.\n\n"
                "Here are things I can help you with:\n"
                "• 💡 **Suggest Titles** — *'Suggest titles for a Python programming book'*\n"
                "• 📖 **Chapter Outline** — *'Outline a 7-chapter book on Financial Literacy'*\n"
                "• ✍️ **Write Chapter / Intro** — *'Write Chapter 1 for a book about Space Exploration'*\n"
                "• ✨ **Improve Writing** — *'Improve this: The book has good stuff about AI.'*\n"
                "• 🛠 **Fix Grammar** — *'Fix grammar in: Their is many people who loves books.'*\n"
                "• 📝 **Summaries** — *'Summarize key principles of machine learning'*\n"
                "• ❓ **Generate Quizzes** — *'Create a 5-question quiz on World War 2'*\n"
                "• 💰 **Pricing & Marketing** — *'How should I price my educational eBook?'*\n\n"
                "What would you like to work on today?"
            )
        }

    # 1. CHAPTER OUTLINE & STRUCTURE (Checked early for high specificity)
    if _matches_any(raw_message, ["outline", "chapter outline", "structure", "table of contents", "toc", "plan my book", "book structure"]):
        topic = _clean_topic(raw_message, ["generate", "give", "me", "chapter", "outline", "outlines", "for", "a", "book", "about", "structure", "toc", "table", "of", "contents", "plan", "please"])
        return {
            "reply": (
                f"📖 **Complete Book Outline: {topic.title()}**\n\n"
                f"### **Part I: Foundations & Core Concepts**\n"
                f"• **Chapter 1: The Big Picture** — Introduction, importance of {topic.title()}, roadmap of what readers will master.\n"
                f"• **Chapter 2: Essential Fundamentals** — Key terms, historical context, and building blocks.\n"
                f"• **Chapter 3: Setting Up for Success** — Tools, environment, and mindset required.\n\n"
                f"### **Part II: Deep Dive & Core Techniques**\n"
                f"• **Chapter 4: Core Frameworks & Principles** — Step-by-step methodology and foundational mechanics.\n"
                f"• **Chapter 5: Practical Hands-on Walkthrough** — Real-world scenarios, worked examples, and best practices.\n"
                f"• **Chapter 6: Overcoming Common Pitfalls** — Mistakes beginners make, debugging, and troubleshooting.\n\n"
                f"### **Part III: Advanced Applications & Mastery**\n"
                f"• **Chapter 7: Advanced Strategies** — Optimization, scaling, and professional-level insights.\n"
                f"• **Chapter 8: Case Studies & Industry Applications** — How top practitioners apply {topic.title()}.\n"
                f"• **Chapter 9: The Future Horizon** — Emerging trends, continuing education, and summary.\n\n"
                f"💡 *Tip: Each chapter should open with a clear learning outcome and conclude with a quick summary and 3–5 review exercises!*"
            )
        }

    # 2. WRITE CHAPTER / WRITE CONTENT / INTRODUCTION
    if _matches_any(raw_message, ["write chapter", "draft chapter", "write intro", "write introduction", "draft introduction", "write about", "start writing"]):
        topic = _clean_topic(raw_message, ["write", "draft", "chapter", "intro", "introduction", "about", "for", "a", "book", "on", "please", "can", "you"])
        return {
            "reply": (
                f"✍️ **Draft Content: Introduction to {topic.title()}**\n\n"
                f"### Chapter 1: Unlocking {topic.title()}\n\n"
                f"Have you ever wondered why **{topic.title()}** plays such a transformative role in our modern world? "
                f"Whether you are just starting your journey or looking to sharpen your existing knowledge, mastering this subject opens doors to unprecedented opportunities.\n\n"
                f"#### **Why {topic.title()} Matters Today**\n"
                f"In today's fast-evolving landscape, understanding {topic.title()} is no longer just an optional advantage — it is an indispensable skill. "
                f"From solving complex problems to creating innovative solutions, the core principles provide a solid foundation for sustainable growth.\n\n"
                f"#### **Key Pillars You Will Master:**\n"
                f"1. **Core Understanding:** Establishing clarity on the foundational mechanics.\n"
                f"2. **Practical Execution:** Applying theoretical insights through actionable steps and exercises.\n"
                f"3. **Critical Problem Solving:** Developing the analytical mindset to tackle edge cases and challenges.\n\n"
                f"#### **Real-World Application**\n"
                f"Consider how leading organizations and experts leverage {topic.title()}. By breaking down complex challenges into modular, manageable components, "
                f"they consistently achieve higher efficiency and measurable outcomes.\n\n"
                f"> *“The journey of a thousand miles begins with a single step. As you progress through these pages, treat each concept as a stepping stone toward full mastery.”*\n\n"
                f"#### **Chapter Summary & Action Step:**\n"
                f"• Reflect on your primary goal with {topic.title()}.\n"
                f"• Keep a notebook for key takeaways as we move into Chapter 2!"
            )
        }

    # 3. TITLE SUGGESTIONS
    if _matches_any(raw_message, ["title", "name of book", "book name", "suggest title", "heading", "catchy name"]):
        topic = _clean_topic(raw_message, ["suggest", "title", "titles", "for", "a", "book", "about", "give", "me", "name", "names", "catchy", "please", "some", "good", "of"])
        return {
            "reply": (
                f"📚 **Title Ideas for '{topic.title()}':**\n\n"
                f"**🚀 Action & Bestseller Style:**\n"
                f"1. *Mastering {topic.title()}: The Definitive Step-by-Step Guide*\n"
                f"2. *The {topic.title()} Playbook: Practical Strategies for Success*\n"
                f"3. *Zero to Hero in {topic.title()}*\n\n"
                f"**🎯 Beginner & Educational:**\n"
                f"4. *Understanding {topic.title()} in 30 Days*\n"
                f"5. *The Absolute Beginner's Guide to {topic.title()}*\n"
                f"6. *{topic.title()} Explained Simply: Core Principles & Applications*\n\n"
                f"**💡 Creative & Intriguing:**\n"
                f"7. *Decoding {topic.title()}: Secrets, Frameworks, and Future Trends*\n"
                f"8. *Beyond the Basics: Advanced Insights into {topic.title()}*\n\n"
                f"💡 *Pro-Tip: Pair your title with a clear subtitle highlighting reader benefits (e.g. 'How to Learn Fast and Build Real-World Skills').*"
            )
        }

    # 4. GRAMMAR FIX & PROOFREADING
    if _matches_any(raw_message, ["grammar", "proofread", "spell check", "correct this", "fix grammar", "typo"]):
        return {
            "reply": (
                "✨ **Grammar & Polish Check:**\n\n"
                "**🔍 Analysis & Improvements:**\n"
                "• **Sentence Structure:** Converted passive voice to crisp active voice.\n"
                "• **Clarity & Flow:** Enhanced transitional phrases for a smoother reading rhythm.\n"
                "• **Punctuation:** Corrected comma splices and ensured proper capitalization.\n\n"
                "**📝 Recommended Polished Version:**\n"
                "> *\"Effective writing communicates ideas with clarity, precision, and confidence. By structuring each paragraph around a clear focal point and supporting it with compelling evidence, your readers remain engaged from start to finish.\"*\n\n"
                "💡 *Tip: Paste your specific draft text here, and I will proofread and polish it sentence-by-sentence!*"
            )
        }

    # 5. IMPROVE WRITING / STYLE POLISH
    if _matches_any(raw_message, ["improve writing", "rewrite", "enhance writing", "make better", "polish style", "writing tips"]):
        return {
            "reply": (
                "✨ **Writing Style Enhancements:**\n\n"
                "Here are proven techniques to elevate your prose:\n\n"
                "1. **Use Stronger Action Verbs:**\n"
                "   • *Instead of:* 'He made a decision to start'\n"
                "   • *Write:* 'He decided to start' or 'He launched'\n\n"
                "2. **Eliminate Filler Words:**\n"
                "   • Cut 'really', 'very', 'basically', 'in order to', 'due to the fact that'.\n\n"
                "3. **Vary Sentence Length:**\n"
                "   • Mix punchy short sentences with descriptive longer ones to create a dynamic reading cadence.\n\n"
                "4. **Show, Don't Just Tell:**\n"
                "   • Provide concrete sensory details and data rather than vague generalizations.\n\n"
                "Paste any excerpt from your chapter, and I'll generate three stylistic variations (Professional, Conversational, Academic)!"
            )
        }

    # 6. QUIZ & EXERCISE GENERATION
    if _matches_any(raw_message, ["quiz", "question", "questions", "exercise", "test", "assessment", "mcq"]):
        topic = _clean_topic(raw_message, ["generate", "create", "quiz", "quizzes", "question", "questions", "on", "for", "about", "mcq", "test", "please"])
        return {
            "reply": (
                f"❓ **Interactive Chapter Quiz: {topic.title()}**\n\n"
                f"**Q1. (Multiple Choice)** What is the primary objective of understanding {topic.title()} in modern practice?\n"
                f"• A) To memorize theoretical formulas without application\n"
                f"• B) To establish a structured foundation for solving complex real-world problems *(Correct)*\n"
                f"• C) To replace all traditional methodologies immediately\n"
                f"• D) To minimize collaboration among team members\n\n"
                f"**Q2. (True / False)**\n"
                f"True or False: Consistent iteration and review significantly enhance long-term mastery of {topic.title()}.\n"
                f"*Answer: True — Feedback loops reinforce core understanding.*\n\n"
                f"**Q3. (Scenario Based)**\n"
                f"Imagine a practitioner encountering an unexpected error when applying {topic.title()}. What is the recommended first diagnostic step?\n"
                f"*Answer: Isolate the variable, inspect the input parameters, and cross-reference foundational assumptions.*\n\n"
                f"**Q4. (Short Answer)**\n"
                f"State two core advantages that distinguished practitioners gain from mastering {topic.title()}.\n\n"
                f"💡 *Tip: Adding 3–5 interactive questions at the end of each chapter increases student completion rates by over 40%!*"
            )
        }

    # 7. SUMMARY & CONCLUSION
    if _matches_any(raw_message, ["summary", "summarize", "conclusion", "recap", "wrap up", "key takeaways"]):
        topic = _clean_topic(raw_message, ["generate", "summary", "summarize", "conclusion", "recap", "of", "for", "about", "key", "takeaways", "please"])
        return {
            "reply": (
                f"📝 **Executive Summary & Key Takeaways: {topic.title()}**\n\n"
                f"### **Core Highlights:**\n"
                f"1. **Primary Premise:** {topic.title()} serves as a critical pillar, enabling structured problem solving and repeatable success.\n"
                f"2. **Actionable Methodology:** Focus on consistent, modular execution rather than overwhelming monolithic overhauls.\n"
                f"3. **Long-Term Impact:** Understanding the underlying mechanics empowers learners to adapt effortlessly to future advancements.\n\n"
                f"### **Chapter Closing Hook:**\n"
                f"> *\"Now that you possess a thorough command of these essential concepts, we are ready to advance to the next level of practical execution in Chapter 2.\"*\n\n"
                f"💡 *Use this summary template at the end of your chapter to solidify student learning!*"
            )
        }

    # 8. PRICING & MONETIZATION
    if _matches_any(raw_message, ["price", "pricing", "monetize", "how much", "sell", "cost", "free vs paid", "payment"]):
        return {
            "reply": (
                "💰 **EduNote Book Pricing & Monetization Strategy:**\n\n"
                "**Recommended Pricing Tiers:**\n"
                "• **🆓 Free (₹0):** Perfect for introductory guides, cheat sheets, and course samples. Generates high view counts and builds an eager student following.\n"
                "• **🥉 ₹49 – ₹149 (Short Guides & Notes):** Quick-reference materials, exam preparation summaries, and focused tutorials.\n"
                "• **🥈 ₹199 – ₹399 (Standard Books):** Comprehensive 5–10 chapter handbooks with practical exercises and deep insights.\n"
                "• **🥇 ₹499 – ₹999+ (Masterclasses & Bundles):** Professional curriculum, full code repos, and advanced certification material.\n\n"
                "**💡 Pro Monetization Tips:**\n"
                "1. Publish your first chapter or a companion cheat sheet for **Free** to gain reviews.\n"
                "2. Offer paid content with multiple payment methods (UPI, Card, Net Banking) for friction-free student checkout.\n"
                "3. Track your real-time earnings and sales analytics right inside your Author Dashboard!"
            )
        }

    # 9. CONTINUE PARAGRAPH / EXPAND
    if _matches_any(raw_message, ["continue", "expand", "next section", "continue paragraph", "keep writing"]):
        return {
            "reply": (
                "✍️ **Seamless Paragraph Continuation:**\n\n"
                "Building upon these foundational principles, the next crucial step is translating concept into execution. "
                "When we look closer at practical scenarios, several defining patterns immediately emerge.\n\n"
                "First, consistency in application guarantees steady progress, preventing the common trap of cognitive overload. "
                "Furthermore, by analyzing real-world feedback loops, we can iterate rapidly, refining our approach and eliminating unnecessary friction.\n\n"
                "Consequently, the practitioner who embraces this structured methodology will notice measurable improvements in clarity, retention, and final output.\n\n"
                "💡 *Feel free to click 'Insert into Book' to append this directly to your Quill editor!*"
            )
        }

    # 10. GREETING & GENERAL HELP
    if _matches_any(raw_message, ["hello", "hi", "hey", "who are you", "what can you do", "help me", "start"]):
        return {
            "reply": (
                "👋 **Hello Author! I am EduNote AI — your personal creative assistant.**\n\n"
                "I'm here to help you brainstorm, write, outline, edit, and publish outstanding books and educational material.\n\n"
                "**Quick Actions you can try:**\n"
                "• 💡 **Suggest Titles** (e.g. *'Suggest titles for a Data Science handbook'*)\n"
                "• 📖 **Outline Chapters** (e.g. *'Generate chapter outline for Python Web Dev'*)\n"
                "• ✍️ **Draft Content** (e.g. *'Write an introduction on Climate Change'*)\n"
                "• ✨ **Improve & Polish** (Paste any paragraph to enhance flow and vocabulary)\n"
                "• ❓ **Create Quiz** (e.g. *'Generate multiple choice quiz on Biology'*)\n\n"
                "Tell me what you're working on!"
            )
        }

    # 11. GENERAL CONTEXTUAL KNOWLEDGE / WRITING PROMPT
    topic = _clean_topic(raw_message, ["what", "is", "how", "to", "explain", "tell", "me", "about", "can", "you", "why", "does"])
    return {
        "reply": (
            f"💡 **Insights on {topic.title()}:**\n\n"
            f"### **Overview & Concept**\n"
            f"**{topic.title()}** is a pivotal subject in modern learning and creative exploration. "
            f"When presenting this to your readers, structuring the discussion logically ensures maximum engagement.\n\n"
            f"### **3 Key Angles to Cover in Your Book:**\n"
            f"1. **The Fundamental Concept:** Clearly define the core ideas without unnecessary jargon.\n"
            f"2. **Practical Real-World Example:** Illustrate with an intuitive case study that readers can relate to.\n"
            f"3. **Actionable Takeaway:** Give readers a direct exercise or reflection question to test their understanding.\n\n"
            f"### **Suggested Chapter Excerpt:**\n"
            f"> *\"To truly master {topic.title()}, one must look beyond surface-level mechanics and understand the underlying dynamics that drive meaningful outcomes.\"*\n\n"
            f"Would you like me to:\n"
            f"• ✍️ **Draft a full section** on this?\n"
            f"• 💡 **Suggest chapter titles** around this topic?\n"
            f"• ❓ **Create a 5-question quiz** for your students?"
        )
    }


# ==================================================
# MY BOOKS PAGE
# ==================================================

@app.get(
    "/my-books",
    response_class=HTMLResponse
)
def my_books_page(

    request: Request,

    author_id: int = 0

):

    return templates.TemplateResponse(
        request=request,
        name="my_book.html",
        context={
            "author_id": author_id
        }
    )


# ==================================================
# ANALYTICS PAGE
# ==================================================

@app.get(
    "/analytics/{user_id}",
    response_class=HTMLResponse
)
def analytics_page(

    user_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    user = db.query(
        models.User
    ).filter(
        models.User.id == user_id
    ).first()

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={
            "user": user
        }
    )


# ==================================================
# COMMENTS PAGE
# ==================================================

@app.get(
    "/comments/{user_id}",
    response_class=HTMLResponse
)
def comments_page(

    user_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    user = db.query(
        models.User
    ).filter(
        models.User.id == user_id
    ).first()

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="comments.html",
        context={
            "user": user
        }
    )


# ==================================================
# EARNINGS PAGE
# ==================================================

@app.get(
    "/earnings/{user_id}",
    response_class=HTMLResponse
)
def earnings_page(

    user_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    user = db.query(
        models.User
    ).filter(
        models.User.id == user_id
    ).first()

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="earnings.html",
        context={
            "user": user
        }
    )


# ==================================================
# PROFILE PAGE
# ==================================================

@app.get(
    "/profile/{user_id}",
    response_class=HTMLResponse
)
def profile_page(

    user_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    user = db.query(
        models.User
    ).filter(
        models.User.id == user_id
    ).first()

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user
        }
    )


# ==================================================
# LOGOUT
# ==================================================

@app.get("/logout")
def logout(
    request: Request
):

    request.session.clear()

    return RedirectResponse(
        "/",
        status_code=303
    )


# ==================================================
# BOOK READER PAGE
# ==================================================

@app.get(
    "/read/{book_id}",
    response_class=HTMLResponse
)
def read_book_page(

    book_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    book = crud.get_book(
        db,
        book_id
    )

    if not book:

        return RedirectResponse(
            "/",
            status_code=303
        )

    comments = crud.get_comments_with_users(
        db,
        book_id
    )

    user_id = request.query_params.get(
        "user_id",
        0
    )

    return templates.TemplateResponse(
        request=request,
        name="reader.html",
        context={
            "book": book,
            "comments": comments,
            "user_id": (
                int(user_id)
                if str(user_id).isdigit()
                else 0
            )
        }
    )


# ==================================================
# STUDENT STATS
# ==================================================

@app.get(
    "/student/{user_id}/stats"
)
def student_stats(

    user_id: int,

    db: Session = Depends(get_db)

):

    return crud.get_student_stats(
        db,
        user_id
    )


# ==================================================
# ALL PUBLISHED BOOKS
# ==================================================

@app.get(
    "/published-books"
)
def published_books(

    db: Session = Depends(get_db)

):

    books = crud.get_published_books(
        db
    )

    return [
        serialize_book(b)
        for b in books
    ]


# ==================================================
# BOOK COMMENTS
# ==================================================

@app.get(
    "/book/{book_id}/comments"
)
def get_book_comments(

    book_id: int,

    db: Session = Depends(get_db)

):

    return crud.get_comments_with_users(
        db,
        book_id
    )


# ==================================================
# STUDENT PROFILE UPDATE
# ==================================================

@app.get(
    "/student-profile/{user_id}",
    response_class=HTMLResponse
)
def student_profile_page(

    user_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    user = db.query(
        models.User
    ).filter(
        models.User.id == user_id
    ).first()

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="student_profile.html",
        context={
            "user": user
        }
    )


# ==================================================
# API BOOKS
# ==================================================

@app.get(
    "/api/books"
)
def api_books(

    db: Session = Depends(get_db)

):

    books = crud.get_all_books(
        db
    )

    return [
        serialize_book(b)
        for b in books
    ]


# ==================================================
# UPLOAD BOOK
# ==================================================

@app.post("/upload-book")
async def upload_book(

    title: str = Form(...),

    description: str = Form(""),

    category: str = Form(""),

    price: float = Form(0),

    author_id: int = Form(...),

    cover: UploadFile = File(None),

    book_file: UploadFile = File(None),

    db: Session = Depends(get_db)

):

    cover_name = ""

    if cover:
        cover_name = cover.filename

    file_name = ""

    if book_file:
        file_name = book_file.filename

    new_book = models.Book(

        title=title,

        description=description,

        content="",

        category=category,

        cover_image=cover_name,

        book_file=file_name,

        price=price,

        status="Published",

        author_id=author_id

    )

    db.add(new_book)

    db.commit()

    db.refresh(new_book)

    return {

        "success": True,

        "message": "Book uploaded successfully",

        "book": new_book.id

    }


# ==================================================
# UPDATE BOOK
# ==================================================

@app.put(
    "/book/{book_id}"
)
def update_book(

    book_id: int,

    title: str = Form(...),

    description: str = Form(...),

    category: str = Form(...),

    price: float = Form(...),

    db: Session = Depends(get_db)

):

    book = crud.update_book(

        db,

        book_id,

        title,

        description,

        category,

        price

    )

    if not book:

        return {

            "success": False,

            "message": "Book not found"

        }

    return {

        "success": True,

        "message": "Book updated"

    }


# ==================================================
# BOOK VIEW
# ==================================================

@app.post(
    "/book/{book_id}/view"
)
def increase_view(

    book_id: int,

    db: Session = Depends(get_db)

):

    crud.increase_view(
        db,
        book_id
    )

    book = crud.get_book(
        db,
        book_id
    )

    return {
        "success": True,
        "views": (
            book.views
            if book
            else 0
        )
    }


# ==================================================
# BOOK LIKE
# ==================================================

@app.post(
    "/book/{book_id}/like"
)
def like_book(

    book_id: int,

    db: Session = Depends(get_db)

):

    crud.like_book(
        db,
        book_id
    )

    book = crud.get_book(
        db,
        book_id
    )

    return {
        "success": True,
        "likes": (
            book.likes
            if book
            else 0
        )
    }


# ==================================================
# VIDEO URL HELPERS
# ==================================================

def normalize_video_url(filename):

    if not filename:
        return ""

    raw = str(filename).strip()

    if not raw:
        return ""

    if (
        raw.startswith("http://")
        or
        raw.startswith("https://")
    ):
        return raw

    raw = raw.replace(
        "\\",
        "/"
    )

    while raw.startswith("//"):
        raw = raw[1:]

    if raw.startswith(
        "/static/uploads/videos/"
    ):
        return raw

    if raw.startswith(
        "static/uploads/videos/"
    ):
        return "/" + raw

    if raw.startswith(
        "/uploads/videos/"
    ):
        return "/static" + raw

    if raw.startswith(
        "uploads/videos/"
    ):
        return "/static/" + raw

    while raw.startswith(
        "/static/static/"
    ):
        raw = raw[len("/static/"):]

    if raw.startswith(
        "static/static/"
    ):
        raw = raw[len("static/"):]

    if raw.startswith(
        "/static/uploads/"
    ):
        return raw

    if raw.startswith(
        "static/uploads/"
    ):
        return "/" + raw

    filename_only = Path(
        raw
    ).name

    if not filename_only:
        return ""

    return (
        "/static/uploads/videos/"
        + filename_only
    )


# ==================================================
# THUMBNAIL URL HELPER
# ==================================================

def normalize_thumbnail_url(thumbnail):

    if not thumbnail:
        return ""

    raw = str(thumbnail).strip()

    if not raw:
        return ""

    if (
        raw.startswith("http://")
        or
        raw.startswith("https://")
    ):
        return raw

    raw = raw.replace(
        "\\",
        "/"
    )

    while raw.startswith("//"):
        raw = raw[1:]

    if raw.startswith(
        "/static/uploads/thumbnails/"
    ):
        return raw

    if raw.startswith(
        "static/uploads/thumbnails/"
    ):
        return "/" + raw

    if raw.startswith(
        "/uploads/thumbnails/"
    ):
        return "/static" + raw

    if raw.startswith(
        "uploads/thumbnails/"
    ):
        return "/static/" + raw

    filename_only = Path(
        raw
    ).name

    if not filename_only:
        return ""

    return (
        "/static/uploads/thumbnails/"
        + filename_only
    )


# ==================================================
# VIDEO COMMENT COUNT
# ==================================================

def get_video_comment_count(
    db: Session,
    video_id: int
):

    try:

        return db.query(
            models.VideoComment
        ).filter(
            models.VideoComment.video_id == video_id
        ).count()

    except Exception as e:

        print(
            "VIDEO COMMENT COUNT ERROR:",
            e
        )

        return 0


# ==================================================
# VIDEO TO DICT
# ==================================================

def video_to_dict(
    video,
    db: Session = None
):

    video_url = normalize_video_url(
        video.filename
    )

    thumbnail_url = normalize_thumbnail_url(
        video.thumbnail
    )

    seller_data = None

    if video.seller:

        seller_data = {

            "id": video.seller.id,

            "full_name": (
                video.seller.full_name
            )

        }

    comment_count = 0

    if db is not None:

        comment_count = get_video_comment_count(
            db,
            video.id
        )

    else:

        try:

            comment_count = len(
                video.video_comments
            )

        except Exception:

            comment_count = (
                getattr(
                    video,
                    "comments",
                    0
                )
                or 0
            )

    return {

        "id": video.id,

        "title": video.title,

        "description": (
            video.description or ""
        ),

        "category": (
            video.category or ""
        ),

        "price": (
            video.price or 0
        ),

        "filename": video_url,

        "video": video_url,

        "thumbnail": thumbnail_url,

        "duration": (
            video.duration or ""
        ),

        "status": (
            video.status or "Published"
        ),

        "seller_id": video.seller_id,

        "seller_name": (
            video.seller.full_name
            if video.seller
            else "EduNote Seller"
        ),

        "seller": seller_data,

        "views": (
            video.views or 0
        ),

        "likes": (
            video.likes or 0
        ),

        "comments": comment_count,

        "sales": (
            video.sales or 0
        ),

        "created_at": (
            video.created_at.isoformat()
            if video.created_at
            else ""
        )
    }


# ==================================================
# VIDEO TEMPLATE CONTEXT
# ==================================================

def video_template_context(
    video,
    db: Session = None
):

    return video_to_dict(
        video,
        db
    )


# ==================================================
# VIDEO SELLER API
# ==================================================

@app.get(
    "/seller/{seller_id}/videos"
)
def get_seller_videos_api(

    seller_id: int,

    db: Session = Depends(get_db)

):

    videos = crud.get_seller_videos(
        db,
        seller_id
    )

    return [
        video_to_dict(
            video,
            db
        )
        for video in videos
    ]


# ==================================================
# ALL PUBLISHED VIDEOS
# ==================================================

@app.get(
    "/videos"
)
def get_all_published_videos(

    db: Session = Depends(get_db)

):

    try:

        videos = crud.get_published_videos(
            db
        )

    except Exception as e:

        print(
            "GET PUBLISHED VIDEOS ERROR:",
            e
        )

        videos = db.query(
            models.Video
        ).filter(
            models.Video.status == "Published"
        ).order_by(
            models.Video.created_at.desc()
        ).all()

    return [
        video_to_dict(
            video,
            db
        )
        for video in videos
    ]


# ==================================================
# UPLOAD VIDEO
# ==================================================

@app.post(
    "/seller/{seller_id}/videos/upload"
)
async def upload_seller_video(

    seller_id: int,

    title: str = Form(...),

    description: str = Form(""),

    category: str = Form(""),

    price: float = Form(0),

    duration: str = Form(""),

    video: UploadFile = File(...),

    thumbnail: UploadFile = File(None),

    db: Session = Depends(get_db)

):

    seller = db.query(
        models.User
    ).filter(
        models.User.id == seller_id
    ).first()

    if not seller:

        raise HTTPException(
            status_code=404,
            detail="Seller not found"
        )

    if not video:

        raise HTTPException(
            status_code=400,
            detail="Video file is required"
        )

    original_video_name = (
        video.filename or ""
    ).strip()

    if not original_video_name:

        raise HTTPException(
            status_code=400,
            detail="Invalid video file"
        )

    video_extension = Path(
        original_video_name
    ).suffix.lower()

    allowed_video_extensions = {
        ".mp4",
        ".webm",
        ".mov",
        ".avi",
        ".mkv",
        ".m4v"
    }

    if video_extension not in allowed_video_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported video format. "
                "Use MP4, WebM, MOV, AVI, MKV or M4V."
            )
        )

    video_filename = (
        uuid.uuid4().hex
        + video_extension
    )

    video_path = (
        VIDEO_UPLOAD_DIR
        / video_filename
    )

    try:

        with open(
            video_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                video.file,
                buffer
            )

    except Exception as e:

        print(
            "VIDEO SAVE ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to save video file"
        )

    thumbnail_filename = ""

    if thumbnail and thumbnail.filename:

        original_thumbnail_name = (
            thumbnail.filename.strip()
        )

        thumbnail_extension = Path(
            original_thumbnail_name
        ).suffix.lower()

        allowed_thumbnail_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif"
        }

        if (
            thumbnail_extension
            not in allowed_thumbnail_extensions
        ):

            try:

                if video_path.exists():
                    video_path.unlink()

            except Exception:
                pass

            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported thumbnail format. "
                    "Use JPG, JPEG, PNG, WEBP or GIF."
                )
            )

        thumbnail_filename = (
            uuid.uuid4().hex
            + thumbnail_extension
        )

        thumbnail_path = (
            THUMBNAIL_UPLOAD_DIR
            / thumbnail_filename
        )

        try:

            with open(
                thumbnail_path,
                "wb"
            ) as buffer:

                shutil.copyfileobj(
                    thumbnail.file,
                    buffer
                )

        except Exception as e:

            print(
                "THUMBNAIL SAVE ERROR:",
                str(e)
            )

            try:

                if video_path.exists():
                    video_path.unlink()

            except Exception:
                pass

            raise HTTPException(
                status_code=500,
                detail="Unable to save thumbnail"
            )

    stored_video_path = (
        "uploads/videos/"
        + video_filename
    )

    stored_thumbnail_path = ""

    if thumbnail_filename:

        stored_thumbnail_path = (
            "uploads/thumbnails/"
            + thumbnail_filename
        )

    try:

        new_video = models.Video(

            title=title.strip(),

            description=description.strip(),

            category=category.strip(),

            price=price,

            filename=stored_video_path,

            thumbnail=stored_thumbnail_path,

            duration=duration.strip(),

            status="Published",

            seller_id=seller_id,

            views=0,

            likes=0,

            sales=0

        )

        db.add(new_video)

        db.commit()

        db.refresh(new_video)

    except Exception as e:

        db.rollback()

        print("====================================")
        print("VIDEO DATABASE ERROR")
        print("====================================")
        print(type(e).__name__)
        print(str(e))
        print("====================================")

        try:

            if video_path.exists():
                video_path.unlink()

        except Exception:
            pass

        if thumbnail_filename:

            try:

                thumbnail_path = (
                    THUMBNAIL_UPLOAD_DIR
                    / thumbnail_filename
                )

                if thumbnail_path.exists():
                    thumbnail_path.unlink()

            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail=(
                "Video could not be saved to database: "
                + str(e)
            )
        )

    return {

        "success": True,

        "message": "Video uploaded successfully",

        "video": video_to_dict(
            new_video,
            db
        )

    }

# ============================================================
# VIDEO WATCH ROUTE - STUDENT COMPATIBILITY
# ============================================================
# Student section currently opens:
# /video/{video_id}?student_id={student_id}
#
# Keep /watch/{video_id} working too.
# This route fixes the existing 404 error without changing
# the student frontend.

@app.get(
    "/video/{video_id}",
    response_class=HTMLResponse
)
def student_video_page(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    video = db.query(
        models.Video
    ).filter(
        models.Video.id == video_id
    ).first()

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    # --------------------------------------------------------
    # Get student ID from session or query parameter
    # --------------------------------------------------------

    student_id = request.session.get(
        "user_id"
    )

    if not student_id:

        student_id = request.query_params.get(
            "student_id"
        )

    # --------------------------------------------------------
    # Increase view
    # --------------------------------------------------------

    try:

        video.views = (
            video.views or 0
        ) + 1

        db.commit()
        db.refresh(video)

    except Exception as e:

        db.rollback()

        print(
            "VIDEO VIEW ERROR:",
            e
        )

    video_data = video_to_dict(
        video
    )

    return templates.TemplateResponse(

        request=request,

        name="videowatch.html",

        context={

            "video": video,

            "video_data": video_data,

            "user": video.seller,

            "student_id": (
                int(student_id)
                if str(student_id).isdigit()
                else 0
            )

        }

    )
# ==================================================
# WATCH VIDEO PAGE
# ==================================================

@app.get(
    "/watch/{video_id}",
    response_class=HTMLResponse
)
def watch_video(

    video_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    video = db.query(
        models.Video
    ).filter(
        models.Video.id == video_id
    ).first()

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    user_id = request.session.get(
        "user_id"
    ) or request.query_params.get(
        "user_id"
    )

    try:

        video.views = (
            video.views or 0
        ) + 1

        db.commit()

    except Exception as e:

        db.rollback()

        print(
            "VIDEO VIEW ERROR:",
            e
        )

    video_data = video_to_dict(
        video,
        db
    )

    return templates.TemplateResponse(
        request=request,
        name="videowatch.html",
        context={
            "video": video,
            "video_data": video_data,
            "user": video.seller,
            "user_id": (
                int(user_id)
                if str(user_id).isdigit()
                else 0
            )
        }
    )


# ==================================================
# VIDEO FILE
# ==================================================

@app.get(
    "/video/{video_id}/file"
)
def get_video_file(

    video_id: int,

    db: Session = Depends(get_db)

):

    video = db.query(
        models.Video
    ).filter(
        models.Video.id == video_id
    ).first()

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    video_url = normalize_video_url(
        video.filename
    )

    if not video_url:

        raise HTTPException(
            status_code=404,
            detail="Video file not found"
        )

    return {

        "success": True,

        "video_url": video_url

    }


# ==================================================
# VIDEO VIEW API
# ==================================================

@app.post(
    "/video/{video_id}/view"
)
def increase_video_view(

    video_id: int,

    db: Session = Depends(get_db)

):

    video = db.query(
        models.Video
    ).filter(
        models.Video.id == video_id
    ).first()

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    try:

        video.views = (
            video.views or 0
        ) + 1

        db.commit()
        db.refresh(video)

    except Exception as e:

        db.rollback()

        print(
            "VIDEO VIEW API ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not update video views"
        )

    return {

        "success": True,

        "views": (
            video.views or 0
        )

    }


# ==================================================
# VIDEO LIKE
# ==================================================

@app.post(
    "/video/{video_id}/like"
)
def like_video(

    video_id: int,

    db: Session = Depends(get_db)

):

    video = db.query(
        models.Video
    ).filter(
        models.Video.id == video_id
    ).first()

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    try:

        video.likes = (
            video.likes or 0
        ) + 1

        db.commit()
        db.refresh(video)

    except Exception as e:

        db.rollback()

        print(
            "VIDEO LIKE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not like video"
        )

    return {

        "success": True,

        "message": "Video liked successfully",

        "likes": (
            video.likes or 0
        )

    }


# ==================================================
# VIDEO COMMENTS
# ==================================================

@app.get(
    "/video/{video_id}/comments"
)
def get_video_comments(

    video_id: int,

    db: Session = Depends(get_db)

):

    video = db.query(
        models.Video
    ).filter(
        models.Video.id == video_id
    ).first()

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    comments = db.query(
        models.VideoComment
    ).filter(
        models.VideoComment.video_id == video_id
    ).order_by(
        models.VideoComment.created_at.asc()
    ).all()

    result = []

    for comment in comments:

        result.append({

            "id": comment.id,

            "video_id": comment.video_id,

            "user_id": comment.user_id,

            "text": comment.text,

            "comment": comment.text,

            "content": comment.text,

            "user_name": (
                comment.user.full_name
                if comment.user
                else "User"
            ),

            "username": (
                comment.user.username
                if comment.user
                else "User"
            ),

            "created_at": (
                comment.created_at.isoformat()
                if comment.created_at
                else ""
            )

        })

    return result


# ==================================================
# ADD VIDEO COMMENT
# ==================================================

@app.post(
    "/video/{video_id}/comments"
)
def add_video_comment(

    video_id: int,

    request: Request,

    data: dict = Body(...),

    db: Session = Depends(get_db)

):

    # ------------------------------------------------
    # CHECK VIDEO
    # ------------------------------------------------

    video = db.query(
        models.Video
    ).filter(
        models.Video.id == video_id
    ).first()

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    # ------------------------------------------------
    # COMMENT TEXT
    # ------------------------------------------------

    comment_text = str(
        data.get(
            "comment",
            data.get(
                "text",
                data.get(
                    "content",
                    ""
                )
            )
        )
    ).strip()

    if not comment_text:

        raise HTTPException(
            status_code=400,
            detail="Comment cannot be empty"
        )

    # ------------------------------------------------
    # USER
    # ------------------------------------------------

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        user_id = data.get(
            "user_id"
        )

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Please login before commenting"
        )

    try:

        user_id = int(
            user_id
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid user ID"
        )

    user = db.query(
        models.User
    ).filter(
        models.User.id == user_id
    ).first()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    # ------------------------------------------------
    # SAVE COMMENT
    # ------------------------------------------------

    try:

        new_comment = models.VideoComment(

            video_id=video_id,

            user_id=user_id,

            text=comment_text

        )

        db.add(
            new_comment
        )

        db.commit()

        db.refresh(
            new_comment
        )

    except Exception as e:

        db.rollback()

        print("====================================")
        print("VIDEO COMMENT ERROR")
        print("====================================")
        print(type(e).__name__)
        print(str(e))
        print("====================================")

        raise HTTPException(
            status_code=500,
            detail="Could not save comment"
        )

    comment_count = get_video_comment_count(
        db,
        video_id
    )

    return {

        "success": True,

        "message": "Comment added successfully",

        "comments": comment_count,

        "comment_count": comment_count,

        "comment": {

            "id": new_comment.id,

            "video_id": new_comment.video_id,

            "user_id": new_comment.user_id,

            "text": new_comment.text,

            "comment": new_comment.text,

            "content": new_comment.text,

            "user_name": user.full_name,

            "username": user.username,

            "created_at": (
                new_comment.created_at.isoformat()
                if new_comment.created_at
                else ""
            )

        }

    }


# ==================================================
# DELETE VIDEO COMMENT
# ==================================================

@app.delete(
    "/video/{video_id}/comments/{comment_id}"
)
def delete_video_comment(

    video_id: int,

    comment_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    comment = db.query(
        models.VideoComment
    ).filter(
        models.VideoComment.id == comment_id,
        models.VideoComment.video_id == video_id
    ).first()

    if not comment:

        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )

    if int(comment.user_id) != int(user_id):

        raise HTTPException(
            status_code=403,
            detail="You can delete only your own comment"
        )

    try:

        db.delete(
            comment
        )

        db.commit()

    except Exception as e:

        db.rollback()

        print(
            "DELETE VIDEO COMMENT ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not delete comment"
        )

    return {

        "success": True,

        "message": "Comment deleted successfully",

        "comments": get_video_comment_count(
            db,
            video_id
        )

    }


# ==================================================
# VIDEO NOTES
# ==================================================

@app.get(
    "/video/{video_id}/notes"
)
def get_video_notes(

    video_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    video = db.query(
        models.Video
    ).filter(
        models.Video.id == video_id
    ).first()

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        user_id = request.query_params.get(
            "user_id"
        )

    if not user_id:

        return []

    try:

        user_id = int(
            user_id
        )

    except Exception:

        return []

    notes = db.query(
        models.VideoNote
    ).filter(
        models.VideoNote.video_id == video_id,
        models.VideoNote.student_id == user_id
    ).order_by(
        models.VideoNote.created_at.asc()
    ).all()

    return [

        {

            "id": note.id,

            "video_id": note.video_id,

            "student_id": note.student_id,

            "timestamp": (
                note.timestamp or "00:00"
            ),

            "content": (
                note.content or ""
            ),

            "text": (
                note.content or ""
            ),

            "note": (
                note.content or ""
            ),

            "created_at": (
                note.created_at.isoformat()
                if note.created_at
                else ""
            )

        }

        for note in notes

    ]


# ==================================================
# ADD VIDEO NOTE
# ==================================================

@app.post(
    "/video/{video_id}/notes"
)
def add_video_note(

    video_id: int,

    request: Request,

    data: dict = Body(...),

    db: Session = Depends(get_db)

):

    video = db.query(
        models.Video
    ).filter(
        models.Video.id == video_id
    ).first()

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    student_id = request.session.get(
        "user_id"
    )

    if not student_id:

        student_id = data.get(
            "student_id"
        )

    if not student_id:

        raise HTTPException(
            status_code=401,
            detail="Please login before saving notes"
        )

    try:

        student_id = int(
            student_id
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid student ID"
        )

    student = db.query(
        models.User
    ).filter(
        models.User.id == student_id
    ).first()

    if not student:

        raise HTTPException(
            status_code=401,
            detail="Student not found"
        )

    content = str(
        data.get(
            "content",
            data.get(
                "text",
                data.get(
                    "note",
                    ""
                )
            )
        )
    ).strip()

    if not content:

        raise HTTPException(
            status_code=400,
            detail="Note cannot be empty"
        )

    timestamp = str(
        data.get(
            "timestamp",
            data.get(
                "time",
                "00:00"
            )
        )
    ).strip()

    if not timestamp:

        timestamp = "00:00"

    try:

        new_note = models.VideoNote(

            video_id=video_id,

            student_id=student_id,

            timestamp=timestamp,

            content=content

        )

        db.add(
            new_note
        )

        db.commit()

        db.refresh(
            new_note
        )

    except Exception as e:

        db.rollback()

        print(
            "VIDEO NOTE SAVE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not save video note"
        )

    return {

        "success": True,

        "message": "Note saved successfully",

        "note": {

            "id": new_note.id,

            "video_id": new_note.video_id,

            "student_id": new_note.student_id,

            "timestamp": new_note.timestamp,

            "content": new_note.content,

            "text": new_note.content,

            "note": new_note.content,

            "created_at": (
                new_note.created_at.isoformat()
                if new_note.created_at
                else ""
            )

        }

    }

@app.post("/video-notes/{video_id}/{student_id}")
def save_video_note_compatibility(
    video_id: int,
    student_id: int,
    data: dict = Body(default={}),
    db: Session = Depends(get_db)
):
    timestamp = data.get("timestamp", "0:00")
    content = data.get("content", "")

    if not content or not str(content).strip():
        raise HTTPException(
            status_code=400,
            detail="Note content cannot be empty"
        )

    note = crud.save_video_note(
        db,
        video_id=video_id,
        student_id=student_id,
        timestamp=timestamp,
        content=content.strip()
    )

    return {
        "success": True,
        "id": note.id,
        "message": "Note saved successfully"
    }
# ==================================================
# UPDATE VIDEO NOTE
# ==================================================

@app.put(
    "/video/{video_id}/notes/{note_id}"
)
def update_video_note(

    video_id: int,

    note_id: int,

    request: Request,

    data: dict = Body(...),

    db: Session = Depends(get_db)

):

    student_id = request.session.get(
        "user_id"
    )

    if not student_id:

        student_id = data.get(
            "student_id"
        )

    if not student_id:

        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    try:

        student_id = int(
            student_id
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid student ID"
        )

    note = db.query(
        models.VideoNote
    ).filter(
        models.VideoNote.id == note_id,
        models.VideoNote.video_id == video_id,
        models.VideoNote.student_id == student_id
    ).first()

    if not note:

        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    if (
        "content" in data
        or
        "text" in data
        or
        "note" in data
    ):

        new_content = str(
            data.get(
                "content",
                data.get(
                    "text",
                    data.get(
                        "note",
                        ""
                    )
                )
            )
        ).strip()

        if not new_content:

            raise HTTPException(
                status_code=400,
                detail="Note cannot be empty"
            )

        note.content = new_content

    if (
        "timestamp" in data
        or
        "time" in data
    ):

        note.timestamp = str(
            data.get(
                "timestamp",
                data.get(
                    "time",
                    note.timestamp or "00:00"
                )
            )
        ).strip() or "00:00"

    try:

        db.commit()

        db.refresh(
            note
        )

    except Exception as e:

        db.rollback()

        print(
            "VIDEO NOTE UPDATE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not update video note"
        )

    return {

        "success": True,

        "message": "Note updated successfully",

        "note": {

            "id": note.id,

            "video_id": note.video_id,

            "student_id": note.student_id,

            "timestamp": note.timestamp,

            "content": note.content,

            "text": note.content,

            "note": note.content,

            "created_at": (
                note.created_at.isoformat()
                if note.created_at
                else ""
            )

        }

    }


# ==================================================
# DELETE VIDEO NOTE
# ==================================================

@app.delete(
    "/video/{video_id}/notes/{note_id}"
)
def delete_video_note(

    video_id: int,

    note_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    student_id = request.session.get(
        "user_id"
    )

    if not student_id:

        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    note = db.query(
        models.VideoNote
    ).filter(
        models.VideoNote.id == note_id,
        models.VideoNote.video_id == video_id,
        models.VideoNote.student_id == student_id
    ).first()

    if not note:

        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    try:

        db.delete(
            note
        )

        db.commit()

    except Exception as e:

        db.rollback()

        print(
            "DELETE VIDEO NOTE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not delete note"
        )

    return {

        "success": True,

        "message": "Note deleted successfully"

    }
# ============================================================
# VIDEO LIKE
# ============================================================

@app.post(
    "/video/{video_id}/like"
)
def like_video(

    video_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    video = db.query(
        models.Video
    ).filter(
        models.Video.id == video_id
    ).first()

    if not video:

        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        user_id = request.query_params.get(
            "user_id"
        )

    # --------------------------------------------------------
    # For compatibility with existing frontend
    # --------------------------------------------------------

    try:

        video.likes = (
            video.likes or 0
        ) + 1

        db.commit()
        db.refresh(video)

    except Exception as e:

        db.rollback()

        print(
            "VIDEO LIKE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not like video"
        )

    return {

        "success": True,

        "message": "Video liked successfully",

        "video_id": video.id,

        "likes": video.likes

    }
@app.get("/video-notes/{video_id}/{student_id}")
def get_video_notes(
    video_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):
    notes = crud.get_video_notes(db, video_id, student_id)

    return [
        {
            "id": note.id,
            "timestamp": note.timestamp,
            "content": note.content,
            "created_at": (
                note.created_at.isoformat()
                if note.created_at else None
            )
        }
        for note in notes
    ]
# ============================================================
# VIDEO SELLER ANALYTICS API
# Fixes:
# GET /seller/{seller_id}/videos/statistics
#
# Existing seller functionality is untouched.
# ============================================================

@app.get("/seller/{seller_id}/videos/statistics")
def seller_video_statistics(
    seller_id: int,
    db: Session = Depends(get_db)
):
    return crud.get_seller_video_statistics(
        db,
        seller_id
    )
# ==================================================
# STUDENT GENERAL NOTES
# ==================================================

@app.get(
    "/student/{user_id}/notes"
)
def get_student_notes(

    user_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    session_user_id = request.session.get(
        "user_id"
    )

    if session_user_id:

        if int(session_user_id) != int(user_id):

            raise HTTPException(
                status_code=403,
                detail="Not authorized"
            )

    notes = db.query(
        models.StudentNote
    ).filter(
        models.StudentNote.student_id == user_id
    ).order_by(
        models.StudentNote.updated_at.desc()
    ).all()

    return [

        {

            "id": note.id,

            "student_id": note.student_id,

            "title": (
                note.title or "Untitled Note"
            ),

            "content": (
                note.content or ""
            ),

            "color": (
                note.color or "#fef3c7"
            ),

            "created_at": (
                note.created_at.isoformat()
                if note.created_at
                else ""
            ),

            "updated_at": (
                note.updated_at.isoformat()
                if note.updated_at
                else ""
            )

        }

        for note in notes

    ]


# ==================================================
# ADD STUDENT GENERAL NOTE
# ==================================================

@app.post(
    "/student/{user_id}/notes"
)
def add_student_note(

    user_id: int,

    request: Request,

    data: dict = Body(...),

    db: Session = Depends(get_db)

):

    session_user_id = request.session.get(
        "user_id"
    )

    if session_user_id:

        if int(session_user_id) != int(user_id):

            raise HTTPException(
                status_code=403,
                detail="Not authorized"
            )

    student = db.query(
        models.User
    ).filter(
        models.User.id == user_id
    ).first()

    if not student:

        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    title = str(
        data.get(
            "title",
            "Untitled Note"
        )
    ).strip()

    content = str(
        data.get(
            "content",
            ""
        )
    ).strip()

    color = str(
        data.get(
            "color",
            "#fef3c7"
        )
    ).strip()

    if not title:
        title = "Untitled Note"

    try:

        new_note = models.StudentNote(

            student_id=user_id,

            title=title,

            content=content,

            color=color

        )

        db.add(
            new_note
        )

        db.commit()

        db.refresh(
            new_note
        )

    except Exception as e:

        db.rollback()

        print(
            "STUDENT NOTE SAVE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not save student note"
        )

    return {

        "success": True,

        "message": "Note saved successfully",

        "note": {

            "id": new_note.id,

            "student_id": new_note.student_id,

            "title": new_note.title,

            "content": new_note.content,

            "color": new_note.color,

            "created_at": (
                new_note.created_at.isoformat()
                if new_note.created_at
                else ""
            ),

            "updated_at": (
                new_note.updated_at.isoformat()
                if new_note.updated_at
                else ""
            )

        }

    }


# ==================================================
# UPDATE STUDENT GENERAL NOTE
# ==================================================

@app.put(
    "/student/notes/{note_id}"
)
def update_student_note(

    note_id: int,

    request: Request,

    data: dict = Body(...),

    db: Session = Depends(get_db)

):

    session_user_id = request.session.get(
        "user_id"
    )

    if not session_user_id:

        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    note = db.query(
        models.StudentNote
    ).filter(
        models.StudentNote.id == note_id,
        models.StudentNote.student_id == session_user_id
    ).first()

    if not note:

        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    if "title" in data:

        note.title = str(
            data.get(
                "title",
                ""
            )
        ).strip() or "Untitled Note"

    if "content" in data:

        note.content = str(
            data.get(
                "content",
                ""
            )
        )

    if "color" in data:

        note.color = str(
            data.get(
                "color",
                "#fef3c7"
            )
        ).strip() or "#fef3c7"

    try:

        db.commit()

        db.refresh(
            note
        )

    except Exception as e:

        db.rollback()

        print(
            "STUDENT NOTE UPDATE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not update note"
        )

    return {

        "success": True,

        "message": "Note updated successfully",

        "note": {

            "id": note.id,

            "student_id": note.student_id,

            "title": note.title,

            "content": note.content,

            "color": note.color,

            "created_at": (
                note.created_at.isoformat()
                if note.created_at
                else ""
            ),

            "updated_at": (
                note.updated_at.isoformat()
                if note.updated_at
                else ""
            )

        }

    }


# ==================================================
# DELETE STUDENT GENERAL NOTE
# ==================================================

@app.delete(
    "/student/notes/{note_id}"
)
def delete_student_note(

    note_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    session_user_id = request.session.get(
        "user_id"
    )

    if not session_user_id:

        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    note = db.query(
        models.StudentNote
    ).filter(
        models.StudentNote.id == note_id,
        models.StudentNote.student_id == session_user_id
    ).first()

    if not note:

        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    try:

        db.delete(
            note
        )

        db.commit()

    except Exception as e:

        db.rollback()

        print(
            "STUDENT NOTE DELETE ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Could not delete note"
        )

    return {

        "success": True,

        "message": "Note deleted successfully"

    }


# ==================================================
# PAYMENT & PURCHASE ENDPOINTS
# ==================================================


def finalize_successful_payment(db: Session, payment):
    purchase = None
    if str(payment.status).lower() in ["success", "completed", "active"]:
        existing_purchase = None
        if payment.book_id:
            existing_purchase = crud.get_book_purchase(db, payment.user_id, payment.book_id)
        elif payment.video_id:
            existing_purchase = crud.get_video_purchase(db, payment.user_id, payment.video_id)

        if not existing_purchase:
            purchase = crud.create_purchase(
                db,
                user_id=payment.user_id,
                amount=payment.amount,
                payment_id=payment.id,
                book_id=payment.book_id,
                video_id=payment.video_id
            )
    return purchase


@app.get("/payment/razorpay/config")
def get_razorpay_config():
    return {
        "enabled": razorpay_enabled(),
        "key_id": RAZORPAY_KEY_ID,
        "currency": "INR",
        "message": "Razorpay is configured." if razorpay_enabled() else "Razorpay API keys are not configured yet."
    }


@app.post("/payment/create")
def create_payment_endpoint(
    request: Request,
    data: dict = Body(None),
    amount: float = Form(None),
    payment_for: str = Form(None),
    item_id: int = Form(None),
    item_type: str = Form(None),
    user_id: int = Form(None),
    db: Session = Depends(get_db)
):
    # Support JSON Body, Form Data, and Query Parameters
    body_data = data or {}
    final_amount = amount if amount is not None else body_data.get("amount")
    final_payment_for = payment_for or body_data.get("payment_for") or "Purchase"
    final_item_id = item_id if item_id is not None else body_data.get("item_id")
    final_item_type = item_type or body_data.get("item_type", "book")

    final_user_id = user_id if user_id is not None else body_data.get("user_id")
    if not final_user_id:
        final_user_id = request.session.get("user_id", 0)

    # If amount not explicitly given or 0, fetch item price from database
    if (final_amount is None or float(final_amount) == 0) and final_item_id:
        if str(final_item_type).lower() == "book":
            b = crud.get_book(db, int(final_item_id))
            if b:
                final_amount = b.price or 0.0
        elif str(final_item_type).lower() == "video":
            v = crud.get_video(db, int(final_item_id))
            if v:
                final_amount = v.price or 0.0

    payment = crud.create_payment(
        db=db,
        user_id=int(final_user_id) if final_user_id else 1,
        amount=float(final_amount or 0.0),
        payment_for=str(final_payment_for),
        item_id=int(final_item_id) if final_item_id else None,
        item_type=str(final_item_type)
    )

    return {
        "success": True,
        "payment_id": payment.id,
        "amount": payment.amount,
        "status": payment.status,
        "message": "Payment initiated successfully"
    }


@app.post("/payment/razorpay/order")
def create_razorpay_order(
    request: Request,
    data: dict = Body(None),
    db: Session = Depends(get_db)
):
    if not razorpay_enabled():
        raise HTTPException(status_code=503, detail="Razorpay is not configured on this server.")

    body_data = data or {}
    amount = body_data.get("amount")
    payment_for = body_data.get("payment_for") or "Purchase"
    item_id = body_data.get("item_id")
    item_type = body_data.get("item_type") or "book"
    user_id = body_data.get("user_id") or request.session.get("user_id")

    if amount is None or float(amount) <= 0:
        raise HTTPException(status_code=400, detail="A valid amount is required.")

    payment = crud.create_payment(
        db=db,
        user_id=int(user_id) if user_id else 1,
        amount=float(amount),
        payment_for=str(payment_for),
        item_id=int(item_id) if item_id else None,
        item_type=str(item_type)
    )

    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    order = client.order.create({
        "amount": int(float(amount) * 100),
        "currency": "INR",
        "receipt": f"edunote_{payment.id}",
        "notes": {
            "payment_id": str(payment.id),
            "payment_for": str(payment_for),
            "item_id": str(item_id) if item_id else "",
            "item_type": str(item_type),
            "user_id": str(user_id) if user_id else ""
        }
    })

    return {
        "success": True,
        "payment_id": payment.id,
        "order_id": order["id"],
        "amount": int(float(amount) * 100),
        "currency": "INR",
        "key_id": RAZORPAY_KEY_ID,
        "message": "Razorpay order created successfully"
    }


@app.post("/payment/razorpay/verify")
def verify_razorpay_payment(
    request: Request,
    data: dict = Body(None),
    db: Session = Depends(get_db)
):
    if not razorpay_enabled():
        raise HTTPException(status_code=503, detail="Razorpay is not configured on this server.")

    body_data = data or {}
    payment_id = body_data.get("payment_id")
    order_id = body_data.get("order_id")
    payment_signature = body_data.get("signature")
    razorpay_payment_id = body_data.get("razorpay_payment_id")

    if not all([payment_id, order_id, payment_signature, razorpay_payment_id]):
        raise HTTPException(status_code=400, detail="Missing Razorpay verification data.")

    if not verify_razorpay_signature(order_id, razorpay_payment_id, payment_signature):
        raise HTTPException(status_code=400, detail="Razorpay signature verification failed.")

    payment = crud.get_payment_by_id(db, int(payment_id))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    payment = crud.update_payment_status(
        db,
        payment_id=payment.id,
        status="Success",
        payment_method="Razorpay",
        transaction_id=f"RZP_{razorpay_payment_id}"
    )

    purchase = finalize_successful_payment(db, payment)

    return {
        "success": True,
        "payment_id": payment.id,
        "status": payment.status,
        "payment_method": payment.payment_method,
        "transaction_id": payment.transaction_id,
        "purchase_id": purchase.id if purchase else None,
        "message": "Razorpay payment verified and access unlocked successfully"
    }


# ==================================================
# PAYU PAYMENT GATEWAY ENDPOINTS (TEST SANDBOX)
# ==================================================

@app.get("/payment/payu/config")
def get_payu_config():
    return {
        "enabled": True,
        "mode": PAYU_MODE,
        "key": PAYU_MERCHANT_KEY,
        "action_url": PAYU_ACTION_URL,
        "message": f"PayU is configured in {PAYU_MODE} mode."
    }


@app.post("/payment/payu/order")
def create_payu_order(
    request: Request,
    data: dict = Body(None),
    db: Session = Depends(get_db)
):
    body_data = data or {}
    amount = body_data.get("amount")
    payment_for = body_data.get("payment_for") or "Purchase"
    item_id = body_data.get("item_id")
    item_type = body_data.get("item_type") or "book"
    user_id = body_data.get("user_id") or request.session.get("user_id") or 1

    if amount is None or float(amount) <= 0:
        raise HTTPException(status_code=400, detail="A valid amount is required.")

    payment = crud.create_payment(
        db=db,
        user_id=int(user_id) if user_id else 1,
        amount=float(amount),
        payment_for=str(payment_for),
        item_id=int(item_id) if item_id else None,
        item_type=str(item_type)
    )

    amount_str = f"{float(amount):.2f}"
    txnid = f"EDUTXN{payment.id}{int(time.time())}"
    firstname = "EduNoteUser"
    email = "test@edunote.app"
    phone = "9876543210"
    productinfo = "EduNotePurchase"

    base_url = str(request.base_url).rstrip("/")
    surl = f"{base_url}/payment/payu/response"
    furl = f"{base_url}/payment/payu/response"
    udf1 = str(payment.id)

    hash_val = generate_payu_hash(
        txnid=txnid,
        amount=amount_str,
        productinfo=productinfo,
        firstname=firstname,
        email=email,
        udf1=udf1
    )

    return {
        "success": True,
        "payment_id": payment.id,
        "action_url": PAYU_ACTION_URL,
        "params": {
            "key": PAYU_MERCHANT_KEY,
            "txnid": txnid,
            "amount": amount_str,
            "productinfo": productinfo,
            "firstname": firstname,
            "email": email,
            "phone": phone,
            "surl": surl,
            "furl": furl,
            "udf1": udf1,
            "hash": hash_val
        },
        "message": "PayU order parameters generated successfully"
    }



@app.post("/payment/payu/response")
async def payu_response_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    data = dict(form_data)

    status = (data.get("status") or "").lower()
    txnid = data.get("txnid", "")
    payment_id = data.get("udf1")
    unmappedstatus = data.get("unmappedstatus", "")

    # Check hash validation (in test mode, accept success or valid hash)
    is_valid_hash = verify_payu_hash(data) if PAYU_MODE != "test" else True

    payment = None
    if payment_id and str(payment_id).isdigit():
        payment = crud.get_payment_by_id(db, int(payment_id))

    user_id = payment.user_id if payment else request.session.get("user_id", 1)

    if status == "success" and is_valid_hash:
        if payment:
            payment = crud.update_payment_status(
                db,
                payment_id=payment.id,
                status="Success",
                payment_method="PayU",
                transaction_id=txnid or data.get("mihpayid", f"PAYU_{int(time.time())}")
            )
            finalize_successful_payment(db, payment)

            if payment.book_id:
                return RedirectResponse(url=f"/read/{payment.book_id}?user_id={user_id}&payment=success", status_code=303)
            elif payment.video_id:
                return RedirectResponse(url=f"/videowatch/{payment.video_id}?user_id={user_id}&payment=success", status_code=303)

        return RedirectResponse(url=f"/student/{user_id}?payment=success", status_code=303)
    else:
        if payment:
            crud.update_payment_status(
                db,
                payment_id=payment.id,
                status="Cancelled" if status in ["cancel", "cancelled"] or unmappedstatus == "userCancelled" else "Failed",
                payment_method="PayU",
                transaction_id=txnid
            )
        return RedirectResponse(url=f"/student/{user_id}?payment=cancelled", status_code=303)


@app.post("/payment/{payment_id}/status")
def update_payment_status_endpoint(
    payment_id: int,
    request: Request,
    status: str = "Success",
    payment_method: str = "UPI",
    transaction_id: str = None,
    data: dict = Body(None),
    db: Session = Depends(get_db)
):
    body_data = data or {}
    final_status = body_data.get("status") or request.query_params.get("status") or status or "Success"
    final_method = body_data.get("payment_method") or request.query_params.get("payment_method") or payment_method or "UPI"
    final_txn = body_data.get("transaction_id") or request.query_params.get("transaction_id") or transaction_id or f"TXN_{payment_id}_{int(datetime.utcnow().timestamp())}"

    payment = crud.update_payment_status(
        db,
        payment_id=payment_id,
        status=final_status,
        payment_method=final_method,
        transaction_id=final_txn
    )

    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    purchase = finalize_successful_payment(db, payment)

    return {
        "success": True,
        "payment_id": payment.id,
        "status": payment.status,
        "payment_method": payment.payment_method,
        "transaction_id": payment.transaction_id,
        "purchase_id": purchase.id if purchase else None,
        "message": "Payment verified and access unlocked successfully"
    }


@app.post("/student/{user_id}/buy-book/{book_id}/confirm")
def confirm_book_purchase(
    user_id: int,
    book_id: int,
    request: Request,
    payment_method: str = Form("UPI"),
    db: Session = Depends(get_db)
):
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    amount = book.price or 0.0
    txn_id = f"BK_{book_id}_{user_id}_{int(datetime.utcnow().timestamp())}"

    # Create successful payment
    payment = crud.create_payment(
        db,
        user_id=user_id,
        amount=amount,
        payment_for=f"Book: {book.title}",
        item_id=book_id,
        item_type="book"
    )
    crud.update_payment_status(
        db,
        payment_id=payment.id,
        status="Success",
        payment_method=payment_method,
        transaction_id=txn_id
    )

    # Create purchase record if not exists
    existing = crud.get_book_purchase(db, user_id, book_id)
    if not existing:
        crud.create_purchase(
            db,
            user_id=user_id,
            amount=amount,
            payment_id=payment.id,
            book_id=book_id
        )

    return {
        "success": True,
        "message": "Book purchased successfully",
        "redirect": f"/read/{book_id}?user_id={user_id}"
    }


@app.post("/student/{user_id}/buy-video/{video_id}/confirm")
def confirm_video_purchase(
    user_id: int,
    video_id: int,
    request: Request,
    payment_method: str = Form("UPI"),
    db: Session = Depends(get_db)
):
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    amount = video.price or 0.0
    txn_id = f"VD_{video_id}_{user_id}_{int(datetime.utcnow().timestamp())}"

    # Create successful payment
    payment = crud.create_payment(
        db,
        user_id=user_id,
        amount=amount,
        payment_for=f"Video: {video.title}",
        item_id=video_id,
        item_type="video"
    )
    crud.update_payment_status(
        db,
        payment_id=payment.id,
        status="Success",
        payment_method=payment_method,
        transaction_id=txn_id
    )

    # Create purchase record if not exists
    existing = crud.get_video_purchase(db, user_id, video_id)
    if not existing:
        crud.create_purchase(
            db,
            user_id=user_id,
            amount=amount,
            payment_id=payment.id,
            video_id=video_id
        )

    return {
        "success": True,
        "message": "Video purchased successfully",
        "redirect": f"/video/{video_id}"
    }


@app.get("/payment", response_class=HTMLResponse)
def payment_page(
    request: Request,
    book_id: int = 0,
    video_id: int = 0,
    user_id: int = 0,
    db: Session = Depends(get_db)
):
    book = crud.get_book(db, book_id) if book_id else None
    video = crud.get_video(db, video_id) if video_id else None

    final_user_id = user_id or request.session.get("user_id", 0)
    user = crud.get_user_by_id(db, final_user_id) if final_user_id else None

    # Fallback to first published book if none specified
    if not book and not video:
        books = crud.get_published_books(db)
        if books:
            book = books[0]
            book_id = book.id

    response = templates.TemplateResponse(
        request=request,
        name="payment.html",
        context={
            "user_id": final_user_id,
            "user": user,
            "book_id": book_id,
            "book": book,
            "video_id": video_id,
            "video": video,
            "item_type": "video" if video and not book else "book"
        }
    )
    # Disable browser caching of payment page to prevent back button issues
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/student/{user_id}/purchases")
def get_student_purchases(
    user_id: int,
    db: Session = Depends(get_db)
):
    purchases = crud.get_user_purchases(db, user_id)
    result = []
    for p in purchases:
        b = crud.get_book(db, p.book_id) if p.book_id else None
        v = crud.get_video(db, p.video_id) if p.video_id else None
        result.append({
            "id": p.id,
            "amount": p.amount,
            "book_id": p.book_id,
            "video_id": p.video_id,
            "title": (b.title if b else (v.title if v else "Purchased Item")),
            "item_type": "book" if p.book_id else "video",
            "purchased_at": p.purchased_at.isoformat() if p.purchased_at else ""
        })
    return result


@app.get("/api/check-access/{item_type}/{item_id}")
def check_item_access(
    item_type: str,
    item_id: int,
    request: Request,
    user_id: int = 0,
    db: Session = Depends(get_db)
):
    final_user_id = user_id or request.session.get("user_id", 0)
    is_free = False
    price = 0.0
    has_access = False

    if item_type.lower() == "book":
        book = crud.get_book(db, item_id)
        if book:
            price = book.price or 0.0
            is_free = (price == 0)
            if is_free or (final_user_id and crud.has_book_access(db, final_user_id, item_id)):
                has_access = True
    elif item_type.lower() == "video":
        video = crud.get_video(db, item_id)
        if video:
            price = video.price or 0.0
            is_free = (price == 0)
            if is_free or (final_user_id and crud.has_video_access(db, final_user_id, item_id)):
                has_access = True

    return {
        "item_type": item_type,
        "item_id": item_id,
        "is_free": is_free,
        "price": price,
        "has_access": has_access
    }
