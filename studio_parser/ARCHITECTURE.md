# Studio Parser — Architecture

## Overview

Studio Parser is a standalone module within Visurena Studio (Step 1) that downloads Project Gutenberg books by ID, parses them across multiple formats, reconciles the best parse, extracts individual short stories with full metadata, and persists results as JSON files + SQLite rows.

## System Flow

```
book_id (e.g., "pg160")
  │
  ▼
┌─────────────┐
│ downloader   │  Downloads 4 format variants from PG:
│              │  HTML, EPUB2, EPUB2+images, EPUB3+images
│              │  → output/downloads/{book_id}/
└──────┬──────┘
       ▼
┌─────────────┐
│ parsers/*    │  Runs up to 7 parse strategies:
│              │  • html_parser (HTML div.chapter)
│              │  • epub_divchapter × 3 formats
│              │  • epub_toc × 3 formats (NCX/nav-based)
└──────┬──────┘
       ▼
┌─────────────┐
│ reconciler   │  For each unique work title:
│              │  1. Deterministic: highest word count + most paragraphs
│              │  2. LLM tiebreak if top-2 within 5% (optional)
└──────┬──────┘
       ▼
┌─────────────┐
│ splitter     │  Extracts individual StoryOutput objects
│              │  from reconciled Works
└──────┬──────┘
       ▼
┌─────────────┐
│ quality_agent│  LLM scores each story 0-100 (optional)
└──────┬──────┘
       ▼
┌─────────────┐
│ output       │  Writes JSON: output/stories/{book_id}/{slug}.json
│              │  Upserts DB: visurena_studio.db → parsed_stories
└─────────────┘
```

## Module Structure

```
studio_parser/
├── config.py          Config loading: YAML + env vars + CLI overrides
├── models.py          Pydantic v2: Chapter, Work, ParseResult, StoryOutput
├── downloader.py      PG download (4 formats, urllib.request)
├── db.py              SQLite: parsed_stories table, upsert
├── reconciler.py      Multi-format merge (deterministic + LLM fallback)
├── splitter.py        Work → individual StoryOutput
├── output.py          JSON writing + DB insertion
├── cli.py             CLI args + orchestration pipeline
├── parsers/
│   ├── base.py        Shared: clean_text, is_boilerplate, parse_div_chapters
│   ├── html_parser.py HTML div.chapter parser
│   ├── epub_reader.py EPUB reading: OPF, spine, TOC (NCX + nav)
│   ├── epub_divchapter.py  EPUB div.chapter parser
│   └── epub_toc.py    EPUB TOC-based parser (anchor extraction)
└── agent/
    ├── llm_provider.py    Factory: ChatOllama or ChatOpenAI (swap point)
    ├── prompts.py         Prompt templates for merge + quality
    ├── merge_agent.py     LLM reconciliation between close candidates
    └── quality_agent.py   LLM quality scoring (0-100)
```

## Parsing Strategies

### Approach A: div.chapter (heuristic)
- Finds `<div class="chapter">` elements
- Uses `<h2>` for work titles, `<h3>` for chapter titles
- Collects `<p>` tags between headings
- Works for both HTML and EPUB content

### Approach B: TOC-based (structural)
- Uses EPUB's built-in Table of Contents as source of truth
- EPUB3: parses `toc.xhtml` (nav element)
- EPUB2: fallback to `toc.ncx` (NCX format)
- Extracts paragraphs between anchor IDs
- More reliable for properly structured EPUBs

## LLM Integration

- **Default model**: `gpt-oss:20b` via Ollama
- **Alternative**: `phi4-reasoning` for heavier reasoning
- **Switch to OpenRouter**: Set `STUDIO_PARSER_LLM_PROVIDER=openrouter` + API key
- **All LLM calls are optional** — system works fully without LLM via deterministic logic
- **Single swap point**: `agent/llm_provider.py`

## Database

Table `parsed_stories` in `visurena_studio.db`:
- Keyed on `(book_id, story_title)` — idempotent re-runs via UPSERT
- Stores: word count, paragraph count, chapter count, format source, JSON path, quality score
- Does NOT modify existing `schedule` or `schedule_runs` tables

## Configuration Priority

CLI flags > Environment variables > config.yaml > Defaults

Key env vars:
- `STUDIO_PARSER_LLM_PROVIDER` — "ollama" or "openrouter"
- `STUDIO_PARSER_OPENROUTER_API_KEY`
- `STUDIO_PARSER_OLLAMA_MODEL`
- `STUDIO_PARSER_OUTPUT_DIR`
- `STUDIO_PARSER_DB_PATH`
