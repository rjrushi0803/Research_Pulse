from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


class DuplicateEmailError(ValueError):
    """Raised when a profile already exists for an email."""


def parse_keywords(raw_keywords: str) -> list[str]:
    """Split keywords by commas or new lines and remove duplicates."""

    # Support either comma-separated or newline-separated input.
    parts = raw_keywords.replace("\n", ",").split(",")

    # Keep the first spelling while comparing case-insensitively.
    unique_keywords: dict[str, str] = {}

    for part in parts:
        keyword = part.strip()

        if keyword:
            unique_keywords.setdefault(keyword.casefold(), keyword)

    return list(unique_keywords.values())


def create_user_profile(
    db: Session,
    email: str,
    raw_keywords: str,
    research_description: str,
) -> User:
    """Create and persist a new user profile."""

    # Normalize email so simple case variations are treated consistently.
    normalized_email = email.strip().lower()

    # Check for an existing profile before attempting the insert.
    existing_user = db.scalar(select(User).where(User.email == normalized_email))

    if existing_user:
        raise DuplicateEmailError("A profile already exists for this email.")

    user = User(
        email=normalized_email,
        research_keywords=parse_keywords(raw_keywords),
        research_description=research_description.strip(),
    )

    db.add(user)

    try:
        # Commit writes the row to PostgreSQL.
        db.commit()

        # Refresh loads database-generated values, such as id and created_at.
        db.refresh(user)

    except IntegrityError as exc:
        # Roll back the failed transaction before the session is reused.
        db.rollback()

        # Another request may have inserted this email concurrently.
        raise DuplicateEmailError("A profile already exists for this email.") from exc

    return user
