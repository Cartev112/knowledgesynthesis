from __future__ import annotations

from pathlib import Path


# Look for sample input file in project root (4 levels up from this file: core -> app -> python_worker -> backend -> root)
project_root = Path(__file__).parent.parent.parent.parent.parent
HARD_CODED_INPUT = project_root / "data" / "sample" / "input.txt"


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



