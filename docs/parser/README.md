# studio_parser

**Status: deleted from the working tree, recoverable from commit `d060598`.**
Restoring and wrapping it as Steps is **P0**.

Parses Project Gutenberg books into individual short stories — the entry point for all
source content.

## What it does

Downloads a book, parses it across multiple formats (EPUB by TOC, EPUB by div/chapter,
HTML), reconciles the competing parses with an LLM, and writes stories to JSON plus a
`parsed_stories` table.

## Known facts

- Default model `gpt-oss:20b` on Ollama, switchable to OpenRouter
- Invoked as `uv run python -m studio_parser pg160` — the `160` is a Gutenberg id
- Output: `output/stories/{book_id}/{slug}.json`
- Writes to `D:\Projects\GlobalDatabases\visurena_studio.db` — **conflicts** with the
  in-repo `db/visurena_studio.db` decision; must be resolved before P0 lands

## P0 scope

Restore from `d060598`, migrate LLM calls onto the Strands gateway, wrap each stage as a
Step under TDD. Zero credits — it proves the runner on safe work.
