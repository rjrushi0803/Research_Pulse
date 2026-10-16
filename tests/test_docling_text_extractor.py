from types import SimpleNamespace

import pytest

from app.ingestion.docling_text_extractor import (
    DoclingTextExtractor,
    DocumentExtractionError,
)


class FakeDocument:
    pictures = []

    def export_to_markdown(self):
        return "# Example paper\n\nPaper content."


class FakeConverter:
    def convert(self, source, **kwargs):
        return SimpleNamespace(
            status=SimpleNamespace(name="SUCCESS"),
            document=FakeDocument(),
            errors=[],
        )


def test_saves_markdown_without_picture_descriptions(tmp_path):
    extractor = DoclingTextExtractor(
        converter=FakeConverter(),
        enable_picture_descriptions=False,
    )

    path = extractor.extract_to_markdown(
        "https://arxiv.org/pdf/2206.01062",
        output_dir=tmp_path,
        paper_id="paper_123",
    )

    assert path.exists()
    assert path.read_text(encoding="utf-8") == ("# Example paper\n\nPaper content.")
    assert extractor.picture_descriptions_enabled is False


def test_rejects_unapproved_host(tmp_path):
    extractor = DoclingTextExtractor(
        converter=FakeConverter(),
        enable_picture_descriptions=False,
    )

    with pytest.raises(ValueError, match="approved host"):
        extractor.extract_to_markdown(
            "https://example.com/paper.pdf",
            output_dir=tmp_path,
        )


def test_rejects_empty_markdown(tmp_path):
    class EmptyDocument:
        pictures = []

        def export_to_markdown(self):
            return "  "

    class EmptyConverter:
        def convert(self, source, **kwargs):
            return SimpleNamespace(
                status=SimpleNamespace(name="SUCCESS"),
                document=EmptyDocument(),
                errors=[],
            )

    extractor = DoclingTextExtractor(
        converter=EmptyConverter(),
        enable_picture_descriptions=False,
    )

    with pytest.raises(DocumentExtractionError, match="empty Markdown"):
        extractor.extract_to_markdown(
            "https://arxiv.org/pdf/2206.01062",
            output_dir=tmp_path,
        )


def test_failed_conversion_does_not_write_markdown(tmp_path):
    class FailedConverter:
        def convert(self, source, **kwargs):
            return SimpleNamespace(
                status=SimpleNamespace(name="FAILURE"),
                document=FakeDocument(),
                errors=["simulated failure"],
            )

    extractor = DoclingTextExtractor(
        converter=FailedConverter(),
        enable_picture_descriptions=False,
    )

    with pytest.raises(DocumentExtractionError, match="conversion failed"):
        extractor.extract_to_markdown(
            "https://arxiv.org/pdf/2206.01062",
            output_dir=tmp_path,
            paper_id="failed_paper",
        )

    assert not (tmp_path / "failed_paper.md").exists()


def test_picture_description_setting_can_be_overridden():
    extractor = DoclingTextExtractor(
        converter=FakeConverter(),
        enable_picture_descriptions=True,
    )

    assert extractor.picture_descriptions_enabled is True
