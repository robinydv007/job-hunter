"""BM25-based keyword retriever — no embeddings, pure text matching."""

from typing import List, Tuple
from rank_bm25 import BM25Okapi
import re


class BM25Retriever:
    """Retrieves relevant text chunks using BM25 keyword ranking."""

    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self.bm25 = None
        self.chunks: List[Tuple[str, str]] = []  # (chunk, source)

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, split on non-alphanumeric."""
        return re.findall(r"[a-z0-9]+", text.lower())

    def add_chunks(self, chunks: List[Tuple[str, str]]):
        """Add document chunks to the index."""
        self.chunks.extend(chunks)
        tokenized = [self._tokenize(chunk) for chunk, _ in self.chunks]
        self.bm25 = BM25Okapi(tokenized)

    def retrieve(self, query: str) -> List[Tuple[str, str, float]]:
        """Retrieve top-k most relevant chunks for a query.

        Returns list of (chunk, source, score) tuples.
        """
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        scored = []
        for i, (chunk, source) in enumerate(self.chunks):
            if scores[i] > 0:
                scored.append((chunk, source, float(scores[i])))

        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[: self.top_k]

    def reset(self):
        """Clear all indexed chunks."""
        self.bm25 = None
        self.chunks = []
