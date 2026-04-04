# Spec-Driven Development Project

A project management system for spec-driven development with AI agents.

## Current Project: Vectorless RAG Chatbot

This repo also contains a **Vectorless RAG Chatbot** — a document-based Q&A application using BM25 keyword search (no embeddings).

### Quick Start

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Set up API key:** `cp .env.example .env` and add your key
3. **Run the app:** `streamlit run app.py`

See the full [RAG README](#vectorless-rag-chatbot-1) below for details.

---

## SDD Workflow

This repository uses a **spec-driven development (SDD)** workflow where:
- Every phase of work is planned before coding starts
- AI agents and developers share the same source of truth (`specs/`)
- Tracking is automatic — agents update status, changelog, and tasks as they work
- Phase history captures decisions and discoveries as they happen
- Git discipline is built in — automatic branching, atomic commits, safe merges

### Quick Start (SDD)

1. Read `specs/status.md` to understand the current state
2. Read `docs/developer-guideline.md` for how to work with this system
3. Run `/start-phase` to begin a new phase

### Structure

| Path | Purpose |
|------|---------|
| `specs/` | Single source of truth — status, backlog, phases, decisions, roadmap |
| `docs/` | Developer documentation and vision |
| `.opencode/commands/` | Slash commands for phase workflows |
| `.opencode/plugins/` | Event hooks (history reminder, automation) |
| `opencode.json` | Project config (commands, instructions, plugins) |
| `.agent/rules/` | Agent operational rules |
| `scripts/` | Automation hooks |

### Key Commands

| Command | Purpose |
|---------|---------|
| `/start-phase` | Begin a new implementation phase |
| `/complete-phase` | Verify and release a completed phase |
| `/sync-docs` | Propagate phase history to docs |
| `/log` | Record a manual history entry |
| `/track` | Add a backlog item |
| `/review` | Groom the backlog between phases |

### Development Cycle

```
DISCOVER → PLAN → IMPLEMENT → VERIFY → SYNC → RELEASE
```

See `docs/developer-guideline.md` for the complete guide.

---

## Vectorless RAG Chatbot

A simple document-based Q&A application that uses **keyword search (BM25)** instead of vector embeddings for retrieval.

### How It Works

```
Upload Documents → Extract Text → Chunk → BM25 Index → Ask Question → Retrieve Top-K → LLM Answer
```

### Setup

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Set up your API key:** `cp .env.example .env`
3. **Run the app:** `streamlit run app.py`

### Architecture

```
app.py (Streamlit UI)
├── src/document_processor.py  — Text extraction + chunking
├── src/retriever.py           — BM25 keyword-based retrieval
└── src/chat_engine.py         — LLM integration + answer generation
```

### Why No Embeddings?

BM25 keyword search is simpler, faster, and more transparent than embedding-based retrieval. For most document Q&A use cases, it performs comparably.
