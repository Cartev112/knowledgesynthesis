from __future__ import annotations

from pathlib import Path


HARD_CODED_INPUT = Path("data/sample/input.txt")


def read_text_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore")


def extract_text_from_path(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return read_text_file(file_path)

    # Placeholder for future formats (e.g., PDF)
    # For now, keep scope limited to .txt in Phase 1
    raise ValueError(f"Unsupported file type: {suffix}")



