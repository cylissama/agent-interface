from pathlib import Path


def read_file(path: Path, encoding: str = "utf-8") -> str:
    """Read a text file with fallback error handling."""
    return path.read_text(encoding=encoding, errors="ignore")
