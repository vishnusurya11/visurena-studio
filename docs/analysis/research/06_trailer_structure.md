# Does a trailer have a screenplay? — six independent research passes, 2026-09-07

Commissioned to settle one design question: should the trailer be written as a
document before anything is rendered, or should its structure keep coming out of
the music cue? Six agents, non-overlapping briefs, told to cite URLs and named
practitioners and to mark anecdote as anecdote.

## The verdict

**A theatrical trailer has no screenplay — and the reason does not apply to us.**

The written artifact that exists at a trailer house is a **copy exploration**:
ten-odd short "scripts" of VO lines and title-card text, no picture column,
produced by a copywriter from a creative brief. Fred Greene (entertainment
copywriter, UCLA TFT) states the constraint that keeps picture off the page:

> "You wouldn't want to write a script calling for scenes and settings that
> aren't in the negative."

Picture in a normal trailer is a **selection problem over fixed inventory**. The
editor's real starting artifact is a breakdown — Chris MacDonald: *"You really
just do type out every single line in the movie… It takes eight to 10 hours."*
Doug Brandt (Ant Farm CEO), asked directly: *"We're not given storyboards. We're
generally not given paper cuts."*

**But every domain where footage must be COMMISSIONED writes the plan first**,
without exception in what six agents found: teasers cut before principal
photography (*"We just break down the script"* — Jeff Gritton, Trailer Park),
game trailers (Derek Lieu: *"All of my timelines start with text descriptors for
each section"*), commercials (the two-column AV script), and **book trailers —
our own vertical — where script + storyboard is the standard, for the reason
that names our problem: it is much cheaper to redirect at storyboard stage than
after the final edit.**

We render every shot to order. We are in the second regime.

## The order of operations professionals use

`spine (written) → music briefed FROM the spine → picture cut LAST`

- Picture last is right, and we already do it. Brandt: *"It all starts with the
  audio bed and the dialog structure and we end up filling in picture last."*
- Structure from the cue is wrong, and nobody does it. When a custom cue is
  commissioned, Lieu's brief is: *"show or tell the composer what you want the
  music to be doing in each part of the trailer, the vibe, emotion, tone,
  energy, pacing… Then send them an outline of the trailer."*
- A trailer cue's three-act shape is a **story template someone already put in**.
  Richard Pryn's composer spec: act 1 30 s, act 2 60 s, act 3 60 s, titles 5 s.
  Reading structure out of a cue reads that generic template back — with this
  book's drama stripped out.
- For TV spots the trade method is explicit: *start with the head of the music,
  end with its climax, custom-edit the middle to connect them.* **They cut the
  music to the structure, not the structure to the music.**
- Cues are built to be cut into. Sound on Sound: *"Gaps between sections are
  thus essential: pauses in the music make it easy for the editor to chop
  between different tracks."* A single monolithic render is the wrong delivery.

## The numbers (measured, with n)

| Figure | Value | n | Source |
|---|---|---|---|
| Trailer runtime | 114.2 s mean | trailers for 20,000+ films | Stephen Follows |
| Trailer runtime | 122.8 s mean | 6,926 trailers / 4,004 films | Stephen Follows |
| **Shots per trailer** | **44 mean** | 277 professional trailers | Papalampidi et al., arXiv 2111.08774 |
| **Mean shot length** | **2.4–3.9 s** (derived) | same | same |
| **Shot-selection overlap between independent human trailers of the same film** | **86.14 %** | same | same |
| Turning point 1 | 11.39 % of runtime (σ 6.72) | 84 screenplays | TRIPOD, Papalampidi et al., EMNLP 2019 |
| Turning point 2 | 31.86 % (σ 11.26) | same | same |
| Turning point 3 | 50.65 % (σ 12.15) | same | same |
| Turning point 4 | 74.15 % (σ 8.40) | same | same |
| Climax | 89.43 % (σ 4.74) | same | same |

Two readings that matter. **86.14 % overlap** means structure converges between
independent professionals — it is not an idiosyncratic property of whichever cue
got chosen. And the **variance is small at the ends and large in the middle**
(σ 6.7 and 4.7 vs σ 11–12): pin the opening and the climax, flex act two.

**Run 19 against these:** 106 s ✅ · 23 shots ❌ (half) · 5.07 s mean shot ❌ ·
act 1 at 1 % against a 15–40 % range ❌.

## The intensity arc is not a ramp

> "trailers should have medium intensity at first in order to captivate
> viewers, followed by **low intensity for delivering key information about the
> story**, and then progressively increasing intensity until reaching a climax
> at the end."

The low stretch is *where the story is told*. `cue_arc.ride` climbs
monotonically low → mid → high, so there is no dip and nowhere to put
information. Same wound as the 0.7 s first act, expressed in the music.

Provenance flag, worth keeping: that quote appears in an EMNLP-lineage paper
whose citation for it is **a practitioner blog post**. The three-act trailer is
consensus craft knowledge, not a measured finding, even where it appears in the
literature.

## Editing rhythm is elastic, and the ceiling belongs to the act

BEAT (arXiv 2605.27067): *"rapid cuts accompany high-energy passages while
sustained shots span quieter bars"* — an atmospheric introduction lets one shot
span three to five bars, **6–10 s at 120 BPM**. A blanket `MAX_SHOT` across the
whole trailer is wrong; act 1 may hold, act 3 cuts on the bar.

## Act proportions to build against

For a 106 s trailer: **≈ 21 s / 40 s / 40 s / 4 s button**, act 1 floored at the
larger of 15 % or 16 s. Sources reconciled: Pryn's 30/60/60/5 composer spec
(19.4/38.7/38.7/3.2 %), trade lore placing act 2 at 1:00 and act 3 at 1:30 of a
2:30 trailer, TRIPOD's measured turning points, and Lieu's *"hook firmly
established 30 seconds in."*

## Prior art: writing the plan first is published, and it wins

| System | Intermediate representation | Written plan? |
|---|---|---|
| IBM "Morgan" (ACM MM 2017) | 10 unordered candidate moments; **a human filmmaker cut it** | No |
| TGT (CVPR 2024) | autoregressive latent shot-embedding sequence | No |
| Papalampidi et al. (TPAMI 2024) | shot graph + 5 turning-point labels + sentiment | No |
| BEAT (2026) | bar/shot embeddings + DP; text only for control and critique | Partial |
| TeaserGen (2024) | **LLM writes the narration, visuals matched to it** | Yes |
| **TRAILDREAMS (2025)** | **LLM writes one line per trailer scene; CLIP retrieval fills each** | **Yes** |
| **REGen (2025)** | **LLM writes a script with placeholders; retrieval fills them** | **Yes** |
| L-Storyboard (2025) | shots → structured language; all reasoning in text | Yes |

REGen reports beating both extractive and abstractive baselines on **coherence,
alignment and realism for teaser generation** — the closest published test of
this exact decision, and it comes out for the written plan.

Two things to steal, both from BEAT: a **VLM critic that watches the rendered
trailer and triggers re-selection, capped at 3 rounds**, and a **Levenshtein
ordering metric**. One warning to obey, from L-Storyboard: free-form LLM
*ordering* is unstable, and the fix is to reduce ordering to **selection among
candidates**. So the drafter picks beats from the analysed pool rather than
inventing them — the same shape as Lieu's paper edit, which reorders transcribed
selects, and REGen's placeholders, which are filled by retrieval.

## The open gap (publishable)

**No published system commits to a beat template, cuts against it, and then
measures the finished cut for conformance.** Papalampidi enforces turning points
at selection time and evaluates the *selector*; everything that produces a cut
evaluates it with a Likert scale or similarity to real trailers. Nobody has
published a measured distribution of act-break and title-card positions over a
trailer corpus either, though the corpora are public (TRIPOD⊕, MovieNet, the
23,304-pair set). A structure-conformance metric suite computed on the output
artifact is novel on its own, and it is the instrument that would have caught
our 0.7-second first act.

## What was NOT verified

- The "MPAA 2:30 rule" is lore. The largest-dataset researcher could not find
  the source document; the traceable rule is Cinema United's **voluntary
  two-minute guideline (2014)**.
- "Trailer studios write a script before the creative process begins" —
  circulates on content farms with no practitioner attribution and contradicts
  every named practitioner found.
- One paper reports a 6.6–7.1 s mean shot length that is arithmetically
  inconsistent with its own shot counts; the derived 2.4–3.9 s is the figure to
  trust.
- Two standard books (Kernan, *Coming Attractions*; Johnston, *Coming Soon*)
  were not fetchable.
