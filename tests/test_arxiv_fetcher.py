
"""Tests for arXiv retrieval and metadata normalization."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.providers.arxiv_fetcher import ArxivFetcher, ArxivFetchError


def make_result():
    """Create a fake result shaped like an arXiv API entry."""

    return SimpleNamespace(
        title="AI in Drug Discovery",
        authors=[
            SimpleNamespace(name="Alice Smith"),
            SimpleNamespace(name="Bob Jones"),
        ],
        summary="A study of AI-based drug discovery.",
        published=datetime(2026, 10, 5, tzinfo=UTC),
        entry_id="https://arxiv.org/abs/2610.12345",
        pdf_url="https://arxiv.org/pdf/2610.12345",
        doi="10.1234/example",
    )


def test_fetch_maps_api_result_to_paper():
    client = Mock()
    client.results.return_value = iter([make_result()])
    fetcher = ArxivFetcher(client=client)

    papers = fetcher.fetch(
        keywords=["AI in Drug Discovery"],
        max_results=5,
    )

    assert len(papers) == 1
    assert papers[0].title == "AI in Drug Discovery"
    assert papers[0].authors == ["Alice Smith", "Bob Jones"]
    assert papers[0].published_date == "2026-10-05"
    assert papers[0].source_name == "arXiv"
    assert papers[0].doi == "10.1234/example"


def test_fetch_respects_result_limit():
    client = Mock()
    client.results.return_value = iter(
        [make_result(), make_result(), make_result()]
    )
    fetcher = ArxivFetcher(client=client)

    papers = fetcher.fetch(
        keywords=["drug discovery"],
        max_results=2,
    )

    assert len(papers) == 2


def test_fetch_rejects_invalid_date_range_before_api_call():
    client = Mock()
    fetcher = ArxivFetcher(client=client)

    with pytest.raises(ValueError):
        fetcher.fetch(
            keywords=["AI"],
            start_date="2026-10-10",
            end_date="2026-10-01",
        )

    client.results.assert_not_called()


def test_fetch_rejects_zero_result_limit():
    fetcher = ArxivFetcher(client=Mock())

    with pytest.raises(ValueError):
        fetcher.fetch(keywords=["AI"], max_results=0)


def test_fetch_wraps_api_errors():
    client = Mock()
    client.results.side_effect = RuntimeError("Network failure")
    fetcher = ArxivFetcher(client=client)

    with pytest.raises(ArxivFetchError):
        fetcher.fetch(keywords=["AI"])


def test_build_query_includes_keywords_and_date_range():
    query = ArxivFetcher._build_query(
        keywords=["AI in Drug Discovery"],
        start_date="2026-10-01",
        end_date="2026-10-12",
    )

    assert 'all:"AI in Drug Discovery"' in query
    assert "202610010000" in query
    assert "202610122359" in query


if __name__ == "__main__":
    # Manual test: uv run python tests/test_arxiv_fetcher.py
    test_fetch_maps_api_result_to_paper()
    test_fetch_respects_result_limit()
    test_fetch_rejects_invalid_date_range_before_api_call()
    print("Manual arXiv fetcher tests passed.")
