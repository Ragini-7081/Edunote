from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    inspect,
    text,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


# ============================================================
# USER
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    full_name = Column(
        String(150),
        nullable=False
    )

    username = Column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        index=True,
        nullable=False
    )

    password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(50),
        nullable=False,
        default="student"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    books = relationship(
        "Book",
        back_populates="author",
        cascade="all, delete-orphan"
    )

    comments = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Video comments written by this user
    video_comments = relationship(
        "VideoComment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    videos = relationship(
        "Video",
        back_populates="seller",
        cascade="all, delete-orphan"
    )

    video_notes = relationship(
        "VideoNote",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    student_notes = relationship(
        "StudentNote",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    payments = relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# ============================================================
# BOOK
# ============================================================

class Book(Base):
    __tablename__ = "books"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        default=""
    )

    content = Column(
        Text,
        default=""
    )

    category = Column(
        String(100),
        default=""
    )

    cover_image = Column(
        String(500),
        default=""
    )

    # --------------------------------------------------------
    # BOOK FILE
    # --------------------------------------------------------

    book_file = Column(
        String(500),
        default=""
    )

    price = Column(
        Float,
        default=0.0
    )

    status = Column(
        String(50),
        default="Draft"
    )

    views = Column(
        Integer,
        default=0
    )

    likes = Column(
        Integer,
        default=0
    )

    comments = Column(
        Integer,
        default=0
    )

    sales = Column(
        Integer,
        default=0
    )

    author_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    author = relationship(
        "User",
        back_populates="books"
    )

    book_comments = relationship(
        "Comment",
        back_populates="book",
        cascade="all, delete-orphan"
    )

    payments = relationship(
        "Payment",
        back_populates="book"
    )


# ============================================================
# BOOK COMMENTS
# ============================================================

class Comment(Base):
    __tablename__ = "comments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    book_id = Column(
        Integer,
        ForeignKey("books.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    text = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    book = relationship(
        "Book",
        back_populates="book_comments"
    )

    user = relationship(
        "User",
        back_populates="comments"
    )


# ============================================================
# VIDEO
# ============================================================

class Video(Base):
    __tablename__ = "videos"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        default=""
    )

    category = Column(
        String(100),
        default=""
    )

    price = Column(
        Float,
        default=0.0
    )

    filename = Column(
        String(500),
        nullable=False
    )

    thumbnail = Column(
        String(500),
        default=""
    )

    duration = Column(
        String(50),
        default=""
    )

    status = Column(
        String(50),
        default="Published"
    )

    seller_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    views = Column(
        Integer,
        default=0
    )

    likes = Column(
        Integer,
        default=0
    )

    # --------------------------------------------------------
    # VIDEO COMMENTS COUNT
    # --------------------------------------------------------
    # Keeps the existing seller analytics/dashboard structure
    # working without removing the separate VideoComment table.
    # --------------------------------------------------------

    comments = Column(
        Integer,
        default=0
    )

    sales = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    seller = relationship(
        "User",
        back_populates="videos"
    )

    video_notes = relationship(
        "VideoNote",
        back_populates="video",
        cascade="all, delete-orphan"
    )

    video_comments = relationship(
        "VideoComment",
        back_populates="video",
        cascade="all, delete-orphan"
    )

    payments = relationship(
        "Payment",
        back_populates="video"
    )


# ============================================================
# VIDEO COMMENTS
# ============================================================

class VideoComment(Base):
    __tablename__ = "video_comments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    video_id = Column(
        Integer,
        ForeignKey("videos.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    text = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    video = relationship(
        "Video",
        back_populates="video_comments"
    )

    user = relationship(
        "User",
        back_populates="video_comments"
    )


# ============================================================
# VIDEO NOTES
# ============================================================

class VideoNote(Base):
    __tablename__ = "video_notes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    video_id = Column(
        Integer,
        ForeignKey("videos.id"),
        nullable=False
    )

    student_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    timestamp = Column(
        String(50),
        default="00:00"
    )

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    video = relationship(
        "Video",
        back_populates="video_notes"
    )

    student = relationship(
        "User",
        back_populates="video_notes"
    )


# ============================================================
# STUDENT GENERAL NOTES
# ============================================================

class StudentNote(Base):
    __tablename__ = "student_notes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    student_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    title = Column(
        String(255),
        default="Untitled Note"
    )

    content = Column(
        Text,
        default=""
    )

    color = Column(
        String(50),
        default="#fef3c7"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    student = relationship(
        "User",
        back_populates="student_notes"
    )


# ============================================================
# PAYMENT
# ============================================================

class Payment(Base):
    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    book_id = Column(
        Integer,
        ForeignKey("books.id"),
        nullable=True
    )

    video_id = Column(
        Integer,
        ForeignKey("videos.id"),
        nullable=True
    )

    amount = Column(
        Float,
        default=0.0
    )

    payment_method = Column(
        String(50),
        default="demo"
    )

    transaction_id = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )

    status = Column(
        String(50),
        default="Pending"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    user = relationship(
        "User",
        back_populates="payments"
    )

    book = relationship(
        "Book",
        back_populates="payments"
    )

    video = relationship(
        "Video",
        back_populates="payments"
    )


# ============================================================
# PURCHASE / ACCESS RECORD
# ============================================================

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    book_id = Column(
        Integer,
        ForeignKey("books.id"),
        nullable=True
    )

    video_id = Column(
        Integer,
        ForeignKey("videos.id"),
        nullable=True
    )

    payment_id = Column(
        Integer,
        ForeignKey("payments.id"),
        nullable=True
    )

    amount = Column(
        Float,
        default=0.0
    )

    active = Column(
        Boolean,
        default=True
    )

    purchased_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables(engine):
    """
    Create all missing tables.

    Existing tables are NOT deleted.

    Also makes sure older databases get newly-added
    columns required by the current models.
    """

    # --------------------------------------------------------
    # CREATE MISSING TABLES
    # --------------------------------------------------------

    Base.metadata.create_all(
        bind=engine
    )

    # --------------------------------------------------------
    # DATABASE MIGRATIONS FOR EXISTING SQLITE DATABASE
    # --------------------------------------------------------

    try:

        inspector = inspect(engine)

        table_names = inspector.get_table_names()

        # ====================================================
        # BOOKS TABLE
        # ====================================================

        if "books" in table_names:

            columns = [
                column["name"]
                for column in inspector.get_columns(
                    "books"
                )
            ]

            if "book_file" not in columns:

                with engine.begin() as connection:

                    connection.execute(
                        text(
                            "ALTER TABLE books "
                            "ADD COLUMN book_file VARCHAR(500)"
                        )
                    )

                    print(
                        "DATABASE UPDATE: "
                        "Added books.book_file"
                    )

        # ====================================================
        # VIDEOS TABLE
        # ====================================================

        if "videos" in table_names:

            columns = [
                column["name"]
                for column in inspector.get_columns(
                    "videos"
                )
            ]

            if "comments" not in columns:

                with engine.begin() as connection:

                    connection.execute(
                        text(
                            "ALTER TABLE videos "
                            "ADD COLUMN comments INTEGER DEFAULT 0"
                        )
                    )

                    print(
                        "DATABASE UPDATE: "
                        "Added videos.comments"
                    )

    except Exception as e:

        print(
            "DATABASE COLUMN CHECK ERROR:",
            str(e)
        )