# Engineering Principles
1. **Spec-Driven** — All work starts from specs, not code
2. **Incremental** — Small phases, frequent releases
3. **Documented** — Decisions captured as they happen
4. **Automated** — Let agents handle tracking and bookkeeping
5. **User In Control** — The system minimizes manual effort while allowing the user to dictate constraints via config files.
6. **Transparent** — Maintain full transparency over every decision made (e.g., CSV exports clearly stating "Why Selected").
7. **Resilient** — Web UI navigation and scraping are treated as fragile layers. Handle rate-limiting, bot detection, and form brittleness with resilient code and graceful degradation.
