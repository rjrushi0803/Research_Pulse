
"""Tests for the canonical Paper model."""

import pytest

from app.models.paper import Paper


def make_paper(**overrides) -> Paper:
    """Build a valid paper, allowing individual fields to be overridden."""

    values = {
        "title": "AI for Drug Discovery",
        "authors": ["Alice Smith", "Bob Jones"],
        "abstract": "A research abstract.",
        "published_date": "2026-10-12",
        "source_url": "https://arxiv.org/abs/2610.12345",
    }
    values.update(overrides)
    return Paper(**values)


def test_paper_normalizes_title_and_authors():
    paper = make_paper(
        title="  AI for Drug Discovery  ",
        authors=[" Alice Smith ", "Bob Jones"],
    )

    assert paper.title == "AI for Drug Discovery"
    assert paper.authors == ["Alice Smith", "Bob Jones"]


def test_paper_id_is_deterministic():
    first = make_paper(title="AI for Drug Discovery")
    second = make_paper(title=" AI   FOR drug discovery ")

    assert first.paper_id == second.paper_id


def test_to_dict_contains_expected_fields():
    paper = make_paper()

    data = paper.to_dict()

    assert data["title"] == "AI for Drug Discovery"
    assert data["authors"] == ["Alice Smith", "Bob Jones"]
    assert data["source_name"] == ""
    assert "paper_id" not in data  # It is a property, not a dataclass field.


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", ""),
        ("abstract", " "),
        ("source_url", ""),
        ("published_date", "2026-02-30"),
        ("published_date", "12-10-2026"),
    ],
)
def test_invalid_required_fields_are_rejected(field, value):
    with pytest.raises(ValueError):
        make_paper(**{field: value})


def test_authors_must_be_a_list():
    with pytest.raises(TypeError):
        make_paper(authors="Alice Smith")


def test_author_names_must_not_be_empty():
    with pytest.raises(ValueError):
        make_paper(authors=["Alice Smith", " "])


def test_optional_fields_must_have_string_types():
    with pytest.raises(TypeError):
        make_paper(pdf_url=None)


if __name__ == "__main__":
    # Manual test: uv run python tests/test_paper.py
    test_paper_normalizes_title_and_authors()
    test_paper_id_is_deterministic()
    test_to_dict_contains_expected_fields()
    print("Manual Paper tests passed.")
