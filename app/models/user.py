from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.psql_db import Base


class User(Base):
    """Database model for a Research Pulse user."""

    __tablename__ = "users"

    # Primary key: the database-generated unique ID for each user.
    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    # Email identifies the profile and must be unique.
    # It does not prove that the person owns the email address.
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    # PostgreSQL JSONB stores a list of research keywords.
    # Example: ["RAG", "drug discovery", "biomedical NLP"]
    research_keywords: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Longer, free-text description of the user's research interests.
    research_description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    # PostgreSQL sets this timestamp when the row is inserted.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
