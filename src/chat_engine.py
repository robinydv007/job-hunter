"""Chat engine — integrates with LLM to generate answers from context."""

import os
from typing import List, Tuple
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based ONLY on the provided documents.

Rules:
1. Answer ONLY using information from the context provided below.
2. If the answer cannot be found in the context, say "I cannot find information about this in the provided documents."
3. Always cite which document your answer comes from.
4. Be concise and direct.

Context:
{context}
"""


class ChatEngine:
    """Generates answers using an LLM with document context."""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._client = None

    def _get_client(self):
        """Lazy-load the LLM client."""
        if self._client is not None:
            return self._client

        if self.provider == "openai":
            from openai import OpenAI

            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "anthropic":
            import anthropic

            self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        return self._client

    def _build_prompt(
        self, query: str, context_chunks: List[Tuple[str, str, float]]
    ) -> str:
        """Build the prompt with context and query."""
        context_text = ""
        for i, (chunk, source, score) in enumerate(context_chunks, 1):
            context_text += f"[Document: {source}]\n{chunk}\n\n"

        return SYSTEM_PROMPT.format(context=context_text) + f"\nQuestion: {query}"

    def answer(self, query: str, context_chunks: List[Tuple[str, str, float]]) -> str:
        """Generate an answer based on retrieved context.

        Args:
            query: The user's question
            context_chunks: List of (chunk, source, score) from retriever

        Returns:
            The LLM's answer string
        """
        if not context_chunks:
            return "No relevant documents found. Please upload documents related to your question."

        client = self._get_client()
        prompt = self._build_prompt(query, context_chunks)

        if self.provider == "openai":
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        raise ValueError(f"Unsupported provider: {self.provider}")
