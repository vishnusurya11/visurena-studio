# Mockups — the premium board (static, for review)

Serve: `uv run --no-project python -m http.server 8710 --bind 127.0.0.1` from this folder, then open
http://127.0.0.1:8710/ . Pictures come live from the running board (http://127.0.0.1:8700/thumb/...).
Shared design system: `assets/board.css` (tokens + components, SPEC.md), `assets/icons.svg` (Lucide sprite).
Data is real, captured read-only from the ledger and library on 2026-10-04; nothing here writes.
