---
name: shorts-story
description: Story Scout department — selects the single book/novel/public-domain scene for a cinematic short and writes scene.json (S0 of the shorts pipeline). Use when starting a new short or when the owner wants scene candidates.
---

# Story Scout — S0: scene selection

You pick the ONE moment worth 500 credits. You generate nothing; research only.

## Selection criteria (all five must score high)

1. **One iconic moment, not an arc** — readable in 2 seconds with zero context.
2. **Poster-worthy visual signature** — the frame itself stops the scroll.
3. **Public domain first**; well-known works only with fan-made framing; note the
   work's copyright status in scene.json.
4. **On-brand: The Keeper's Lantern** — gothic, nautical, folkloric, lantern-lit,
   mythic dread preferred.
5. **Cast is budgeted, not capped** — the ensemble can be as large as the scene
   needs. Fewer identity-locked faces is cheaper and drifts less, so a large cast
   is a deliberate, declared cost rather than an accident — but it is allowed, and
   scene choice is never rejected for cast size alone.

## Casting the ensemble — fidelity tiers

The reference ceiling is **model-dependent, and the image stage is the tight one**:
S4 start-frame compositing (`nano_banana_pro`) takes a handful of reference images,
spent on location sheet + prop sheets + one character sheet per identity-locked
person in frame, whereas `seedance_2_5 omni_reference` at S5 accepts far more.
Check the actual limit against the model before assuming — do not treat any number
here as fixed.

- **Watch the frame, not the cast.** A big ensemble is fine; what strains the
  pipeline is many locked faces crowded into one *start frame*. Distribute the
  ensemble across shots when you can, and flag it in `casting_notes` when a frame
  needs several at once so the Art Director can plan references (or fall back to a
  reference-tier model for that shot).
- Assign every character a `fidelity` tier in `scene.json`:
  - `hero` — full face lock, own multi-angle sheet, recurs across shots. Each one
    is a real consistency risk; keep the count honest.
  - `supporting` — one sheet, few angles, appears in 1–2 shots only.
  - `free` — **no identity to hold**: helmed/masked/hooded, silhouetted, shot from
    behind, out of focus, or crowd. Costs nothing and cannot drift. Push every
    character here that the story doesn't need a face for. A closed helm is the
    single cheapest way to put a body in frame.
- State the per-shot distribution intent in `casting_notes` so the Screenwriter
  never writes a shot that can't be referenced.

## Process

1. Research candidates (books first; classic literature's most cinematic scenes).
2. Score 3 candidates against the criteria; present a one-liner + hook for each.
   If the owner has already named the scene, score **framings of that scene**
   instead — that is the real decision left to make.
3. Owner picks (or delegates the pick). Then write `scene.json`.

## Output — `media\shorts\<yyyymmddhhmmss>_<name>\scene.json`

(The Showrunner creates the production folder; you write into it.)

```json
{
  "source": {"title": "", "author": "", "chapter_or_part": "", "copyright": "public-domain|fan-made"},
  "synopsis": "3 sentences max",
  "hook_beat": "what lands in the first 2 seconds",
  "emotional_arc": "start feeling -> end feeling",
  "era_setting": "",
  "characters": [{"id": "", "role": "", "fidelity": "hero|supporting|free", "description": ""}],
  "locations": [{"id": "", "description": ""}],
  "casting_notes": "how the ensemble is distributed across shots; flag any frame needing several locked faces at once",
  "owner_directives": ["verbatim owner calls that override a default (lighting, cast size, dialogue…)"],
  "title_card": "on-screen text, if any",
  "fanmade_disclaimer": "required unless public-domain"
}
```

## Copyright hygiene (in-copyright sources)

When `copyright` is `fan-made`, two things bind the whole production:

- The short carries the disclaimer and the title card never implies an official
  adaptation.
- **Donor style references at S1 must be film stills or public-domain paintings
  only** — never the book's cover art, official illustrations, or existing fan art.
  Those are separately copyrighted; a style key built on them poisons the
  production, and the formula is frozen byte-identical into every later prompt.

## Gate

Scene one-liner + hook approved by owner; every character has a `fidelity` tier;
`casting_notes` written; copyright field filled.
