# Phase 1: Vectorless RAG Chatbot — Implementation Plan

## Approach
Build a single-page Streamlit application with three components:
1. **DocumentProcessor** — handles file upload, text extraction, and chunking
2. **BM25Retriever** — keyword-based retrieval using the rank_bm25 library (no embeddings)
3. **ChatEngine** — sends query + retrieved context to an LLM and returns answers

The "vectorless" approach means we skip embeddings entirely. Instead:
- Documents are split into text chunks
- User queries are tokenized and matched against chunks using BM25 (a proven keyword ranking algorithm)
- Top-k most relevant chunks are sent to the LLM as context
- The LLM generates an answer based only on the provided context

## File Structure
```
├── app.py                    # Streamlit UI (main entry point)
├── src/
│   ├── __init__.py
│   ├── document_processor.py # Text extraction + chunking
│   ├── retriever.py          # BM25 keyword-based retrieval
│   └── chat_engine.py        # LLM integration + answer generation
├── tests/
│   ├── __init__.py
│   ├── test_document_processor.py
│   ├── test_retriever.py
│   └── test_chat_engine.py
├── requirements.txt
├── .env.example
└── README.md
```

## Implementation Steps
1. **Setup** — requirements.txt, .env.example, project structure
2. **DocumentProcessor** — extract text from PDF/TXT/MD, chunk with overlap
3. **BM25Retriever** — tokenize, build BM25 index, retrieve top-k chunks
4. **ChatEngine** — LLM integration, prompt template, source citations
5. **Streamlit UI** — file upload, chat interface, answer display
6. **Tests** — unit tests for each component
7. **Documentation** — README with setup and usage instructions

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM API key not available | Medium | High | Support multiple providers (OpenAI, Anthropic); clear .env.example |
| BM25 performs poorly on short queries | Medium | Medium | Use query expansion (add synonyms); allow adjusting top-k |
| Large documents exceed LLM context window | Low | Medium | Chunk size tuned to fit within context limits; summarize if needed |
| PDF extraction fails on scanned documents | Medium | Low | Warn user; support only text-based PDFs for v1 |

## Dependencies
- Python 3.10+
- LLM API key (OpenAI or Anthropic)
- pip packages: streamlit, rank_bm25, PyPDF2, python-docx, python-dotenv, openai or anthropic
