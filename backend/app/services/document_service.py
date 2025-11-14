from pathlib import Path

from fastapi import UploadFile


def save_upload(file: UploadFile, upload_dir: Path) -> Path:
    """Persist an uploaded file to disk."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / file.filename
    with destination.open("wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            buffer.write(chunk)
    return destination


def extract_text(path: Path) -> str:
    """Placeholder text extraction logic."""
    return path.read_text(encoding="utf-8", errors="ignore")
