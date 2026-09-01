import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables
load_dotenv()


# ==================================================
# DATABASE URL
# ==================================================

# Use DATABASE_URL from environment (Render provides this)
# Fallback to SQLite for local development if not set
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./app.db"
)

# Convert PostgreSQL URLs to use psycopg3 driver
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    # Render sometimes uses old postgres:// scheme
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    # Standard postgresql:// becomes postgresql+psycopg:// for psycopg3
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


# ==================================================
# DATABASE ENGINE
# ==================================================

if "postgresql" in SQLALCHEMY_DATABASE_URL:
    # PostgreSQL configuration
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )
else:
    # SQLite configuration (local development)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={
            "check_same_thread": False
        }
    )


# ==================================================
# SESSION
# ==================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ==================================================
# BASE
# ==================================================

Base = declarative_base()


# ==================================================
# DATABASE DEPENDENCY
# ==================================================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()


# ==================================================
# ADD MISSING DATABASE COLUMNS
# ==================================================

def add_missing_database_columns():
    """
    Add newly required columns to existing SQLite
    tables without deleting existing data.

    This is important because SQLAlchemy's
    Base.metadata.create_all() does NOT add new
    columns to an already existing table.
    """

    with engine.begin() as connection:

        # Helper to get existing columns of a table
        def get_column_names(table_name):
            try:
                cols = connection.execute(
                    text(f"PRAGMA table_info({table_name})")
                ).fetchall()
                return [c[1] for c in cols]
            except Exception:
                return []

        # ==================================================
        # VIDEOS TABLE
        # ==================================================
        video_cols = get_column_names("videos")
        if video_cols:
            if "updated_at" not in video_cols:
                connection.execute(text("ALTER TABLE videos ADD COLUMN updated_at DATETIME"))
            if "created_at" not in video_cols:
                connection.execute(text("ALTER TABLE videos ADD COLUMN created_at DATETIME"))
            if "comments" not in video_cols:
                connection.execute(text("ALTER TABLE videos ADD COLUMN comments INTEGER DEFAULT 0"))

        # ==================================================
        # BOOKS TABLE
        # ==================================================
        book_cols = get_column_names("books")
        if book_cols:
            if "book_file" not in book_cols:
                connection.execute(text("ALTER TABLE books ADD COLUMN book_file VARCHAR(500) DEFAULT ''"))
            if "cover_image" not in book_cols:
                connection.execute(text("ALTER TABLE books ADD COLUMN cover_image VARCHAR(500) DEFAULT ''"))

        # ==================================================
        # PAYMENTS TABLE
        # ==================================================
        pay_cols = get_column_names("payments")
        if pay_cols:
            # Check if payments table is empty with obsolete NOT NULL constraints
            try:
                count = connection.execute(text("SELECT COUNT(*) FROM payments")).fetchone()[0]
                if count == 0:
                    connection.execute(text("DROP TABLE payments"))
                    pay_cols = []
            except Exception:
                pass

        if not pay_cols:
            try:
                Base.metadata.tables["payments"].create(connection)
            except Exception:
                pass

        # ==================================================
        # PURCHASES TABLE
        # ==================================================
        pur_cols = get_column_names("purchases")
        if pur_cols:
            try:
                count = connection.execute(text("SELECT COUNT(*) FROM purchases")).fetchone()[0]
                if count == 0:
                    connection.execute(text("DROP TABLE purchases"))
                    pur_cols = []
            except Exception:
                pass

        if not pur_cols:
            try:
                Base.metadata.tables["purchases"].create(connection)
            except Exception:
                pass


# ==================================================
# RUN DATABASE MIGRATION
# ==================================================

def initialize_database():

    # Create tables that don't exist
    Base.metadata.create_all(
        bind=engine
    )

    # Add columns that are missing from existing tables
    add_missing_database_columns()