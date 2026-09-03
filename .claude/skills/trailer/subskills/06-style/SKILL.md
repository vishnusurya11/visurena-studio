---
name: trailer-style
description: Visual register - the house look, and how to try others without losing consistency.
---

# Style

The house look so far is one register only: *"cinematic live-action photograph,
anamorphic widescreen, natural film grain, photoreal, muted desaturated
palette"* plus a per-book palette line. It works, and it is the only thing
tried.

## What is established

- **Krea 2 is Qwen-Image lineage, NOT FLUX.** FLUX Redux, PuLID-FLUX, FLUX
  IP-Adapter and Kontext do not load against it. Krea 2 Community License
  permits commercial use of model and outputs.
- `Krea2_Cinematic_Artstyle` LoRA is chained in both t2i workflows.
- **Put the SUBJECT before the style block.** With style leading, the palette
  dominates and the character description barely registers.
- **A style string in every prompt does NOT lock the look** — luma still spanned
  11.9-48.4 across clips. Consistency comes from the post grade-match against
  one hero clip, not from the prompt.
- The strongest generation-time lock is a **style LoRA on the base**, same
  musubi-tuner pipeline as a character LoRA.

## The open question

Whether a stylised reference image survives H3's reference conditioning, or
whether the video model — trained on photoreal data — drags everything back
toward photorealism. This is UNTESTED and it is the crux of any non-photoreal
register. Test it on one clip before committing a book to a style.

Style research is in flight; this file is the place to write the findings.
Per-book style belongs in `library/<book>/refs/refs.json` as `palette`, so the
trailer, song and episode inherit one look.
