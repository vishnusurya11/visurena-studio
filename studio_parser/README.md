# Studio Parser

Project Gutenberg book parser for Visurena Studio. Downloads books by ID, parses across multiple formats, and extracts individual stories as JSON.

## Setup

```bash
cd studio_parser
uv sync
```

## Usage

```bash
# Parse a book by PG ID
uv run python -m studio_parser pg634

# With OpenRouter instead of Ollama
uv run python -m studio_parser pg160 --provider openrouter --model qwen/qwen3-30b

# With a specific Ollama model
uv run python -m studio_parser pg174 --model phi4-reasoning

# Custom config file
uv run python -m studio_parser pg160 --config /path/to/config.yaml
```

## Output

- **JSON files**: `output/stories/{book_id}/{story_slug}.json`
- **Database**: `D:\Projects\GlobalDatabases\visurena_studio.db` → `parsed_stories` table

## Configuration

Edit `config.yaml` or use environment variables:

```bash
export STUDIO_PARSER_LLM_PROVIDER=openrouter
export STUDIO_PARSER_OPENROUTER_API_KEY=sk-...
export STUDIO_PARSER_OUTPUT_DIR=/custom/output/path
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.
