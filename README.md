# Visurena Studio

Visurena Studio turns public-domain books into serialized YouTube Shorts. Each
episode covers one chapter. It is a square (1:1) short, at most 3 minutes long,
with the book's narrator, a few spoken lines and pictures cut to the recorded
voice. Every step runs locally on one GPU (ComfyUI, local text-to-speech and
local vision checks), so an episode costs $0 in API credits.

The studio is organized like a company:

- **Code is management.** Runners and step scripts decide the order of work,
  write the briefs, assemble the output and run the gates.
- **Agents are specialists.** Each one takes a brief and returns one typed
  object.
- **`stages.yaml` is the org chart** that the code runs.

The unit of work is the **Step**. A step has a deterministic identity
(`production_id + step_name + input_hash`), reads earlier artifacts, writes one
artifact, has a known cost, and passes a gate. A department is a list of steps,
and a production is a DAG of them. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Architecture

- [architecture/index.html](architecture/index.html) is the architecture page.
  Open it in a browser. It shows the current org chart, the proposed future
  one, and an animated run of one book.
- Published copy: https://claude.ai/artifact/6HCxs36mcpFk2TJS389QXr
- [architecture/README.md](architecture/README.md) indexes the departments,
  decisions and plans.
- [docs/DECISIONS.md](docs/DECISIONS.md) logs every decision with its reason.

## Install

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/vishnusurya11/visurena-studio.git
cd visurena-studio
uv sync                 # core dependencies + the dev group (pytest)
uv sync --all-groups    # adds the measures, music and voice groups
```

All dependencies are pinned exactly (`==`) in `pyproject.toml`. Rendering an
episode also needs a local ComfyUI with the models its workflows name. Those
models are not part of this repository, and each one has its own licence.

## Run the tests

```sh
uv run pytest -q
```

No test calls a paid API or spends a credit. LLM steps are tested with a fake
model that returns canned structured output, and media steps are tested with
recorded fixtures. Tests marked `local` need ComfyUI or a model on disk, and
tests marked `rehearsal` run the real pipeline in a sandbox. Both are left out
of the default run. Opt in with `-m local` or `-m rehearsal`.

## One measured result

The episode capacity model (`studio/episode_capacity.py`) predicts an episode's
machine time from its shot count. It was priced on one clean 26-shot run
(*The War of the Worlds*, ep25). For a 23-shot plan it projected **5.0 h**.
The run it was checked against, *Jekyll & Hyde* ep01, measured **4.99 h** on
the episode clock. This is one out-of-sample check (n = 1), not a benchmark.
The same model sets the shot cap: 30 shots would fit (5.91 h), and the cap is
28 (5.65 h) to leave a margin inside the 6-hour machine budget.

Source: [docs/DECISIONS.md](docs/DECISIONS.md), entry 2026-10-17 (the grammar's
numbers), and the docstring of `studio/episode_capacity.py`.

## The channel

The episodes are published on the YouTube channel **The Keeper's Lantern**.

## AI disclosure

- **Episodes:** the pictures and the voices are generated. The words are the
  original author's public-domain text, adapted, and the performances are
  synthetic. Every upload declares this to YouTube
  (`status.containsSyntheticMedia`) and states it in its description
  (`scripts/publish/metadata.py`).
- **Code:** much of the code in this repository was written with AI
  assistance (Claude Code). Those commits carry a `Co-Authored-By` line.

## Licence

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
Copyright 2026 ViSuReNa (vishnusurya11).
