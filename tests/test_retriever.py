"""Tests for BM25Retriever."""

import pytest
from src.retriever import BM25Retriever


class TestBM25Retriever:
    def setup_method(self):
        self.retriever = BM25Retriever(top_k=3)

    def test_retrieve_empty_index(self):
        results = self.retriever.retrieve("any query")
        assert results == []

    def test_add_and_retrieve_chunks(self):
        chunks = [
            ("Python is a programming language", "python.txt"),
            ("JavaScript is used for web development", "js.txt"),
            ("Python has many libraries for data science", "python2.txt"),
        ]
        self.retriever.add_chunks(chunks)
        results = self.retriever.retrieve("Python programming")
        assert len(results) > 0
        assert results[0][1] == "python.txt"  # Most relevant

    def test_retrieve_returns_score(self):
        chunks = [
            ("The cat sat on the mat", "story.txt"),
        ]
        self.retriever.add_chunks(chunks)
        results = self.retriever.retrieve("cat mat")
        assert len(results) == 1
        chunk, source, score = results[0]
        assert isinstance(score, float)
        assert score > 0

    def test_top_k_limits_results(self):
        chunks = [
            (f"Document number {i} about topic {i}", f"doc{i}.txt") for i in range(10)
        ]
        self.retriever.add_chunks(chunks)
        results = self.retriever.retrieve("document topic")
        assert len(results) <= 3

    def test_reset_clears_index(self):
        chunks = [("Some text", "file.txt")]
        self.retriever.add_chunks(chunks)
        self.retriever.reset()
        results = self.retriever.retrieve("text")
        assert results == []

    def test_unrelated_query_returns_empty(self):
        chunks = [
            ("Python is great for data analysis", "python.txt"),
        ]
        self.retriever.add_chunks(chunks)
        results = self.retriever.retrieve("quantum physics black hole")
        assert results == []
