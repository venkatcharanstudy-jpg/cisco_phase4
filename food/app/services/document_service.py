import hashlib
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.exceptions import ValidationFailedError
from app.models.document import Document, DocumentChunk
from app.models.enums import DocumentStatus
from app.models.user import User
from app.rag.chunker import chunk_text
from app.rag.loader import load_pages, sanitize_filename


class DocumentService:
    """Ingests policy documents into document_chunks, keeping one ACTIVE version per filename."""

    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._max_bytes = settings.max_upload_mb * 1024 * 1024

    def ingest(self, admin: User, filename: str, data: bytes) -> Document:
        if len(data) == 0:
            raise ValidationFailedError("Uploaded file is empty")
        if len(data) > self._max_bytes:
            raise ValidationFailedError(f"File exceeds the {self._max_bytes // (1024 * 1024)} MB limit")
        safe_name = sanitize_filename(filename)
        pages = load_pages(safe_name, data)
        pieces = [(text, p.page) for p in pages for text in chunk_text(p.text)]
        if not pieces:
            raise ValidationFailedError("No readable text found in the document")

        try:
            version = (self._session.scalar(
                select(func.max(Document.version)).where(Document.filename == safe_name)
            ) or 0) + 1
            self._session.execute(
                update(Document)
                .where(Document.filename == safe_name, Document.status == DocumentStatus.ACTIVE)
                .values(status=DocumentStatus.SUPERSEDED)
            )
            doc = Document(
                filename=safe_name,
                sha256=hashlib.sha256(data).hexdigest(),
                version=version,
                status=DocumentStatus.ACTIVE,
                uploaded_by=admin.id,
            )
            self._session.add(doc)
            self._session.flush()
            for index, (text, page) in enumerate(pieces):
                self._session.add(DocumentChunk(document_id=doc.id, chunk_index=index, page=page, content=text))
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return doc

    def list_documents(self) -> list[dict[str, Any]]:
        docs = self._session.scalars(select(Document).order_by(Document.id.desc())).all()
        out = []
        for d in docs:
            count = self._session.scalar(select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == d.id))
            out.append({"id": d.id, "filename": d.filename, "version": d.version, "status": d.status, "chunks": count or 0})
        return out
