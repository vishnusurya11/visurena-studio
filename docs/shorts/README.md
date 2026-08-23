# shorts

**Status: 8 department skills implemented and owner-approved (2026-08-09), living in
`.claude/skills/shorts-*` and `.claude/agents/shorts-*`.** The design docs that
accompanied them are not currently in the working tree.

50–60s cinematic fan-made book-scene shorts for The Keeper's Lantern, produced on
Higgsfield.

## Budget

Ultra plan, 9,000 credits/month. **500 credits per short → 16/month.**

## Core principle

Iterate look, casting and composition in **images** (0.12–2 cr), then spend video credits
**once** per approved shot. Consistency comes from a donor-reference style key plus a
byte-identical 80–100 word style formula in every prompt.

## Pipeline

S0 story → S1/S2 style + look test → S3 shot list → S4 start frames → S5 clips
(the only expensive stage) → S6a audio → S6b assembly → S7 publish.

Productions are self-contained folders under `media/shorts/yyyymmddhhmmss_<name>/`.

## Where this is headed

Per [../ARCHITECTURE.md](../ARCHITECTURE.md), **the procedure moves to Python and the
skills become thin interactive drivers over it** (P2). A markdown skill cannot be
automated, only re-implemented — and two implementations drift. The seam between the
interactive and headless runtimes is the JSON contract on disk.

Gates stay `ESCALATE` by default: no credits are spent without an itemized plan and an
explicit go.
