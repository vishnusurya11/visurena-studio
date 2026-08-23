# Research 11 — Narrative map animation (the timeline video)

*Subagent report, 2026-08-23. Implemented in `scripts/analysis/timeline_video.py`.*

## Prior art

- **xkcd 657 movie narrative charts** — the canonical form, but note: its vertical axis
  is *togetherness*, not geography. Steal: colored line per character, **death = line
  ending in a dot**, absence = line disappears and reappears, grey bands for events.
  Spawned an academic subfield (Tanahashi & Ma, IEEE TVCG 2012: minimize line crossings,
  wiggles, whitespace → for us, minimize dot-path crossings and jitter).
- **A Timeline of Ice and Fire** — geography flattened to one axis, **line width = screen
  presence**. The worldline-plot alternative; no disjoint-geography problem because place
  is categorical. Our fallback if a 2D map gets cluttered.
- **serMountainGoat's animated Westeros map** — closest prior art: markers animate by
  date at ~1 s/story-day, prev/next-event buttons, bookmarks. Two lessons: (a) it stuck
  Essos "to the side" — plan disjoint geographies deliberately; (b) it states on screen
  that dates are estimates — mirror that honesty.
- **LotRProject** — full route polylines with date-stamped waypoints (the "trail" idiom).
- **DH literary geography** — Stanford's *Emotions of London*, Turing's *Chronotopic
  Cartographies*: geocoding fictional place references onto real maps is established
  practice. Doyle's London geography is precise enough that Holmes cracks an alibi on it.

## Coordinates

Real London anchors (verified): 221B Baker St 51.5238,-0.1586 · Criterion Bar
51.5101,-0.1340 · St Bartholomew's 51.5175,-0.1000 · Scotland Yard 51.5062,-0.1259 ·
Euston 51.5282,-0.1337. Doyle's invented addresses pinned to their real anchor street
and marked approximate: Lauriston Gardens ≈51.470,-0.114 (Brixton Rd) · Audley Court
≈51.484,-0.109 (Kennington) · Torquay Terrace ≈51.474,-0.092 (Camberwell) · Halliday's
≈51.500,-0.127. Utah: Great Alkali Plain ≈40.8,-113.5 · Salt Lake City 40.7608,-111.8910
· Ferrier farm ≈40.6,-111.6. (All of these went into the entity_resolver skill.)

**Disjoint geographies**: cartography's answer is the inset/panel (Alaska–Hawaii
practice). For this book the narrative decides it: **act-based switch** — swap the main
axes at the Part I/II boundary rather than permanently splitting the frame.

## Stack

- **matplotlib FuncAnimation** is the right tool. manim = overkill; **plotly animations
  cannot be saved to video at all** (frame-by-frame export + manual ffmpeg only).
- **Windows-safe writer chain**: `pip install imageio-ffmpeg` bundles ffmpeg.exe →
  `plt.rcParams['animation.ffmpeg_path'] = imageio_ffmpeg.get_ffmpeg_exe()` →
  FFMpegWriter (mp4); fall back to PillowWriter (GIF). *Adopted verbatim; mp4 worked.*
- Reuse artists (`set_data`), never recreate per frame. Ease with smoothstep
  `3t²−2t³`. Interpolate in *story time*, not frame index.

## Design conventions adopted

1. **Direct moving labels**, not a detached legend (every guide + GoT/LotR projects).
2. **Eased interpolation + fading comet trails** — direction and history at a glance.
3. **Dwell encoding** — stationary must read as information, not as nothing happening.
4. **Honest uncertainty** — faded/hollow at last-known position; *never* a fabricated
   path. A dot gliding somewhere it was never stated to be is a lie the viewer can't
   detect.
5. **Persistent story clock + act indicator** so the viewer always knows *when* they are,
   and that Utah-1847 is a story being told inside London-1881.

Also: ≤8 simultaneous characters (qualitative palette limit); **piecewise time-warp**
because the book's tempo is wildly uneven (4 days vs 33 years) — uniform s/day only
works for calendar-dense stories.

Key sources: xkcd 657 + explainxkcd · Tanahashi & Ma 2012 · StoryFlow · A Timeline of
Ice and Fire · serMountainGoat FAQ · LotRProject · Chronotopic Cartographies ·
Emotions of London · *Deduction and Geography in Conan Doyle's A Study in Scarlet*
(OpenEdition) · matplotlib animations docs · imageio-ffmpeg · maplibrary animated-map
technique guides.
