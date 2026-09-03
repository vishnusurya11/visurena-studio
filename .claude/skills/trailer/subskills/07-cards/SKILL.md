---
name: trailer-cards
description: Title and quotation cards - typography, timing, animation, and two silent failures.
---

# Text cards

`studio/trailer_assemble.py` (`ass_title`, `wrap_title`, `card_fits`).

## Two bugs that shipped, both silent

**1. The fade never fired.** `f"{{\fad(...)}}"` — `\f` is a Python escape,
FORM FEED. libass discards an unrecognised override block in silence, and the
control character even split the Dialogue line. Every card hard-cut in at full
white. **Every ASS string is a raw string**, and a test asserts no codepoint
< 0x20 survives. Most of the vocabulary collides: `\fad \fsp \fs \frz \fn` →
form feed, `\t` → tab, `\bord \blur` → backspace, `\alpha \an` → BEL.

The test asserted `"\fad("` in a non-raw string too, so it searched for the
same form feed and passed against a card that never faded. **A test written
with the same bug as the code cannot catch it.**

**2. The Jekyll title shipped clipped off both edges** — "GE CASE OF DR.
JEKYLL AND", the film's own name unreadable in a delivered file. `WrapStyle: 2`
disables libass wrapping, so a long title has no way to fail except by running
off. Nothing measured the card after rendering it.

`card_fits()` now decodes a frame, measures the ink bbox and REFUSES above 90%
of frame width. The old single-line render measures 1323px of 1344 with a 3px
margin and fails, as it should.

## Typography

| | value |
|---|---|
| face | Bookman Old Style — genuinely Victorian (ATF 1901), low enough stroke contrast to survive H.264 |
| cap height | 5.0% of frame height (`H//13`) |
| tracking | **0.20 em**, not 0.37 — all-caps convention is ~0.1em, film titles 0.2-0.3 |
| colour | warm off-white `&H00DAE6ED`, not `#FFFFFF` |
| centring | `MarginL = MarginR + tracking` — libass counts the final glyph's trailing letter-space, so a centred tracked line sits tracking/2 left |

Assert the font file exists: libass substitutes a missing face **without
warning**, the same class as PIL's default bitmap font.

Never end a wrapped line on an honorific — "DR" / "JEKYLL" reads as a typo.

## Fewer cards than you think

Lieu: title cards "tell, rather than show" and are "an easy way to make a
trailer look very generic". But for a public-domain adaptation there is one
legitimate exception: **the author's own sentence**. Stevenson's prose is not a
marketing claim, it IS the thing being adapted.

So: 0-2 cards beyond the title, and both must be quotation. Split one sentence
across two cards, setup and turn — "MAN IS NOT TRULY ONE" / "BUT TRULY TWO",
the second hard-cutting on a measured impact so the turn in the sentence and
the turn in the music are the same event.

Signage cards ≤3 words. Quotation ≤12 words, ≤2 lines. Hold = `0.55 x words +
0.5s` on black, floor 1.4s.

**Cut in on a hit; fade up in a trough.** Fading in on a hit smears the attack.
Logos belong on the END slate, ≤1s, never at the head.
