# Phase 1 Tasks
**Status**: Not Started | **Progress**: 0/8 tasks

* [ ] **Setup project structure**
    * Create requirements.txt, .env.example, src/, tests/ directories
    * Verification: `pip install -r requirements.txt` succeeds
* [ ] **Build DocumentProcessor**
    * Extract text from PDF (PyPDF2), TXT, MD files
    * Chunk text into segments (500 chars, 50 char overlap)
    * Verification: test with sample PDF and TXT files
* [ ] **Build BM25Retriever**
    * Tokenize chunks and queries
    * Build BM25 index from chunks
    * Retrieve top-k most relevant chunks for a query
    * Verification: search returns relevant chunks for test queries
* [ ] **Build ChatEngine**
    * Integrate with LLM API (OpenAI or Anthropic)
    * Create prompt template with system instructions and context
    * Return answer with source document references
    * Verification: answers are grounded in provided documents
* [ ] **Build Streamlit UI**
    * File upload sidebar (multiple files)
    * Chat interface with message history
    * Display answers with source citations
    * Verification: full flow works — upload → ask → answer
* [ ] **Write tests**
    * Unit tests for DocumentProcessor, BM25Retriever, ChatEngine
    * Verification: `pytest tests/` passes
* [ ] **Write README**
    * Setup instructions, usage guide, architecture overview
    * Verification: a new user can run the app following README
* [ ] **Fix BUG-007: Remove duplicate command definitions**
    * Remove `command` block from opencode.json (keep .opencode/commands/*.md files)
    * Verification: opencode.json is valid, commands still work from .opencode/commands/
