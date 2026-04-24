from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader


SUPPORTED_TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".json"}
SUPPORTED_SUFFIXES = SUPPORTED_TEXT_SUFFIXES | {".pdf"}


@dataclass(slots=True)
class UploadArtifact:
    filename: str
    content_type: str | None
    raw_bytes: bytes
    text: str
    checksum: str


async def load_upload(upload: UploadFile) -> UploadArtifact:
    filename = Path(upload.filename or "document.txt").name
    suffix = Path(filename).suffix.lower()

    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix or 'unknown'}",
        )

    raw_bytes = await upload.read()
    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    text = extract_text(raw_bytes, suffix)
    checksum = hashlib.sha256(raw_bytes).hexdigest()

    return UploadArtifact(
        filename=filename,
        content_type=upload.content_type,
        raw_bytes=raw_bytes,
        text=text,
        checksum=checksum,
    )


def extract_text(raw_bytes: bytes, suffix: str) -> str:
    if suffix in SUPPORTED_TEXT_SUFFIXES:
        return raw_bytes.decode("utf-8", errors="ignore")

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(raw_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(page.strip() for page in pages if page.strip())

    raise ValueError(f"Unsupported suffix: {suffix}")

