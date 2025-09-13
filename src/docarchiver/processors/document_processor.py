import re
from pathlib import Path
from typing import List, Optional

# Lazy import: PyMuPDF
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

# DOCX
try:
    from docx import Document
except Exception:
    Document = None

# Optional: KoNLPy (not required for base functionality)
try:
    from konlpy.tag import Okt  # noqa: F401
except Exception:
    Okt = None


class DocumentProcessor:
    """Document preprocessing and text extraction."""

    def __init__(self):
        self.okt = Okt() if Okt else None

    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF, DOCX, or TXT."""
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf(file_path)
        if suffix == ".txt":
            return Path(file_path).read_text(encoding="utf-8", errors="ignore")
        if suffix == ".docx":
            return self._extract_docx(file_path)
        raise ValueError(f"Unsupported file format: {suffix}")

    def _extract_pdf(self, file_path: str) -> str:
        if not fitz:
            raise ImportError("PyMuPDF (fitz) is not installed.")
        text = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text.append(page.get_text())
        return "\n".join(text)

    def _extract_docx(self, file_path: str) -> str:
        if not Document:
            raise ImportError("python-docx is not installed.")
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    def preprocess(self, text: str) -> List[str]:
        """Basic cleanup and sentence segmentation."""
        cleaned = self._remove_noise(text)
        # naive segmentation by newlines
        sentences = [s.strip() for s in cleaned.split("\n") if s.strip()]
        return sentences

    def _remove_noise(self, text: str) -> str:
        lines = text.split("\n")
        out = []
        for line in lines:
            if not self._is_noise(line):
                out.append(line)
        return "\n".join(out)

    def _is_noise(self, line: str) -> bool:
        line = line.strip()
        if len(line) < 5:
            return True
        # page number / numeric-only lines
        if line.isdigit():
            return True
        # headers/footers like "Page 1/10", dates, etc. (very naive)
        if re.match(r"^Page\s+\d+(/\d+)?$", line, flags=re.I):
            return True
        return False
