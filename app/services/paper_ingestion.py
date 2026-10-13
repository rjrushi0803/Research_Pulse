"""Application service for retrieving and deduplicating papers."""

import logging
import re
from typing import Protocol
from urllib.parse import urlparse

from app.models.paper import Paper

logger = logging.getLogger(__name__)


class PaperFetcher(Protocol):
    """Interface implemented by any paper metadata provider."""

    def fetch(
        self,
        keywords: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
        max_results: int = 10,
    ) -> list[Paper]: ...


class PaperIngestionService:
    """Coordinate paper retrieval and remove duplicate records."""

    def __init__(self, fetcher: PaperFetcher) -> None:
        """Receive a provider rather than constructing one internally."""

        self.fetcher = fetcher

    @staticmethod
    def _deduplication_key(paper: Paper) -> str:
        """Create a stable key, preferring DOI and then source URL."""

        if paper.doi.strip():
            # DOI values may be stored with or without their URL prefix.
            doi = paper.doi.strip().casefold()
            doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
            return f"doi:{doi}"

        if paper.source_url.strip():
            parsed = urlparse(paper.source_url.strip())
            path = parsed.path.rstrip("/")

            # arXiv versions such as 2610.12345v2 refer to the same work.
            if parsed.netloc.casefold().endswith("arxiv.org"):
                path = re.sub(r"v\d+$", "", path)

            return f"url:{parsed.netloc.casefold()}{path}"

        # Fallback for records that have no DOI or source URL.
        return f"title:{paper.paper_id}"

    def ingest(
        self,
        keywords: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
        max_results: int = 10,
    ) -> list[Paper]:
        """Fetch papers and return unique records in provider order."""

        papers = self.fetcher.fetch(
            keywords=keywords,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results,
        )

        unique_papers: list[Paper] = []
        seen_keys: set[str] = set()

        for paper in papers:
            key = self._deduplication_key(paper)

            if key in seen_keys:
                logger.debug("Skipping duplicate paper: %s", key)
                continue

            seen_keys.add(key)
            unique_papers.append(paper)

        logger.info(
            "Ingestion completed: fetched=%d unique=%d",
            len(papers),
            len(unique_papers),
        )

        return unique_papers


if __name__ == "__main__":
    # Manual live API smoke test:
    # uv run python -m app.services.paper_ingestion
    from app.providers.arxiv_fetcher import ArxivFetcher

    logging.basicConfig(level=logging.INFO)

    service = PaperIngestionService(fetcher=ArxivFetcher())

    papers = service.ingest(
        keywords=["AI in Drug Discovery"],
        start_date="2026-10-01",
        end_date="2026-10-12",
        max_results=5,
    )

    print(f"Unique papers: {len(papers)}")

    for paper in papers:
        print(paper.title, paper.paper_id)
