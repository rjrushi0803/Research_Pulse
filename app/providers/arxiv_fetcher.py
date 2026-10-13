"""Fetch research-paper metadata from the arXiv API."""

import logging
from datetime import date
from typing import Protocol

import arxiv

from app.models.paper import Paper

logger = logging.getLogger(__name__)


class ArxivClientProtocol(Protocol):
    """Minimal interface required from the arXiv client."""

    def results(self, search: arxiv.Search): ...


class ArxivFetchError(RuntimeError):
    """Raised when arXiv retrieval or response parsing fails."""


class ArxivFetcher:
    """Retrieve and normalize paper metadata from arXiv."""

    def __init__(
        self,
        client: ArxivClientProtocol | None = None,
    ) -> None:
        """Accept an injectable client to make testing straightforward."""

        # Keep network configuration in one place.
        self.client = client or arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=2,
        )

    @staticmethod
    def _validate_inputs(
        keywords: list[str],
        start_date: str | None,
        end_date: str | None,
        max_results: int,
    ) -> None:
        """Reject invalid requests before making any network calls."""

        if not keywords or not all(
            isinstance(keyword, str) and keyword.strip() for keyword in keywords
        ):
            raise ValueError("keywords must contain non-empty strings.")

        if not isinstance(max_results, int) or isinstance(max_results, bool):
            raise TypeError("max_results must be an integer.")

        if max_results < 1:
            raise ValueError("max_results must be at least 1.")

        parsed_start = date.fromisoformat(start_date) if start_date else None
        parsed_end = date.fromisoformat(end_date) if end_date else None

        # Ensure callers do not accidentally request an inverted range.
        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise ValueError("start_date must not be after end_date.")

    @staticmethod
    def _build_query(
        keywords: list[str],
        start_date: str | None,
        end_date: str | None,
    ) -> str:
        """Build an arXiv query with optional submission-date filtering."""

        # Escape embedded quotation marks in keyword phrases.
        keyword_queries = []

        for keyword in keywords:
            escaped = keyword.strip().replace('"', r"\"")
            keyword_queries.append(f'all:"{escaped}"')

        # Match any supplied keyword phrase.
        query = " OR ".join(keyword_queries)

        if start_date or end_date:
            # The arXiv API expects timestamps in YYYYMMDDHHMM form.
            start = start_date.replace("-", "") + "0000" if start_date else "000000000000"
            end = end_date.replace("-", "") + "2359" if end_date else "999912312359"

            query = f"({query}) AND submittedDate:[{start} TO {end}]"

        return query

    @staticmethod
    def _to_paper(result: object) -> Paper:
        """Convert one arXiv API result to the canonical Paper model."""

        try:
            # arXiv provides a datetime for publication/submission.
            published_date = result.published.date().isoformat()

            return Paper(
                title=result.title,
                authors=[author.name for author in result.authors],
                abstract=result.summary,
                published_date=published_date,
                source_url=result.entry_id,
                pdf_url=result.pdf_url or "",
                source_name="arXiv",
                doi=result.doi or "",
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise ArxivFetchError("Could not normalize an arXiv result.") from exc

    def fetch(
        self,
        keywords: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
        max_results: int = 10,
    ) -> list[Paper]:
        """Fetch a bounded number of papers matching the supplied keywords.

        Args:
            keywords: Search phrases, such as ["AI in Drug Discovery"].
            start_date: Optional inclusive submission-date lower bound.
            end_date: Optional inclusive submission-date upper bound.
            max_results: Maximum number of papers to return.

        Returns:
            A list of normalized Paper objects.

        Raises:
            ValueError: If the query arguments are invalid.
            ArxivFetchError: If the API request or parsing fails.
        """

        self._validate_inputs(keywords, start_date, end_date, max_results)

        query = self._build_query(keywords, start_date, end_date)

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        papers: list[Paper] = []

        try:
            # The API client yields results incrementally. Stop at the limit.
            for result in self.client.results(search):
                papers.append(self._to_paper(result))

                if len(papers) >= max_results:
                    break

        except ArxivFetchError:
            raise
        except Exception as exc:
            logger.exception("arXiv request failed; keywords=%s", keywords)
            raise ArxivFetchError("Unable to retrieve papers from arXiv.") from exc

        logger.info("Retrieved %d papers from arXiv.", len(papers))

        return papers


if __name__ == "__main__":
    # Manual live API smoke test:
    # uv run python -m app.providers.arxiv_fetcher
    logging.basicConfig(level=logging.INFO)

    fetcher = ArxivFetcher()

    papers = fetcher.fetch(
        keywords=["AI in Drug Discovery"],
        start_date="2026-10-01",
        end_date="2026-10-12",
        max_results=5,
    )

    for paper in papers:
        print(paper.to_dict())
