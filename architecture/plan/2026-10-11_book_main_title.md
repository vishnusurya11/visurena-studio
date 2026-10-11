# 2026-10-11 — Book main title, thumbnail, title-first chapters

**Status:** BUILT 2026-10-11. Decision: [../decisions/2026-10-11_book_main_title_and_thumbnail.md](../decisions/2026-10-11_book_main_title_and_thumbnail.md).

- [x] Title first per chapter: each shipped Short cut by frame into title + main (`studio/book_compilation`)
- [x] The card MEASURED in the Short (last cut before the closing black): Scarlet ep01's older 90-frame card
- [x] Every piece conformed to the book's square: Scarlet is 768x1344 / 768 / 1536
- [x] Footer and intro from `source/book.json`: the code named Wells
- [x] The main title: `studio/book_title.py` (pure) + `scripts/episode/book_title.py` (render, judge, thumbnail)
- [x] The book video: main title first, stamps shifted by `lead_s`, thumbnail set, replaced video made private
- [x] WotW and Scarlet book videos uploaded: https://youtu.be/HSn8Gl7mnyA, https://youtu.be/IDtuFR_VAqo (old WotW 7grcwgBJ9S0 private)
- [x] First-render faults fixed: drama-scored cold open, sting laid on the black, level pass, bt709 tags, biggest-change card finder, list-based doubled-person check, banner-thumbnail fallback, square-only cold open

## Log
- 2026-10-11: owner saw the WotW book video with every card at the chapter's END; asked title first, a book main title unlike the cards, and a poster (thumbnail). Three designers + a judge; C (reliability first) won with B's cold open.
- [x] Retro (owner 2026-10-11): recorded card layout by sha8, the upload door + contact sheet, the book's look on every picture (main title, thumbnail, chapter-card art), a list-judged doubled-person check, a per-book lock, live logs, a writer fallback, read-back failure = flag, a compile check, GPU decode + packet counts, the GPU half in parallel. WotW/Scarlet not re-made (live: HSn8Gl7mnyA, HOLHQEN0Gic).
