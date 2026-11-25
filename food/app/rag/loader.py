import io
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

import fitz  # pymupdf
from docx import Document as DocxDocument

from app.exceptions import ValidationFailedError

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@dataclass(frozen=True)
class LoadedPage:
    text: str
    page: int | None


def sanitize_filename(name: str) -> str:
    base = PurePosixPath(name.replace("\\", "/")).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._")
    if not cleaned:
        raise ValidationFailedError("Invalid filename")
    return cleaned[:120]


def load_pages(filename: str, data: bytes) -> list[LoadedPage]:
    ext = PurePosixPath(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationFailedError(f"Unsupported file type '{ext}'. Allowed: .pdf, .docx, .txt")
    if ext == ".txt":
        return [LoadedPage(text=data.decode("utf-8", errors="replace"), page=None)]
    if ext == ".docx":
        doc = DocxDocument(io.BytesIO(data))
        return [LoadedPage(text="\n\n".join(p.text for p in doc.paragraphs), page=None)]
    pdf = fitz.open(stream=data, filetype="pdf")
    try:
        return [LoadedPage(text=page.get_text(), page=i + 1) for i, page in enumerate(pdf)]
    finally:
        pdf.close()
