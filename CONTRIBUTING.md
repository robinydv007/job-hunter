# Contributing to Job Hunter Agent

Thanks for your interest in contributing to Job Hunter Agent!

## Development Process

This project uses aSpec-Driven Development (SDD) approach. All work is planned, tracked, and documented before code is written.

### Key Files

| File | Purpose |
|------|---------|
| `specs/status.md` | Current phase and progress |
| `specs/backlog/backlog.md` | Planned features and bugs |
| `specs/phases/` | Per-phase task lists |

### How Development Works

1. **Planning** — Features are spec'd in `specs/` before implementation
2. **Tracking** — Tasks are tracked in phase-specific `tasks.md`
3. **History** — Changes are logged to phase `history.md`
4. **Code Quality** — Lint and type checks pass before commit

### Setting Up Development Environment

```bash
# Clone and setup
git clone https://github.com/yourusername/job-hunter.git
cd job-hunter

# Virtual environment
uv venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Install
uv pip install -e .
uv pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
```

### Making Changes

1. Branch from `staging` or `main`
2. Make changes following existing code patterns
3. Update relevant spec tracking if adding features
4. Commit with conventional format: `feat(scope): description`
5. Push and create a pull request

### Code Style

- **Format**: Follow existing patterns in `src/job_hunter/`
- **Types**: Use Pydantic models for data validation
- **Tests**: Add tests for new functionality
- **Docs**: Update README if user-facing changes

### Commit Convention

```
feat(scope): new feature
fix(scope): bug fix
refactor(scope): code restructuring
docs: documentation only
chore: build/tooling changes
```

## Questions?

- Open an issue for bugs or feature requests
- Discussions open for general questions

## Recognition

Contributors will be added to the README acknowledgments section.

---

*This project is part of a portfolio demonstration. PRs may not be merged but all contributions are appreciated.*