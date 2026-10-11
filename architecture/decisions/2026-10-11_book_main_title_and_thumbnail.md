# 2026-10-11 — The book's main title and thumbnail

**Status:** APPROVED (owner, 2026-10-11: "Build it"; Sherlock waits for it, one upload per book). BUILT 2026-10-11.

## The ask (owner, 2026-10-11)
Every book gets a main title for the whole book: 5–8 s, movie-style, and
completely different from the chapter-card animation. It opens the book video,
which runs each chapter title first, then the chapter. The book video also
gets a 16:9 custom thumbnail. This applies to WotW now and to every future book.
It costs $0 and needs no human input.

## The debate
Three designers worked from the same brief, and one judge checked their claims
in the repo.

| Design | Idea | Score /60 |
|---|---|---|
| A, Classic Epic | key art + H3, gold engraved lettering drawn by Ideogram, OCR'd, composited | 33 |
| B, the book's own world | a cold-open montage cut from the shipped Shorts, PIL title, 2.39 matte, ~5 GPU min | 41 |
| **C, reliability first** | **no model ever draws a letter**: Krea2 text-free plate + H3 push-in, PIL type in a vendored OFL font | **45** |

What the judge verified in the repo:
- **C's evidence holds.** Model lettering broke again and again: "WHE THE WORLDS", sideways plates, quote marks. ep17 failed all six seeds (`title/lettered_5200..5205.png`). The OCR reads the still, never the H3 frames that ship.
- **B's picker had no data.** It leaned on `motion_quality.json`, which exists for WotW ep02–05 only.
- **A reuses the chain that failed.** Its gold Roman capitals are also the chapter cards' family.

## The decision: C, with B's cold open and a widescreen band
**Picture, 7.0 s at 24 fps, inside the book's square:**
- A 2.39 band inside the square, black above and below. The chapter cards are full-bleed, so the band alone sets the title apart.
- Bleach-bypass grade plus grain.

| Time | What plays |
|---|---|
| 0.00–2.50 | **Cold open:** 5 segments, each shorter than the last, one from each fifth of the book, cut from the shipped Shorts. They are picked from `placed.json` plus measured sharpness and motion, then a VLM checks them for lettering and signature props. |
| 2.50–2.92 | Black, landing on the sting's measured hit |
| 2.92–3.80 | "THE KEEPER'S LANTERN PRESENTS" |
| 3.80–7.00 | **The hero:** a Krea2 text-free key-art plate, H3 i2v push-in. The PIL title tracks in, with a rule and the author line under it. |

**Lettering:**
- PIL only, cold white condensed sans in a vendored OFL font with its licence.
- The title string comes from the book's own data, never from an LLM.
- `fit_lines` handles long titles; a glyph check runs against the font.

**Sound:**
- An ACE-Step instrumental sting (`audio_acestep15_music`). The cut lands on its onset.
- If no onset is found or loudness fails, a synthesised riser + boom is used instead.

**Thumbnail:**
- A Krea2 16:9 plate of the same motif, with the title set by PIL and "FULL ADAPTATION · N EPISODES".
- Uploaded with `thumbnails().set`. A 403 (unverified channel) is recorded and never blocks.

**Timestamps:**
- The title folds into Ep 1's chapter. 0:00 stays Ep 1, and later stamps shift by the title's measured length.
- A 7 s chapter would make YouTube drop every chapter.

**Gate G-BOOKTITLE, judge-signed:**
- *Refuses on:* a glyph missing, the title outside the safe area, contrast below 7:1, ≠168 frames, LUFS outside ±1, stream params ≠ the chapter pieces, or a lettered cold-open segment.
- *Flags on:* an OCR misread of the final encode, or distinctness vs the cards.

**Never parks:**
- If the H3 render fails, the hero becomes a zoompan over the still.
- If no cold-open segment survives, the cold open is dropped and the title runs 4.5 s.

**Code and runtime:**
- *Files:* `studio/book_title.py` (pure), `scripts/episode/book_title.py` (`ensure(book)`), and output under `library/<book>/title/book/`.
- *Runs:* `book_compilation` calls `ensure()` before the join. One shared `encode_args` comes out of `cut_argv`.
- *Cost:* about 15–20 GPU min per book, $0.

**Publishable:** a book-neutral movie-title engine. Diffusion paints, code spells, and a VLM checks the cold open. It can ship as a standalone package.
