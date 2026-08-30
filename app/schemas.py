from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ============================================================
# USER SCHEMAS
# ============================================================

class UserBase(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    role: str = "student"


class UserCreate(UserBase):
    password: str


# Compatibility schema used by existing registration route
class RegisterUser(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


# Compatibility schema used by existing login route
class LoginUser(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# BOOK SCHEMAS
# ============================================================

class BookBase(BaseModel):
    title: str
    description: Optional[str] = ""
    content: Optional[str] = ""
    category: Optional[str] = ""
    price: float = 0.0


class BookCreate(BookBase):
    author_id: int

    # Keep compatibility with existing book upload/update code
    cover_image: Optional[str] = ""
    book_file: Optional[str] = ""
    status: Optional[str] = "Draft"


class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    cover_image: Optional[str] = None
    book_file: Optional[str] = None


class BookResponse(BookBase):
    id: int
    author_id: int

    cover_image: Optional[str] = ""
    book_file: Optional[str] = ""

    status: str = "Draft"

    views: int = 0
    likes: int = 0
    comments: int = 0
    sales: int = 0

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# BOOK COMMENTS
# ============================================================

class CommentCreate(BaseModel):
    book_id: int
    user_id: int

    # Existing database column is "text"
    text: str


class CommentResponse(BaseModel):
    id: int
    book_id: int
    user_id: int
    text: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# VIDEO SCHEMAS
# ============================================================

class VideoBase(BaseModel):
    title: str
    description: Optional[str] = ""
    category: Optional[str] = ""
    price: float = 0.0


class VideoCreate(VideoBase):
    seller_id: int

    # Existing upload code can provide these
    filename: str = ""
    thumbnail: Optional[str] = ""
    duration: Optional[str] = ""
    status: Optional[str] = "Published"


class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[str] = None
    status: Optional[str] = None
    thumbnail: Optional[str] = None
    filename: Optional[str] = None


class VideoResponse(VideoBase):
    id: int
    seller_id: int

    filename: str
    thumbnail: Optional[str] = ""

    duration: Optional[str] = ""
    status: str = "Published"

    views: int = 0
    likes: int = 0
    comments: int = 0
    sales: int = 0

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# VIDEO COMMENT SCHEMAS
# ============================================================

class VideoCommentCreate(BaseModel):
    """
    Used by the video watch page.

    Accepted frontend fields:

        video_id
        user_id
        student_id
        text
        content

    Database uses:

        video_id
        user_id
        text
    """

    video_id: Optional[int] = None

    # Existing backend/database user field
    user_id: Optional[int] = None

    # Existing frontend student field
    student_id: Optional[int] = None

    # Existing database column
    text: Optional[str] = None

    # Compatibility with frontend
    content: Optional[str] = None

    def get_user_id(self) -> Optional[int]:
        """
        Return user_id if supplied,
        otherwise use student_id.
        """
        return self.user_id or self.student_id

    def get_text(self) -> str:
        """
        Return text if supplied,
        otherwise use content.
        """
        return (self.text or self.content or "").strip()


class VideoCommentResponse(BaseModel):
    id: int
    video_id: int
    user_id: int
    text: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# VIDEO LIKE SCHEMAS
# ============================================================

class VideoLikeCreate(BaseModel):
    """
    Used by the video watch page.

    Frontend can send:

        {
            "video_id": 1,
            "user_id": 1,
            "student_id": 1
        }

    Only student_id is required by this schema.
    """

    student_id: int

    # Optional compatibility fields.
    # They do not break existing code.
    video_id: Optional[int] = None
    user_id: Optional[int] = None


class VideoLikeResponse(BaseModel):
    success: bool
    likes: int
    liked: Optional[bool] = None


# ============================================================
# VIDEO NOTE SCHEMAS
# ============================================================

class VideoNoteCreate(BaseModel):
    video_id: int
    student_id: int

    timestamp: str = "00:00"

    content: str = ""


class VideoNoteUpdate(BaseModel):
    timestamp: Optional[str] = None
    content: Optional[str] = None


class VideoNoteResponse(BaseModel):
    id: int
    video_id: int
    student_id: int

    timestamp: str
    content: str

    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# STUDENT GENERAL NOTES
# ============================================================

class StudentNoteCreate(BaseModel):
    student_id: int

    title: str = "Untitled"
    content: str = ""
    color: str = "#fef3c7"


class StudentNoteUpdate(BaseModel):
    title: str = "Untitled"
    content: str = ""
    color: str = "#fef3c7"


class StudentNoteResponse(BaseModel):
    id: int
    student_id: int

    title: str
    content: str
    color: str

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# PAYMENT
# ============================================================

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)

    # Existing payment fields
    payment_for: Optional[str] = None
    item_id: Optional[int] = None
    item_type: Optional[str] = None

    # Compatibility fields
    user_id: Optional[int] = None
    book_id: Optional[int] = None
    video_id: Optional[int] = None

    payment_method: str = "demo"


class PaymentStatusUpdate(BaseModel):
    status: str

    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None


class PaymentResponse(BaseModel):
    success: bool
    message: str

    payment_id: int
    status: str
    amount: float


# ============================================================
# GENERIC RESPONSES
# ============================================================

class MessageResponse(BaseModel):
    success: bool
    message: str


class LoginResponse(BaseModel):
    success: bool
    message: Optional[str] = None