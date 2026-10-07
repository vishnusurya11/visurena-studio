# line_filler — the micro-line writer

One grounded narration sentence that bridges a residual hole in speech after
trimming to the floors could not close it, or splits an unsplit ONE PER TAKE
pair (speech splits a take without opening silence).

- Tier `local` (the plan's own writer voice) through `studio.llm.structured`;
  `guard_spend` fires before anything is sent.
- Inputs are typed: the shot's own fields, the chapter paragraph, the lines on
  either side. Output is one string.
- Schema rules live in `MicroLine`; the book-aware checks (`lifted_run`,
  `slow_word`) live in `refusals` and re-ask exactly once.
- Book-neutral: names no book, character, episode or take.
