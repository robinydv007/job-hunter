"""Tests for DocumentProcessor."""

import os
import tempfile
import pytest
from src.document_processor import DocumentProcessor


class TestDocumentProcessor:
    def setup_method(self):
        self.processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)

    def test_chunk_text_basic(self):
        text = "A" * 120
        chunks = self.processor.chunk_text(text)
        assert len(chunks) >= 2
        assert all(len(c) <= 50 for c in chunks)

    def test_chunk_text_empty(self):
        assert self.processor.chunk_text("") == []
        assert self.processor.chunk_text("   ") == []

    def test_chunk_text_overlap(self):
        text = "The quick brown fox jumps over the lazy dog"
        chunks = self.processor.chunk_text(text)
        assert len(chunks) >= 1

    def test_extract_text_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello world")
            tmp_path = f.name
        try:
            result = self.processor.extract_text(tmp_path)
            assert result == "Hello world"
        finally:
            os.unlink(tmp_path)

    def test_extract_md_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Hello\n\nWorld")
            tmp_path = f.name
        try:
            result = self.processor.extract_text(tmp_path)
            assert "Hello" in result
        finally:
            os.unlink(tmp_path)

    def test_extract_unsupported_type(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
            f.write("test")
            tmp_path = f.name
        try:
            with pytest.raises(ValueError, match="Unsupported"):
                self.processor.extract_text(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_process_file_returns_chunks_with_source(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("A" * 120)
            tmp_path = f.name
        try:
            results = self.processor.process_file(tmp_path)
            assert len(results) >= 1
            for chunk, source in results:
                assert isinstance(chunk, str)
                assert isinstance(source, str)
                assert len(chunk) > 0
        finally:
            os.unlink(tmp_path)
