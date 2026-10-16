"""Convert a remote research paper URL to Markdown using Docling."""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)


class DocumentExtractionError(RuntimeError):
    """Raised when document conversion or Markdown export fails."""


def detect_gpu() -> bool:
    """Return True if PyTorch can access a CUDA GPU."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        logger.info("PyTorch is unavailable; using standard conversion.")
        return False


def build_converter(enable_picture_descriptions: bool) -> DocumentConverter:
    """Build a Docling converter with the requested processing options."""
    if not enable_picture_descriptions:
        logger.info("Using standard Docling conversion (no VLM descriptions).")
        return DocumentConverter()

    # Import VLM-related configuration only when requested.
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions,
        smolvlm_picture_description,
    )
    from docling.document_converter import PdfFormatOption

    options = PdfPipelineOptions()
    options.do_picture_description = True
    options.picture_description_options = smolvlm_picture_description
    options.images_scale = 1.0
    options.generate_picture_images = True

    logger.info("Enabling local SmolVLM picture descriptions.")

    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


class DoclingTextExtractor:
    """Convert approved remote URLs into persisted Markdown files."""

    def __init__(
        self,
        converter: DocumentConverter | None = None,
        allowed_hosts: set[str] | None = None,
        max_pages: int = 100,
        max_file_size_mb: int = 50,
        enable_picture_descriptions: bool | None = None,
    ) -> None:
        # None means choose automatically based on CUDA availability.
        if enable_picture_descriptions is None:
            enable_picture_descriptions = detect_gpu()

        self.picture_descriptions_enabled = enable_picture_descriptions

        # Injection lets tests use a fake converter without loading models.
        self.converter = converter or build_converter(enable_picture_descriptions)

        self.allowed_hosts = {
            host.lower()
            for host in (
                allowed_hosts if allowed_hosts is not None else {"arxiv.org", "export.arxiv.org"}
            )
        }
        self.max_pages = max_pages
        self.max_file_size = max_file_size_mb * 1024 * 1024

        logger.info(
            "Picture descriptions enabled: %s",
            self.picture_descriptions_enabled,
        )

    def _validate_url(self, url: str) -> None:
        """Accept HTTPS URLs only from explicitly approved hosts."""
        parsed = urlparse(url)

        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.hostname.lower() not in self.allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError("URL must use HTTPS and belong to an approved host.")

    @staticmethod
    def _get_figure_descriptions(document) -> list[str]:
        """Collect available figure captions and VLM descriptions."""
        sections: list[str] = []

        for index, picture in enumerate(document.pictures, start=1):
            try:
                caption = picture.caption_text(doc=document) or ""
            except (AttributeError, TypeError, ValueError):
                caption = ""

            description = ""
            metadata = getattr(picture, "meta", None)
            description_data = getattr(metadata, "description", None)

            if description_data is not None:
                description = getattr(description_data, "text", "") or ""

            # Avoid adding empty figure entries.
            if not caption.strip() and not description.strip():
                continue

            entry = [f"### Figure {index}"]

            if caption.strip():
                entry.append(f"**Caption:** {caption.strip()}")

            if description.strip():
                entry.append(f"**Description:** {description.strip()}")

            sections.append("\n\n".join(entry))

        return sections

    def _export_markdown(self, document) -> str:
        """Export Markdown and append available figure descriptions."""
        markdown = document.export_to_markdown()

        if not markdown or not markdown.strip():
            raise DocumentExtractionError("Docling returned empty Markdown.")

        # Descriptions are generated only if the configured pipeline
        # enabled a picture-description model. Captions may exist either way.
        figure_sections = self._get_figure_descriptions(document)

        if figure_sections:
            markdown += "\n\n## Figures and image descriptions\n\n" + "\n\n".join(figure_sections)

        return markdown

    def extract_to_markdown(
        self,
        source_url: str,
        output_dir: str | Path = "data/papers/markdown",
        paper_id: str | None = None,
    ) -> Path:
        """Convert a URL and atomically save its Markdown output."""
        self._validate_url(source_url)

        file_id = paper_id or hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:16]

        if not file_id or any(
            char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
            for char in file_id
        ):
            raise ValueError("paper_id contains invalid characters.")

        destination_dir = Path(output_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"{file_id}.md"
        temp_path: Path | None = None

        try:
            logger.info("Starting Docling conversion: %s", source_url)

            result = self.converter.convert(
                source_url,
                max_num_pages=self.max_pages,
                max_file_size=self.max_file_size,
                raises_on_error=False,
            )

            status = getattr(result, "status", None)
            status_name = getattr(status, "name", str(status)).upper()

            # PARTIAL_SUCCESS can contain useful extracted content.
            if "FAILURE" in status_name:
                errors = getattr(result, "errors", [])
                raise DocumentExtractionError(
                    f"Docling conversion failed: {status_name}; errors={errors}"
                )

            markdown = self._export_markdown(result.document)

            # Use a temporary file in the destination directory so that
            # os.replace remains atomic on the same filesystem.
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".tmp",
                prefix=f".{file_id}_",
                dir=destination_dir,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(markdown)
                temp_file.flush()
                os.fsync(temp_file.fileno())

            os.replace(temp_path, destination)
            temp_path = None

            logger.info("Markdown saved: %s", destination)
            return destination

        except Exception as exc:
            logger.exception("Markdown extraction failed for %s", source_url)

            if isinstance(exc, (ValueError, DocumentExtractionError)):
                raise

            raise DocumentExtractionError(f"Could not extract document from {source_url}") from exc

        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    extractor = DoclingTextExtractor()

    markdown_path = extractor.extract_to_markdown(
        source_url="https://arxiv.org/pdf/2206.01062",
        paper_id="example_paper",
    )

    print(f"Markdown saved to: {markdown_path}")
