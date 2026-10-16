"""Validated representation of a research search plan."""

from dataclasses import dataclass, field


@dataclass
class QueryPlan:
    """Search instructions generated from a user's research description."""

    keywords: list[str]
    refined_description: str
    excluded_terms: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize and validate the generated search plan."""

        if not isinstance(self.keywords, list):
            raise TypeError("keywords must be a list of strings.")

        if not self.keywords:
            raise ValueError("At least one keyword is required.")

        if not all(isinstance(term, str) and term.strip() for term in self.keywords):
            raise ValueError("Keywords must be non-empty strings.")

        if not isinstance(self.refined_description, str):
            raise TypeError("refined_description must be a string.")

        if not isinstance(self.excluded_terms, list):
            raise TypeError("excluded_terms must be a list of strings.")

        if not all(isinstance(term, str) and term.strip() for term in self.excluded_terms):
            raise ValueError("Excluded terms must be non-empty strings.")

        # Remove duplicates while preserving the original ordering.
        self.keywords = list(dict.fromkeys(term.strip() for term in self.keywords))
        self.excluded_terms = list(dict.fromkeys(term.strip() for term in self.excluded_terms))
        self.refined_description = self.refined_description.strip()
