# Retrospect — why TRAILER-A-sherlock was bad

Measured 2026-09-01 against the artefact itself, not from memory.

## What is NOT wrong (I guessed each of these first, and each was wrong)

**The edit.** I first measured the source clips — all exactly 10.1 s — and concluded the
trailer was nine clips concatenated. That was wrong: I had measured the raw material, not
the cut. Scene detection on the finished file finds **29 cuts, mean 2.71 s, 10 shots
under 2 s.** That is a real edit, on the slow side but inside the range.

**The images.** They are good. Cinematic grade, period-correct, properly composed: a
guttering candle, RACHE scratched on plaster, London rooftops at dusk, a hansom in fog,
the Alkali plain caravan, a ring in an open palm.

**The references.** `SH-char-holmes.png` is a textbook character sheet — gaunt, dark
frock coat, neutral grey backdrop, level gaze, hands out of frame. Watson, Lestrade,
Gregson, Hope, Stamford all exist. Seven location plates exist. `style.json` holds one
style key for the whole production.

## What IS wrong

### 1. The references were built and then not carried into the shots

The Holmes reference is a lean man in a black Victorian frock coat. In the trailer, the
man in the laboratory wears **a tan shirt with rolled sleeves**.

**The trailer has no protagonist.** Twenty-nine shots and no face the eye can follow. A
viewer cannot say who the film is about, and that is the difference between footage and
a trailer.

It is not enough for refs to exist — every shot must be CONDITIONED on them, and the
result must be CHECKED against them.

### 2. Mixed aspect ratios inside one cut

At least one shot is letterboxed while the rest are full-frame. Nothing reads as amateur
faster, and it is free to fix.

## The lesson

The pipeline was not short of craft. It had a style key, character sheets, location
plates, a beat scorer that ranks by reversal and withheld information, a spoiler cut, and
an assembler with a real three-act structure.

**It was short of one binding step: making the generated shot obey the reference, and
failing the shot when it does not.**
