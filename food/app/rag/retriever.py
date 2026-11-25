import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import DocumentStatus
from app.models.document import Document, DocumentChunk

_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset({"the", "a", "an", "is", "are", "of", "to", "in", "and", "or", "for", "on", "what", "how", "do", "i", "my", "it", "be"})


@dataclass(frozen=True)
class Citation:
    document: str
    chunk_id: int
    page: int | None
    score: float
    excerpt: str


class Retriever(Protocol):
    def search(self, query: str, top_k: int = 3) -> list[Citation]: ...


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOPWORDS]


class LexicalRetriever:
    """TF-IDF style scoring over active document chunks stored in MySQL."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def search(self, query: str, top_k: int = 3) -> list[Citation]:
        q_terms = set(_tokens(query))
        if not q_terms:
            return []
        rows = self._session.execute(
            select(DocumentChunk.id, DocumentChunk.content, DocumentChunk.page, Document.filename)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.status == DocumentStatus.ACTIVE)
        ).all()
        if not rows:
            return []
        doc_terms = [Counter(_tokens(r.content)) for r in rows]
        df: Counter[str] = Counter()
        for terms in doc_terms:
            df.update(set(terms))
        n = len(rows)
        scored: list[Citation] = []
        for row, terms in zip(rows, doc_terms):
            score = 0.0
            for term in q_terms:
                if term in terms:
                    idf = math.log((n + 1) / (df[term] + 1)) + 1.0
                    score += (1 + math.log(terms[term])) * idf
            if score > 0:
                scored.append(Citation(row.filename, row.id, row.page, round(score, 3), row.content[:300]))
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]
