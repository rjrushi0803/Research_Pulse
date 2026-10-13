"""Canonical data model for a research paper."""

from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256


@dataclass
class Paper:
    """Normalized metadata for a scientific publication.

    Required fields are validated when a Paper is created.
    Optional metadata uses empty strings to keep serialization consistent.
    """

    title: str
    authors: list[str]
    abstract: str
    published_date: str
    source_url: str

    pdf_url: str = ""
    source_name: str = ""
    doi: str = ""
    methodology: str = ""
    results: str = ""
    full_text: str = ""

    def __post_init__(self) -> None:
        """Normalize simple fields and reject invalid required values."""

        # Strip whitespace without changing the meaning of the metadata.
        self.title = self.title.strip()
        self.abstract = self.abstract.strip()
        self.source_url = self.source_url.strip()

        required_strings = {
            "title": self.title,
            "abstract": self.abstract,
            "published_date": self.published_date,
            "source_url": self.source_url,
        }

        for field_name, value in required_strings.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string.")

        # Check types explicitly instead of silently converting bad data.
        if not isinstance(self.authors, list):
            raise TypeError("authors must be a list of strings.")

        if not all(isinstance(author, str) and author.strip() for author in self.authors):
            raise ValueError("Every author must be a non-empty string.")

        # Store a normalized author list.
        self.authors = [author.strip() for author in self.authors]

        # Require a real ISO 8601 calendar date, e.g. 2026-10-12.
        try:
            parsed_date = date.fromisoformat(self.published_date)
        except (TypeError, ValueError) as exc:
            raise ValueError("published_date must be a valid ISO date (YYYY-MM-DD).") from exc

        if parsed_date.isoformat() != self.published_date:
            raise ValueError("published_date must use the YYYY-MM-DD format.")

        # All optional metadata fields must be strings.
        optional_fields = (
            "pdf_url",
            "source_name",
            "doi",
            "methodology",
            "results",
            "full_text",
        )

        for field_name in optional_fields:
            if not isinstance(getattr(self, field_name), str):
                raise TypeError(f"{field_name} must be a string.")

    @property
    def paper_id(self) -> str:
        """Return a deterministic ID derived from the normalized title."""

        normalized_title = " ".join(self.title.casefold().split())
        return sha256(normalized_title.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        """Serialize the model into a dictionary."""

        return asdict(self)


if __name__ == "__main__":
    # Manual smoke test: python -m app.models.paper
    paper = Paper(
        title="  AI in Drug Discovery  ",
        authors=["Alice Smith", "Bob Jones"],
        abstract="A study of AI-based drug discovery.",
        published_date="2026-10-12",
        source_url="https://arxiv.org/abs/2610.12345",
        source_name="arXiv",
    )

    print("Paper ID:", paper.paper_id)
    print("Serialized paper:", paper.to_dict())
