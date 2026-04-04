# Phase 1 — Vectorless RAG: Implementation History
Append-only log. Do NOT edit existing entries. Add new entries at the bottom.
Agent appends automatically when significant changes occur.
Use `/log` to add a manual entry at any time.

## Entry Types
| Type | When to use |
|------|------------|
| [DECISION] | ADR created or updated, technology choice made |
| [SCOPE_CHANGE] | Phase deliverables added, removed, or reprioritized |
| [DISCOVERY] | Bug, tech debt, or enhancement found |
| [FEATURE] | New planned feature added to this phase |
| [ARCH_CHANGE] | Architectural pattern or integration changed |
| [NOTE] | Anything else worth recording |

## Entry Format
```
[TYPE] YYYY-MM-DD — Short title (max 10 words)
Topics: topic-1, topic-2
Affects-phases: phase-N-name (or "none")
Affects-docs: path/to/doc.md#section (or "none")
Detail: What changed and why.
```

## Entries

[FEATURE] 2026-04-02 — Phase 1 started: Vectorless RAG Chatbot
Topics: rag, bm25, streamlit, document-processing, llm-integration
Affects-phases: phase-1-vectorless-rag
Affects-docs: specs/phases/phase-1-vectorless-rag/overview.md, specs/phases/phase-1-vectorless-rag/plan.md
Phase 1 scope: build a simple RAG application using BM25 keyword retrieval (no embeddings) with Streamlit UI. Users upload documents and ask questions, chatbot answers with source citations.

[ARCH_CHANGE] 2026-04-02 — Vectorless RAG implementation complete
Topics: rag, bm25, streamlit, document-processing, llm-integration
Affects-phases: phase-1-vectorless-rag
Affects-docs: README.md, app.py, src/document_processor.py, src/retriever.py, src/chat_engine.py
Built all 4 components: DocumentProcessor (PDF/TXT/MD extraction + chunking), BM25Retriever (keyword-based retrieval), ChatEngine (OpenAI/Anthropic integration), Streamlit UI (upload + chat + source citations). Added unit tests for all components. Fixed BUG-007 (duplicate commands in opencode.json).
