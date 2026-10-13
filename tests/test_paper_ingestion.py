"""Tests for the paper ingestion service."""

from unittest.mock import Mock

from app.models.paper import Paper
from app.services.paper_ingestion import PaperIngestionService


def make_paper(
    source_url: str,
    doi: str = "",
    title: str = "AI for Drug Discovery",
) -> Paper:
    return Paper(
        title=title,
        authors=["Alice Smith"],
        abstract="Research abstract.",
        published_date="2026-10-05",
        source_url=source_url,
        doi=doi,
    )


def test_ingestion_removes_duplicate_source_urls():
    first = make_paper("https://arxiv.org/abs/2610.12345")
    duplicate = make_paper("https://arxiv.org/abs/2610.12345")

    fetcher = Mock()
    fetcher.fetch.return_value = [first, duplicate]

    service = PaperIngestionService(fetcher)
    papers = service.ingest(keywords=["AI"])

    assert len(papers) == 1
    assert papers[0] is first


def test_ingestion_removes_different_versions_of_same_arxiv_paper():
    first = make_paper("https://arxiv.org/abs/2610.12345v1")
    second = make_paper("https://arxiv.org/abs/2610.12345v2")

    fetcher = Mock()
    fetcher.fetch.return_value = [first, second]

    papers = PaperIngestionService(fetcher).ingest(["AI"])

    assert len(papers) == 1


def test_ingestion_prefers_doi_for_deduplication():
    first = make_paper(
        "https://arxiv.org/abs/2610.12345",
        doi="10.1234/example",
    )
    second = make_paper(
        "https://example.org/paper",
        doi="https://doi.org/10.1234/example",
        title="A different title",
    )

    fetcher = Mock()
    fetcher.fetch.return_value = [first, second]

    papers = PaperIngestionService(fetcher).ingest(["AI"])

    assert len(papers) == 1


def test_ingestion_passes_arguments_to_provider():
    fetcher = Mock()
    fetcher.fetch.return_value = []

    service = PaperIngestionService(fetcher)
    service.ingest(
        keywords=["AI in Drug Discovery"],
        start_date="2026-10-01",
        end_date="2026-10-12",
        max_results=5,
    )

    fetcher.fetch.assert_called_once_with(
        keywords=["AI in Drug Discovery"],
        start_date="2026-10-01",
        end_date="2026-10-12",
        max_results=5,
    )


def test_ingestion_returns_empty_list_when_no_papers_found():
    fetcher = Mock()
    fetcher.fetch.return_value = []

    papers = PaperIngestionService(fetcher).ingest(["AI"])

    assert papers == []


if __name__ == "__main__":
    # Manual test: uv run python tests/test_paper_ingestion.py
    test_ingestion_removes_duplicate_source_urls()
    test_ingestion_removes_different_versions_of_same_arxiv_paper()
    test_ingestion_returns_empty_list_when_no_papers_found()
    print("Manual ingestion tests passed.")
