"""Document processor — extracts text from PDF/TXT/MD files and chunks it."""

import os
from typing import List, Tuple
from PyPDF2 import PdfReader


class DocumentProcessor:
    """Extracts text from documents and splits into chunks."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text(self, file_path: str) -> str:
        """Extract text from a file based on its extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self._extract_pdf(file_path)
        elif ext in (".txt", ".md"):
            return self._extract_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)

    def _extract_text_file(self, file_path: str) -> str:
        """Extract text from a TXT or MD file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if not text or not text.strip():
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start = end - self.chunk_overlap
        return chunks

    def process_file(self, file_path: str) -> List[Tuple[str, str]]:
        """Process a file and return list of (chunk, source) tuples."""
        filename = os.path.basename(file_path)
        text = self.extract_text(file_path)
        chunks = self.chunk_text(text)
        return [(chunk, filename) for chunk in chunks]
