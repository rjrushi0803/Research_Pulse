"""Download and extract text from research-paper PDFs."""

import logging

import httpx
import pymupdf

logger = logging.getLogger(__name__)


class PDFExtractionError(RuntimeError):
    """Raised when a PDF cannot be downloaded or parsed."""


class PDFTextExtractor:
    """Extract machine-readable text from a PDF URL."""

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        max_pdf_bytes: int = 30 * 1024 * 1024,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")

        if max_pdf_bytes < 1:
            raise ValueError("max_pdf_bytes must be positive.")

        self.timeout_seconds = timeout_seconds
        self.max_pdf_bytes = max_pdf_bytes

    def extract(self, pdf_url: str) -> str:
        """Download a PDF and return its extracted text.

        This implementation deliberately limits download size and time.
        """

        if not pdf_url.startswith("https://"):
            raise ValueError("Only HTTPS PDF URLs are accepted.")

        try:
            # Stream the response so large PDFs are not loaded unchecked.
            with httpx.stream(
                "GET",
                pdf_url,
                timeout=self.timeout_seconds,
                follow_redirects=True,
                headers={"User-Agent": "Research_Pulse/1.0 (research paper ingestion)"},
            ) as response:
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()

                if (
                    "application/pdf" not in content_type
                    and "application/octet-stream" not in content_type
                ):
                    raise PDFExtractionError(f"Unexpected content type: {content_type}")

                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.max_pdf_bytes:
                    raise PDFExtractionError("PDF exceeds the size limit.")

                pdf_bytes = bytearray()

                for chunk in response.iter_bytes():
                    pdf_bytes.extend(chunk)

                    # Enforce the limit even if Content-Length is missing.
                    if len(pdf_bytes) > self.max_pdf_bytes:
                        raise PDFExtractionError("PDF exceeds the size limit.")

            # Parse the in-memory PDF without writing temporary files.
            with pymupdf.open(
                stream=bytes(pdf_bytes),
                filetype="pdf",
            ) as document:
                page_texts = [page.get_text(sort=True).strip() for page in document]

            full_text = "\n\n".join(
                f"[Page {page_number}]\n{text}"
                for page_number, text in enumerate(page_texts, start=1)
                if text
            ).strip()

            if not full_text:
                raise PDFExtractionError("No extractable text found; OCR may be required.")

            logger.info(
                "Extracted %d characters from PDF.",
                len(full_text),
            )

            return full_text

        except PDFExtractionError:
            raise
        except (
            httpx.HTTPError,
            pymupdf.FileDataError,
            ValueError,
        ) as exc:
            logger.exception("PDF download or extraction failed.")
            raise PDFExtractionError("Unable to download or extract the paper PDF.") from exc


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    extractor = PDFTextExtractor()

    text = extractor.extract("https://arxiv.org/pdf/1706.03762")

    print(text)
