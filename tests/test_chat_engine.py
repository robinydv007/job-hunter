"""Tests for ChatEngine."""

import os
import pytest
from src.chat_engine import ChatEngine


class TestChatEngine:
    def setup_method(self):
        self.engine = ChatEngine()

    def test_no_context_returns_fallback(self):
        """When no context chunks provided, returns fallback message."""
        result = self.engine.answer("What is Python?", [])
        assert "No relevant documents" in result

    def test_build_prompt_includes_context(self):
        """Verify the prompt includes context chunks."""
        context = [
            ("Python is a programming language.", "python.txt", 2.5),
        ]
        # We can't test the full answer without an API key,
        # but we can verify the prompt building works
        prompt = self.engine._build_prompt("What is Python?", context)
        assert "Python is a programming language" in prompt
        assert "python.txt" in prompt
        assert "What is Python?" in prompt

    def test_build_prompt_multiple_chunks(self):
        """Verify multiple context chunks are included."""
        context = [
            ("Chunk one content", "doc1.txt", 3.0),
            ("Chunk two content", "doc2.txt", 2.0),
        ]
        prompt = self.engine._build_prompt("Test query", context)
        assert "Chunk one content" in prompt
        assert "Chunk two content" in prompt
        assert "doc1.txt" in prompt
        assert "doc2.txt" in prompt

    def test_unsupported_provider_raises_error(self):
        """Invalid provider should raise ValueError."""
        os.environ["LLM_PROVIDER"] = "invalid_provider"
        try:
            engine = ChatEngine()
            with pytest.raises(ValueError, match="Unsupported"):
                engine.answer("test", [("context", "file.txt", 1.0)])
        finally:
            os.environ["LLM_PROVIDER"] = "openai"
