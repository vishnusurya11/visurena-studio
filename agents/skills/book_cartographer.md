# Skill: book cartographer — what are this book's real divisions? (analysis 01_03)

You are given every heading found in a cleaned book, with the evidence for judging it,
plus the table of contents. You return a **map**: what each heading actually is, and how
many divisions the book really has.

You never read the book. You judge evidence that has already been gathered.

---

## The one rule everything else derives from

**A book's structure is what its BODY does, not what its table of contents claims.**

The TOC is a claim by the publisher. The body is the book. When they disagree — and on
five of seven books tested they disagreed — **the body wins**, and your job is to say so
in a way the pipeline can act on.

This is why the deterministic matcher fails: it assumed TOC entries and body headings
correspond one to one. They routinely do not, in five distinct ways you must be able to
tell apart:

| what happened | how you recognise it |
|---|---|
| the TOC lists apparatus | an entry with no body heading, named Contents / Title / Note / License |
| a heading is split across lines | consecutive headings, the first with **no text under it** |
| one chapter is announced twice | two headings, same ordinal, one immediately after the other |
| **a heading is missing from the markup** | the TOC claims N, only N−1 headings exist, and one candidate's text is unusually long |
| the body has divisions the TOC omits | a heading with a clean `series` + `ordinal` and no TOC entry |

---

## The evidence you are given, and what each signal means

Per candidate:

- **`text`** — the heading as printed
- **`series` / `ordinal`** — what the numeral parser made of it. `null` means it parsed
  nothing, which is itself evidence: real chapters usually number.
- **`words_after`** — words of prose before the next heading. **This is your strongest
  signal.** A chapter has hundreds. A title fragment has zero. A contents page has few.
- **`preview`** — the first words of that prose. A chapter opens on narrative; a contents
  page opens on more headings.
- **`anchor_resolved`** — the TOC links directly to this heading. Strong evidence it is a
  real division.
- **`toc_title`** — its text matches a TOC entry exactly.
- **`signals`** — the above, collected.

**`words_after` near zero plus a following heading is a split heading, not a chapter.**
**`words_after` small and `preview` full of other headings is the contents page.**

---

## What you return, per candidate

A `role`, and you must choose exactly one:

| role | when |
|---|---|
| `chapter` | a real division of the narrative — the thing that gets numbered |
| `part` | a container that holds chapters. **Only when chapters follow it.** A heading reading "Part of the Plan" is a chapter title. |
| `front_matter` | preface, introduction, dedication, epigraph — real text, before the story |
| `back_matter` | afterword, note, appendix, colophon — real text, after the story |
| `contents` | the table of contents printed as body text |
| `title` | the book's own title or a fragment of it |
| `ignore` | anything else that is not a division |

**Number only the `chapter` roles, from 1, in reading order.** A book that opens with four
Letters and then twenty-four Chapters has **twenty-eight** divisions, and the letters are
chapters for this purpose — they carry narrative and the reader reads them in sequence.
Series is recorded separately; it does not change the count.

---

## When the body is missing a heading

If the TOC claims more divisions than there are candidates, **say so explicitly** rather
than forcing the numbers to agree. Set `missing` to the divisions you believe exist in the
prose without a marked-up heading, and name the candidate whose text contains them.

> Peter Pan: the TOC lists 18 chapters; the body has 17 headings. That is not a bad
> match — one chapter's heading was never marked as a heading. Saying "17 chapters" is
> wrong and saying "18" without locating the 18th is useless.

**A `missing` entry is a finding, not a failure.** It is more useful than a wrong count.

---

## What you may not do

**Do not invent a division to make the count match the TOC.** The count following from the
evidence is the answer, even when it disagrees with the publisher.

**Do not merge two real chapters** because the TOC lists one. Two headings with prose under
each are two chapters.

**Do not classify by position.** "The first heading is the title" is true often enough to
be dangerous and wrong often enough to corrupt a book. Judge each heading on its own
evidence.

**Do not use word counts as a rule.** A short chapter is a chapter. `words_after` is
evidence to be weighed against the other signals, not a threshold.

---

## Before you return, check

1. Every candidate has exactly one `role`.
2. `chapter` roles are numbered 1..N contiguously in reading order.
3. Every `part` is followed by at least one `chapter` before the next `part`.
4. No heading with substantial `words_after` is classified `title` or `contents`.
5. Any heading with `words_after == 0` is `title`, a split heading, or explained.
6. If your chapter count differs from the TOC's, `missing` or `reason` says why.
7. `structure` states the shape in one sentence a person could check against the book.
