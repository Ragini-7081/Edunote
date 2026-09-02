from sqlalchemy.orm import Session
from datetime import datetime

from . import models
from .schemas import (
    RegisterUser,
    BookCreate
)


# ==================================================
# USER CRUD
# ==================================================

def get_user_by_email(
    db: Session,
    email: str
):
    return (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )


def get_user_by_id(
    db: Session,
    user_id: int
):
    return (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )


def get_user_by_username(
    db: Session,
    username: str
):
    return (
        db.query(models.User)
        .filter(models.User.username == username)
        .first()
    )


def create_user(
    db: Session,
    user: RegisterUser
):
    db_user = models.User(
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        password=user.password,
        role=user.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


# ==================================================
# BOOK CRUD
# ==================================================

def create_book(
    db: Session,
    book: BookCreate
):
    db_book = models.Book(
        title=book.title,
        description=getattr(book, "description", "") or "",
        content=getattr(book, "content", "") or "",
        category=getattr(book, "category", "") or "",
        cover_image=getattr(book, "cover_image", "") or "",
        book_file=getattr(book, "book_file", "") or "",
        price=getattr(book, "price", 0) or 0,
        status=getattr(book, "status", "Draft") or "Draft",
        author_id=book.author_id
    )

    db.add(db_book)
    db.commit()
    db.refresh(db_book)

    return db_book


def get_book(
    db: Session,
    book_id: int
):
    return (
        db.query(models.Book)
        .filter(models.Book.id == book_id)
        .first()
    )


def get_book_by_id(
    db: Session,
    book_id: int
):
    return get_book(db, book_id)


def get_all_books(
    db: Session
):
    return (
        db.query(models.Book)
        .order_by(models.Book.created_at.desc())
        .all()
    )


def get_books(
    db: Session
):
    return get_all_books(db)


def get_books_by_author(
    db: Session,
    author_id: int
):
    return (
        db.query(models.Book)
        .filter(models.Book.author_id == author_id)
        .order_by(models.Book.created_at.desc())
        .all()
    )


def get_published_books(
    db: Session
):
    return (
        db.query(models.Book)
        .filter(models.Book.status == "Published")
        .order_by(models.Book.created_at.desc())
        .all()
    )


# ==================================================
# UPDATE BOOK
# ==================================================

def update_book(
    db: Session,
    book_id: int,
    title: str,
    description: str,
    category: str,
    price: float
):
    book = get_book(db, book_id)

    if not book:
        return None

    book.title = title
    book.description = description or ""
    book.category = category or ""
    book.price = price or 0

    db.commit()
    db.refresh(book)

    return book


# ==================================================
# DELETE BOOK
# ==================================================

def delete_book(
    db: Session,
    book_id: int
):
    book = get_book(db, book_id)

    if not book:
        return False

    db.delete(book)
    db.commit()

    return True


# ==================================================
# BOOK VIEWS
# ==================================================

def increase_view(
    db: Session,
    book_id: int
):
    book = get_book(db, book_id)

    if not book:
        return None

    book.views = (book.views or 0) + 1

    db.commit()
    db.refresh(book)

    return book


# ==================================================
# BOOK LIKES
# ==================================================

def like_book(
    db: Session,
    book_id: int
):
    book = get_book(db, book_id)

    if not book:
        return None

    book.likes = (book.likes or 0) + 1

    db.commit()
    db.refresh(book)

    return book


# ==================================================
# BOOK COMMENTS
# ==================================================

def create_comment(
    db: Session,
    comment
):
    if not comment.text or not comment.text.strip():
        return None

    new_comment = models.Comment(
        book_id=comment.book_id,
        user_id=comment.user_id,
        text=comment.text.strip()
    )

    db.add(new_comment)

    book = get_book(
        db,
        comment.book_id
    )

    if book:
        book.comments = (
            book.comments or 0
        ) + 1

    db.commit()
    db.refresh(new_comment)

    return new_comment


def get_comments_with_users(
    db: Session,
    book_id: int
):
    comments = (
        db.query(models.Comment)
        .filter(
            models.Comment.book_id == book_id
        )
        .order_by(
            models.Comment.created_at.desc()
        )
        .all()
    )

    result = []

    for comment in comments:
        result.append(
            {
                "id": comment.id,
                "book_id": comment.book_id,
                "user_id": comment.user_id,
                "content": comment.text,
                "text": comment.text,
                "created_at": (
                    comment.created_at.isoformat()
                    if comment.created_at
                    else ""
                ),
                "user": (
                    {
                        "id": comment.user.id,
                        "full_name": comment.user.full_name
                    }
                    if comment.user
                    else None
                ),
                "user_name": (
                    comment.user.full_name
                    if comment.user
                    else "User"
                )
            }
        )

    return result


def get_author_comments(
    db: Session,
    author_id: int
):
    return (
        db.query(models.Comment)
        .join(
            models.Book,
            models.Comment.book_id == models.Book.id
        )
        .filter(
            models.Book.author_id == author_id
        )
        .order_by(
            models.Comment.created_at.desc()
        )
        .all()
    )


# ==================================================
# AUTHOR STATISTICS
# ==================================================

def author_stats(
    db: Session,
    author_id: int
):
    books = get_books_by_author(
        db,
        author_id
    )

    total_books = len(books)

    total_views = sum(
        book.views or 0
        for book in books
    )

    total_likes = sum(
        book.likes or 0
        for book in books
    )

    total_comments = sum(
        book.comments or 0
        for book in books
    )

    total_sales = sum(
        book.sales or 0
        for book in books
    )

    total_earnings = sum(
        (book.price or 0) *
        (book.sales or 0)
        for book in books
    )

    return {
        "books": total_books,
        "comments": total_comments,
        "views": total_views,
        "likes": total_likes,
        "sales": total_sales,
        "earnings": round(
            total_earnings,
            2
        )
    }


# ==================================================
# AUTHOR ANALYTICS
# ==================================================

def author_analytics(
    db: Session,
    author_id: int
):
    books = get_books_by_author(
        db,
        author_id
    )

    total_books = len(books)
    total_views = sum(book.views or 0 for book in books)
    total_likes = sum(book.likes or 0 for book in books)
    total_sales = sum(book.sales or 0 for book in books)

    book_labels = [book.title for book in books]
    book_views = [book.views or 0 for book in books]
    book_likes = [book.likes or 0 for book in books]
    book_comments = [book.comments or 0 for book in books]
    book_sales = [book.sales or 0 for book in books]

    # Category counts
    cat_map = {}
    for book in books:
        cat = book.category or "General"
        cat_map[cat] = cat_map.get(cat, 0) + 1

    category_labels = list(cat_map.keys()) if cat_map else ["General"]
    category_counts = list(cat_map.values()) if cat_map else [0]

    # Monthly views mock/trend
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
    base_v = max(1, total_views // 8) if total_views else 0
    monthly_views = [int(base_v * (0.6 + 0.1 * i)) for i in range(len(months))]
    if monthly_views and total_views:
        monthly_views[-1] = max(monthly_views[-1], total_views - sum(monthly_views[:-1]))

    return {
        # Flat compatibility
        "labels": book_labels,
        "views": book_views,
        "likes": book_likes,
        "comments": book_comments,
        "sales": book_sales,

        # Detailed analytics.html keys
        "total_books": total_books,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_sales": total_sales,
        "months": months,
        "monthly_views": monthly_views,
        "category_labels": category_labels,
        "category_counts": category_counts,
        "book_labels": book_labels,
        "book_views": book_views,
        "book_likes": book_likes,
        "book_comments": book_comments,
        "book_sales": book_sales
    }


# # ==================================================
# # STUDENT STATISTICS
# # ==================================================

# def get_student_stats(
#     db: Session,
#     user_id: int
# ):
#     try:
#         total_books = (
#             db.query(models.Book)
#             .filter(
#                 models.Book.status == "Published"
#             )
#             .count()
#         )
#     except Exception:
#         total_books = 0

#     try:
#         total_videos = (
#             db.query(models.Video)
#             .filter(
#                 models.Video.status == "Published"
#             )
#             .count()
#         )
#     except Exception:
#         total_videos = 0

#     try:
#         total_notes = (
#             db.query(models.StudentNote)
#             .filter(
#                 models.StudentNote.student_id == user_id
#             )
#             .count()
#         )
#     except Exception:
#         total_notes = 0

#     return {
#         "books": total_books,
#         "videos": total_videos,
#         "notes": total_notes
#     }

# ============================================================
# STUDENT STATS
# ============================================================

def get_student_stats(db: Session, user_id: int):

    # --------------------------------------------------------
    # BOOK ANALYTICS
    # --------------------------------------------------------

    comments = db.query(models.Comment).filter(
        models.Comment.user_id == user_id
    ).all()

    # Books student interacted with (commented or purchased)
    try:
        book_ids = set(
            comment.book_id
            for comment in comments
            if comment.book_id is not None
        )
        for bp in db.query(models.Purchase.book_id).filter(
            models.Purchase.user_id == user_id,
            models.Purchase.book_id.isnot(None),
            models.Purchase.active == True
        ).all():
            if bp[0]:
                book_ids.add(bp[0])
        books_interacted = len(book_ids)
    except Exception:
        books_interacted = len(comments)

    total_comments = len(comments)

    total_published_books = db.query(
        models.Book
    ).filter(
        models.Book.status == "Published"
    ).count()

    # --------------------------------------------------------
    # VIDEO ANALYTICS
    # --------------------------------------------------------

    try:
        total_published_videos = db.query(
            models.Video
        ).filter(
            models.Video.status == "Published"
        ).count()
    except Exception:
        total_published_videos = 0

    # Videos student interacted with (notes, comments, or purchased)
    try:
        video_ids = set()
        for vn in db.query(models.VideoNote.video_id).filter(models.VideoNote.student_id == user_id).all():
            if vn[0]: video_ids.add(vn[0])
        for vc in db.query(models.VideoComment.video_id).filter(models.VideoComment.user_id == user_id).all():
            if vc[0]: video_ids.add(vc[0])
        for vp in db.query(models.Purchase.video_id).filter(
            models.Purchase.user_id == user_id,
            models.Purchase.video_id.isnot(None),
            models.Purchase.active == True
        ).all():
            if vp[0]: video_ids.add(vp[0])
        videos_watched = len(video_ids)
    except Exception:
        videos_watched = 0

    # Total video notes created by this student.
    try:
        video_notes = db.query(
            models.VideoNote
        ).filter(
            models.VideoNote.student_id == user_id
        ).count()
    except Exception:
        video_notes = 0

    # General student notes.
    try:
        general_notes = db.query(
            models.StudentNote
        ).filter(
            models.StudentNote.student_id == user_id
        ).count()
    except Exception:
        general_notes = 0

    total_notes = video_notes + general_notes

    # --------------------------------------------------------
    # VIDEO COMMENTS
    # --------------------------------------------------------

    try:
        video_comments = db.query(
            models.VideoComment
        ).filter(
            models.VideoComment.user_id == user_id
        ).count()
    except Exception:
        video_comments = 0

    total_learning_comments = (
        total_comments + video_comments
    )

    # --------------------------------------------------------
    # PURCHASED CONTENT
    # --------------------------------------------------------

    try:
        purchased_books = db.query(
            models.Purchase
        ).filter(
            models.Purchase.user_id == user_id,
            models.Purchase.book_id.isnot(None),
            models.Purchase.active == True
        ).count()
    except Exception:
        purchased_books = 0

    try:
        purchased_videos = db.query(
            models.Purchase
        ).filter(
            models.Purchase.user_id == user_id,
            models.Purchase.video_id.isnot(None),
            models.Purchase.active == True
        ).count()
    except Exception:
        purchased_videos = 0

    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    book_progress = min(
        int(
            (
                books_interacted
                / max(total_published_books, 1)
            ) * 100
        ),
        100
    )

    video_progress = min(
        int(
            (
                videos_watched
                / max(total_published_videos, 1)
            ) * 100
        ),
        100
    )

    # Combined learning progress.
    total_available_content = (
        total_published_books +
        total_published_videos
    )

    total_completed_content = (
        books_interacted +
        videos_watched
    )

    overall_progress = min(
        int(
            (
                total_completed_content
                / max(total_available_content, 1)
            ) * 100
        ),
        100
    )

    # --------------------------------------------------------
    # STREAK
    # --------------------------------------------------------
    #
    # Keep the existing streak behaviour so no unrelated
    # functionality is changed.
    #

    streak = min(
        total_learning_comments * 2,
        30
    )

    # --------------------------------------------------------
    # RETURN ANALYTICS DATA
    # --------------------------------------------------------

    return {
        # Existing fields - PRESERVED
        "books_read": books_interacted,
        "total_comments": total_comments,
        "total_available": total_published_books,
        "streak": streak,
        "progress": overall_progress,

        # New student analytics
        "videos_watched": videos_watched,
        "total_videos": total_published_videos,
        "video_notes": video_notes,
        "general_notes": general_notes,
        "total_notes": total_notes,
        "video_comments": video_comments,
        "total_learning_comments": total_learning_comments,

        # Purchase information
        "purchased_books": purchased_books,
        "purchased_videos": purchased_videos,

        # Separate progress values
        "book_progress": book_progress,
        "video_progress": video_progress,
        "overall_progress": overall_progress,
    }
# ==================================================
# VIDEO CRUD
# ==================================================

def create_video(
    db: Session,
    title: str,
    description: str,
    category: str,
    price: float,
    filename: str,
    thumbnail: str,
    duration: str,
    status: str,
    seller_id: int
):
    video = models.Video(
        title=title,
        description=description or "",
        category=category or "",
        price=price or 0,
        filename=filename,
        thumbnail=thumbnail or "",
        duration=duration or "",
        status=status or "Published",
        seller_id=seller_id,
        views=0,
        likes=0,
        sales=0
    )

    db.add(video)
    db.commit()
    db.refresh(video)

    return video


def get_video(
    db: Session,
    video_id: int
):
    return (
        db.query(models.Video)
        .filter(
            models.Video.id == video_id
        )
        .first()
    )


def get_seller_videos(
    db: Session,
    seller_id: int
):
    return (
        db.query(models.Video)
        .filter(
            models.Video.seller_id == seller_id
        )
        .order_by(
            models.Video.created_at.desc()
        )
        .all()
    )


def get_published_videos(
    db: Session
):
    return (
        db.query(models.Video)
        .filter(
            models.Video.status == "Published"
        )
        .order_by(
            models.Video.created_at.desc()
        )
        .all()
    )


# ==================================================
# VIDEO UPDATE
# ==================================================

def update_video(
    db: Session,
    video,
    title: str,
    description: str,
    category: str,
    price: float,
    duration: str,
    status: str
):
    if not video:
        return None

    video.title = title
    video.description = description or ""
    video.category = category or ""
    video.price = price or 0
    video.duration = duration or ""
    video.status = status or "Published"

    db.commit()
    db.refresh(video)

    return video


# ==================================================
# VIDEO DELETE
# ==================================================

def delete_video(
    db: Session,
    video
):
    if not video:
        return False

    db.delete(video)
    db.commit()

    return True


# ==================================================
# VIDEO VIEWS
# ==================================================

def increase_video_views(
    db: Session,
    video
):
    if not video:
        return None

    video.views = (
        video.views or 0
    ) + 1

    db.commit()
    db.refresh(video)

    return video


# ==================================================
# VIDEO LIKES
# ==================================================

def like_video(
    db: Session,
    video
):
    if not video:
        return None

    video.likes = (
        video.likes or 0
    ) + 1

    db.commit()
    db.refresh(video)

    return video


# ==================================================
# VIDEO LIKE COUNT
# ==================================================

def get_video_like_count(
    db: Session,
    video_id: int
):
    video = get_video(
        db,
        video_id
    )

    if not video:
        return 0

    return video.likes or 0


# ==================================================
# VIDEO COMMENTS
# ==================================================

def create_video_comment(
    db: Session,
    video_id: int,
    user_id: int,
    content: str
):
    if not content:
        return None

    content = content.strip()

    if not content:
        return None

    video = get_video(
        db,
        video_id
    )

    if not video:
        return None

    user = get_user_by_id(
        db,
        user_id
    )

    if not user:
        return None

    comment = models.VideoComment(
        video_id=video_id,
        user_id=user_id,
        text=content
    )

    db.add(comment)

    # Keep video comment count synchronized
    if hasattr(video, "comments"):
        video.comments = (
            video.comments or 0
        ) + 1

    db.commit()
    db.refresh(comment)

    return comment


def get_video_comments(
    db: Session,
    video_id: int
):
    comments = (
        db.query(models.VideoComment)
        .filter(
            models.VideoComment.video_id == video_id
        )
        .order_by(
            models.VideoComment.created_at.asc()
        )
        .all()
    )

    result = []

    for comment in comments:

        user_name = "User"
        username = ""

        if comment.user:
            user_name = (
                comment.user.full_name
                or comment.user.username
                or "User"
            )

            username = (
                comment.user.username
                or ""
            )

        result.append(
            {
                "id": comment.id,
                "video_id": comment.video_id,
                "user_id": comment.user_id,

                # Both names are returned
                # for frontend compatibility.
                "content": comment.text,
                "text": comment.text,
                "comment": comment.text,

                "user_name": user_name,
                "username": username,

                "user": (
                    {
                        "id": comment.user.id,
                        "full_name": (
                            comment.user.full_name
                            or comment.user.username
                            or "User"
                        ),
                        "username": (
                            comment.user.username
                            or ""
                        )
                    }
                    if comment.user
                    else None
                ),

                "created_at": (
                    comment.created_at.isoformat()
                    if comment.created_at
                    else ""
                )
            }
        )

    return result


def get_video_comment_count(
    db: Session,
    video_id: int
):
    return (
        db.query(models.VideoComment)
        .filter(
            models.VideoComment.video_id == video_id
        )
        .count()
    )


def delete_video_comment(
    db: Session,
    comment_id: int,
    user_id: int = None
):
    query = (
        db.query(models.VideoComment)
        .filter(
            models.VideoComment.id == comment_id
        )
    )

    if user_id is not None:
        query = query.filter(
            models.VideoComment.user_id == user_id
        )

    comment = query.first()

    if not comment:
        return False

    video_id = comment.video_id

    db.delete(comment)

    video = get_video(
        db,
        video_id
    )

    if video and hasattr(video, "comments"):
        video.comments = max(
            0,
            (video.comments or 0) - 1
        )

    db.commit()

    return True


# ==================================================
# SELLER VIDEO STATISTICS
# ==================================================

def get_seller_video_statistics(
    db: Session,
    seller_id: int
):
    videos = get_seller_videos(
        db,
        seller_id
    )

    total_videos = len(videos)

    total_views = sum(
        video.views or 0
        for video in videos
    )

    total_likes = sum(
        video.likes or 0
        for video in videos
    )

    total_comments = sum(
        get_video_comment_count(
            db,
            video.id
        )
        for video in videos
    )

    total_sales = sum(
        video.sales or 0
        for video in videos
    )

    total_earnings = sum(
        (video.price or 0) *
        (video.sales or 0)
        for video in videos
    )

    return {
        "videos": total_videos,
        "total_videos": total_videos,

        "views": total_views,
        "total_views": total_views,

        "likes": total_likes,
        "total_likes": total_likes,

        "comments": total_comments,
        "total_comments": total_comments,

        "sales": total_sales,
        "total_sales": total_sales,

        "earnings": round(
            total_earnings,
            2
        ),
        "total_earnings": round(
            total_earnings,
            2
        ),

        "video_data": [
            {
                "id": video.id,
                "title": video.title,

                "views": video.views or 0,
                "likes": video.likes or 0,

                "comments": get_video_comment_count(
                    db,
                    video.id
                ),

                "sales": video.sales or 0,

                "earnings": round(
                    (video.price or 0) *
                    (video.sales or 0),
                    2
                )
            }
            for video in videos
        ]
    }


# ==================================================
# VIDEO NOTES
# ==================================================

def save_video_note(
    db: Session,
    video_id: int,
    student_id: int,
    timestamp: str,
    content: str
):
    # ----------------------------------------------
    # Validate video
    # ----------------------------------------------

    video = get_video(
        db,
        video_id
    )

    if not video:
        return None

    # ----------------------------------------------
    # Validate student
    # ----------------------------------------------

    student = get_user_by_id(
        db,
        student_id
    )

    if not student:
        return None

    # ----------------------------------------------
    # Validate content
    # ----------------------------------------------

    content = (
        content.strip()
        if content
        else ""
    )

    if not content:
        return None

    # ----------------------------------------------
    # Save note
    # ----------------------------------------------

    note = models.VideoNote(
        video_id=video_id,
        student_id=student_id,
        timestamp=timestamp or "0:00",
        content=content
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


def get_video_notes(
    db: Session,
    video_id: int,
    student_id: int
):
    return (
        db.query(models.VideoNote)
        .filter(
            models.VideoNote.video_id == video_id,
            models.VideoNote.student_id == student_id
        )
        .order_by(
            models.VideoNote.created_at.desc()
        )
        .all()
    )


def get_video_note(
    db: Session,
    note_id: int,
    student_id: int = None
):
    query = (
        db.query(models.VideoNote)
        .filter(
            models.VideoNote.id == note_id
        )
    )

    if student_id is not None:
        query = query.filter(
            models.VideoNote.student_id == student_id
        )

    return query.first()


def update_video_note(
    db: Session,
    note_id: int,
    student_id: int,
    timestamp: str,
    content: str
):
    note = get_video_note(
        db,
        note_id,
        student_id
    )

    if not note:
        return None

    content = (
        content.strip()
        if content
        else ""
    )

    if not content:
        return None

    note.timestamp = (
        timestamp or "0:00"
    )

    note.content = content

    if hasattr(note, "updated_at"):
        note.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(note)

    return note


def delete_video_note(
    db: Session,
    note_id: int,
    student_id: int = None
):
    note = get_video_note(
        db,
        note_id,
        student_id
    )

    if not note:
        return False

    db.delete(note)
    db.commit()

    return True


# ==================================================
# STUDENT GENERAL NOTES
# ==================================================

def get_student_notes(
    db: Session,
    student_id: int
):
    return (
        db.query(models.StudentNote)
        .filter(
            models.StudentNote.student_id == student_id
        )
        .order_by(
            models.StudentNote.updated_at.desc()
        )
        .all()
    )


def create_student_note(
    db: Session,
    student_id: int,
    title: str,
    content: str,
    color: str
):
    note = models.StudentNote(
        student_id=student_id,
        title=title or "Untitled",
        content=content or "",
        color=color or "#fef3c7"
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


def update_student_note(
    db: Session,
    note_id: int,
    title: str,
    content: str,
    color: str
):
    note = (
        db.query(models.StudentNote)
        .filter(
            models.StudentNote.id == note_id
        )
        .first()
    )

    if not note:
        return None

    note.title = title or "Untitled"
    note.content = content or ""
    note.color = color or "#fef3c7"

    if hasattr(note, "updated_at"):
        note.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(note)

    return note


def delete_student_note(
    db: Session,
    note_id: int
):
    note = (
        db.query(models.StudentNote)
        .filter(
            models.StudentNote.id == note_id
        )
        .first()
    )

    if not note:
        return False

    db.delete(note)
    db.commit()

    return True


# ==================================================
# PAYMENT CRUD
# ==================================================

def create_payment(
    db: Session,
    user_id: int,
    amount: float,
    payment_for: str,
    item_id: int = None,
    item_type: str = None
):
    book_id = None
    video_id = None

    if item_type:

        item_type_lower = (
            item_type.lower()
        )

        if item_type_lower == "book":
            book_id = item_id

        elif item_type_lower == "video":
            video_id = item_id

    payment = models.Payment(
        user_id=user_id,
        amount=amount or 0,
        book_id=book_id,
        video_id=video_id,
        status="Pending"
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def get_payment_by_id(
    db: Session,
    payment_id: int
):
    return (
        db.query(models.Payment)
        .filter(
            models.Payment.id == payment_id
        )
        .first()
    )


def get_user_payments(
    db: Session,
    user_id: int
):
    return (
        db.query(models.Payment)
        .filter(
            models.Payment.user_id == user_id
        )
        .order_by(
            models.Payment.created_at.desc()
        )
        .all()
    )


def get_successful_payments(
    db: Session,
    user_id: int
):
    return (
        db.query(models.Payment)
        .filter(
            models.Payment.user_id == user_id,
            models.Payment.status == "Success"
        )
        .order_by(
            models.Payment.created_at.desc()
        )
        .all()
    )


def update_payment_status(
    db: Session,
    payment_id: int,
    status: str,
    payment_method: str = None,
    transaction_id: str = None
):
    payment = get_payment_by_id(
        db,
        payment_id
    )

    if not payment:
        return None

    payment.status = status

    if payment_method is not None:
        payment.payment_method = payment_method

    if transaction_id is not None:
        # Verify uniqueness to avoid SQLite UNIQUE constraint errors
        existing = db.query(models.Payment).filter(
            models.Payment.transaction_id == transaction_id,
            models.Payment.id != payment_id
        ).first()
        if existing:
            import time
            payment.transaction_id = f"{transaction_id}_{int(time.time() * 1000)}"
        else:
            payment.transaction_id = transaction_id

    db.commit()
    db.refresh(payment)

    return payment


# ==================================================
# PURCHASE CRUD
# ==================================================

def create_purchase(
    db: Session,
    user_id: int,
    amount: float,
    payment_id: int = None,
    book_id: int = None,
    video_id: int = None
):
    purchase = models.Purchase(
        user_id=user_id,
        book_id=book_id,
        video_id=video_id,
        payment_id=payment_id,
        amount=amount or 0,
        active=True
    )

    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    # --------------------------------------------------
    # Increase sales count
    # --------------------------------------------------

    if book_id:

        book = get_book(
            db,
            book_id
        )

        if book:
            book.sales = (
                book.sales or 0
            ) + 1

    if video_id:

        video = get_video(
            db,
            video_id
        )

        if video:
            video.sales = (
                video.sales or 0
            ) + 1

    db.commit()

    return purchase


def get_user_purchases(
    db: Session,
    user_id: int
):
    return (
        db.query(models.Purchase)
        .filter(
            models.Purchase.user_id == user_id,
            models.Purchase.active == True
        )
        .order_by(
            models.Purchase.purchased_at.desc()
        )
        .all()
    )


def get_book_purchase(
    db: Session,
    user_id: int,
    book_id: int
):
    return (
        db.query(models.Purchase)
        .filter(
            models.Purchase.user_id == user_id,
            models.Purchase.book_id == book_id,
            models.Purchase.active == True
        )
        .first()
    )


def get_video_purchase(
    db: Session,
    user_id: int,
    video_id: int
):
    return (
        db.query(models.Purchase)
        .filter(
            models.Purchase.user_id == user_id,
            models.Purchase.video_id == video_id,
            models.Purchase.active == True
        )
        .first()
    )


def has_book_access(
    db: Session,
    user_id: int,
    book_id: int
):
    return (
        get_book_purchase(
            db,
            user_id,
            book_id
        )
        is not None
    )


def has_video_access(
    db: Session,
    user_id: int,
    video_id: int
):
    return (
        get_video_purchase(
            db,
            user_id,
            video_id
        )
        is not None
    )
