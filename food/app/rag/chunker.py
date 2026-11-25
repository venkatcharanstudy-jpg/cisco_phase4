MIN_CHUNK = 500
MAX_CHUNK = 900
OVERLAP = 100


def chunk_text(text: str) -> list[str]:
    """Split on paragraph boundaries into 500-900 character chunks with ~100 characters of overlap."""
    normalized = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()
    if not normalized:
        return []
    chunks: list[str] = []
    current = ""
    for para in (p.strip() for p in normalized.split("\n\n") if p.strip()):
        while len(para) > MAX_CHUNK:
            cut = para.rfind(" ", MIN_CHUNK, MAX_CHUNK)
            cut = cut if cut != -1 else MAX_CHUNK
            piece, para = para[:cut].strip(), para[cut:].strip()
            if current:
                chunks.append(current)
                current = ""
            chunks.append(piece)
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= MAX_CHUNK:
            current = candidate
        else:
            chunks.append(current)
            tail = current[-OVERLAP:] if len(current) > OVERLAP else ""
            current = f"{tail}\n\n{para}".strip() if tail else para
    if current:
        chunks.append(current)
    return chunks
