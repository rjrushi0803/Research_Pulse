"""Rule-based expansion of research descriptions into search terms."""

import re

from app.models.query_plan import QueryPlan

# Keep the dictionary small and reviewable initially.
# Expand it using terms relevant to your research users.
DOMAIN_TERMS: dict[str, list[str]] = {
    "virtual screening": [
        "virtual screening",
        "molecular docking",
        "structure-based drug design",
    ],
    "molecular docking": [
        "molecular docking",
        "protein ligand docking",
        "binding affinity prediction",
    ],
    "graph neural network": [
        "graph neural networks",
        "graph neural network",
        "geometric deep learning",
    ],
    "active learning": [
        "active learning",
        "uncertainty sampling",
        "iterative learning",
    ],
    "drug discovery": [
        "drug discovery",
        "computer aided drug design",
        "drug design",
    ],
    "large language model": [
        "large language models",
        "LLM",
        "language models",
    ],
    "retrieval augmented generation": [
        "retrieval augmented generation",
        "RAG",
        "information retrieval",
    ],
}


class DeterministicKeywordExpander:
    """Generate search terms using transparent, reproducible rules."""

    def __init__(self, max_keywords: int = 10) -> None:
        if max_keywords < 1:
            raise ValueError("max_keywords must be at least 1.")

        self.max_keywords = max_keywords

    def expand(
        self,
        description: str,
        excluded_terms: list[str] | None = None,
    ) -> QueryPlan:
        """Extract known concepts and expand them into related terms."""

        if not isinstance(description, str) or not description.strip():
            raise ValueError("Research description cannot be empty.")

        normalized = re.sub(r"\s+", " ", description.casefold()).strip()

        # Longest phrases are checked first to favor specific concepts.
        matched_concepts = sorted(
            DOMAIN_TERMS,
            key=len,
            reverse=True,
        )

        keywords: list[str] = []

        for concept in matched_concepts:
            # Match whole phrases, not accidental substrings.
            pattern = rf"(?<!\w){re.escape(concept)}(?!\w)"

            if re.search(pattern, normalized):
                for term in DOMAIN_TERMS[concept]:
                    if term.casefold() not in {keyword.casefold() for keyword in keywords}:
                        keywords.append(term)

        # If no dictionary term matches, retain the user description
        # as a fallback instead of returning an empty search plan.
        if not keywords:
            keywords = [description.strip()]

        return QueryPlan(
            keywords=keywords[: self.max_keywords],
            refined_description=description.strip(),
            excluded_terms=excluded_terms or [],
        )


if __name__ == "__main__":
    expander = DeterministicKeywordExpander(max_keywords=8)

    plan = expander.expand(
        description=(
            "I work in computational drug discovery using virtual "
            "screening, molecular docking, graph neural networks, "
            "and active learning."
        )
    )

    print("Refined description:", plan.refined_description)
    print("Generated keywords:")
    for keyword in plan.keywords:
        print("-", keyword)
