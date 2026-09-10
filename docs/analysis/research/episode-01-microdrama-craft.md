# Episode craft: what makes a 90-120 s vertical narrative episode hold, and how to compress one chapter into it

Research date: 2026-09-09. Target: Visurena Studio chapter episodes (one book chapter -> one 90-120 s 9:16 video, VO dialogue over cutaways, no lip-sync, designed TTS voices).
Grounding material: `library/20260822113400_a-study-in-scarlet/screenplay/feature/screenplay.json` (canonical; scene 1 = ch.1 scenes 2-4, 24 elements, 90.0 s, 12 shots; scene 2 = ch.1 scenes 5-6 + ch.2 scene 1, 21 elements, 97.5 s). Note: `screenplay/feature/scenes/sc_0001.json` is a divergent draft (Criterion bar, untouched glass, 27 elements). Element indices below are `screenplay.json` indices.

Evidence grades used throughout: **A** = platform-official, peer-reviewed, or large-N survey; **B** = practitioner source stating a corpus or professional standing; **C** = vendor/SEO blog, no methodology. Retention percentages in this domain are almost all grade C; they agree with each other, which is weak corroboration, not proof.

---

## 1. Rules a skill can enforce

Each rule: the check (machine-checkable where possible), the evidence, one line of why.

### Length and shape

1. **Episode runs 90 s by default; 120 s is the hard ceiling; go longer only if every added second carries a beat.**
   Check: `duration_s in [80, 120]`; default plan target 90.
   Evidence: ReelShort/DramaBox episodes 60-120 s, "many sitting around 90" (Filmustage, B; Vertical Writers, B); Deloitte TMT 2026: micro-series "60- to 90-second episodes" (A, industry); YouTube Shorts: completion falls with length, APV is what ranks (Metricool/TrueFuture, C); Opus Clip 500-video sample: 62% completion at 21-34 s vs 48% at >60 s (C).
   Why: the ranking signal is percentage viewed, so every unearned second lowers the number that decides distribution.
   Sources: https://filmustage.com/blog/how-to-write-a-vertical-drama-script/ , https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/short-form-video-series.html , https://www.opus.pro/blog/tiktok-length-format-retention-data

2. **One event per episode: one turn (a character's choice) and one cliffhanger (the world's answer), and they are different beats.**
   Check: plan has exactly one `turn` beat and one `button` beat with different element indices.
   Evidence: ScreenWeaver: "The turn is a change the character makes; the cliffhanger is a change the world makes to them ... If the same beat does both jobs the episode has one event and a black screen" (B). Character.app: "exactly one meaningful beat ... One clean turn per chapter, not a full act" (C).
   Why: 90 s cannot pay off two arcs; a second event either starves the first or gets no setup.
   Sources: https://www.screenweaver.ai/blog/short-drama-episode-structure , https://www.character.app/blog/what-is-a-vertical-drama

3. **Turn lands at ~60% of runtime (0:54 in 90 s); cliffhanger in the last 5 s; cut to black within 1 s of the last line landing.**
   Check: `turn_t / duration in [0.55, 0.65]`; `button_start >= duration - 6`; `black_at - last_line_end <= 1.0`.
   Evidence: ScreenWeaver 60% / last five seconds (B); Filmustage: freeze-frame "between seconds 55-58" of a 60 s episode, "cut to black the instant it lands without resolving it" (B); Real Reel skeleton 0:00 ignition / 0:32 jolt / 1:18 spike / 1:50 button for a 2-min episode (B, via search snippet; page 403).
   Why: the button is the product; resolving it, or trailing after it, refunds the reason to tap next.
   Sources: https://www.screenweaver.ai/blog/short-drama-episode-structure , https://filmustage.com/blog/how-to-write-a-vertical-drama-script/ , https://medium.com/real-reel/hooked-by-ten-the-writers-playbook-for-high-retention-vertical-dramas-7835e12f063d

4. **Write the last 3-5 s first, then build backwards.**
   Check: plan file records `button` before `hook` (ordering field) or the skill refuses to time the middle until `button` is set.
   Evidence: Filmustage: "Decide the final three seconds of the episode first ... then write the preceding 80 seconds to set it up" (B).
   Why: every surviving line must be justified as setup for the button; without the button fixed there is no selection criterion.

5. **Cliffhanger type is one of four and rotates across episodes: Revelation, Reversal, Deadline, Intrusion. The last line is not spoken by the protagonist.**
   Check: `button.type in {revelation, reversal, deadline, intrusion}`; `button.type != prev_episode.button.type`; `button.speaker != protagonist`.
   Evidence: InkTip (producer-facing) and ScreenWeaver list the same four types (B, possibly common origin); ScreenWeaver: final line "posed as question, reveal, or clock - never delivered by the protagonist" (B); lmtw.com 卡点 rule: "emotion unresolved, plot at a turning point, character in a critical state" (B).
   Why: a cliffhanger is something done TO the lead; a lead who speaks last has already reacted, which is the next episode's job.
   Sources: https://www.inktip.com/articles/writing-for-vertical-video-scripts , https://lmtw.com/mzw/content/detail/id/241607/keyword_id/-1

6. **Pair rule: episode N's last 5 s and episode N+1's first 5 s are one beat split by the title card. The reaction goes in N+1.**
   Check: `ep[N].button.element` and `ep[N+1].hook.element` are adjacent in the screenplay or the N+1 hook is the reaction to N's button.
   Evidence: ScreenWeaver: "Episode 12 ends on the door opening; episode 13 opens on who is in it ... Write them as a pair, board them as a pair, and cut them as a pair" (B). Buka: "each episode answers one question while introducing another" (C).
   Why: this is the only continuity device that costs zero seconds.

### Hook and opening

7. **Conflict in the first image; premise legible with sound off; no setup longer than 10 s.**
   Check: shot 0 contains a conflict/threat/question element (not an establishing wide); `setup_end <= 10 s` (ideally 5-8 s); on-mute test: caption + picture alone state who/what/why.
   Evidence: 163.com corpus ("100+ hit episodes"): 0-3 s hook, 0-10 s must establish core conflict, relationships, goal, "no setup exceeding 10 seconds" (B); Hongguo official writer guide: "first 3 seconds" hook, "avoid prolonged exposition" (B, platform); Douyin paper (Li, CUC): micro-short plays "shift conflicts and tensions to the beginning" - example lands full conflict inside 30 s (A, academic); Stage 32: "try the mute test" (B); Shortimize: "Treat the first 1 second as your thumbnail ... topic legible on mute with 3-6 words" (C).
   Why: 30-50% of a Shorts audience leaves in 0-3 s (C, multiple vendors agree); nothing after the hook is seen by them.
   Sources: https://www.163.com/dy/article/L30RCS1005340TH8.html , https://news.qq.com/rain/a/20251031A04KVO00 , https://pdfs.semanticscholar.org/9cc6/206949c7e2e704bd55c74ba7478ff559ce50.pdf , https://www.stage32.com/blog/the-vertical-microdrama-screenwriting-challenge-part-1-4499 , https://www.shortimize.com/blog/youtube-shorts-retention-rate

8. **First payoff (a reversal, a reveal, or a "he did WHAT") lands by 0:30-0:35.**
   Check: first beat tagged `payoff|reversal` has `t <= 35 s`.
   Evidence: 163.com: "first reversal/payoff must occur within 30 seconds" (B); Hongguo tutorial 05: "the first 30 seconds decide life or death is the industry's accepted law" (B, platform).
   Why: the hook buys 10 s of patience; the first payoff buys the middle.
   Sources: https://www.163.com/dy/article/L30RCS1005340TH8.html , https://www.juben.pro/a/1-1783.html

9. **Enter late: the episode starts at the latest element from which the button is still set up.**
   Check: no element before `hook.element` is required by any later beat (dependency scan); if an earlier element is required, it must be carried by picture (a plant), not by dialogue.
   Evidence: "Enter late, leave early" (Syd Field, via No Film School; B); web-novel-to-duanju guides: cut exposition, backstory, omniscient narration first (Hongguo tutorial 10, B).
   Why: everything before the first conflict is the 3-s swipe window spent on nothing.
   Sources: https://nofilmschool.com/start-late-leave-early , https://www.juben.pro/a/2-1790.html

### Middle

10. **An emotional node every 20-30 s (a conflict line, an action, or a disclosed fact); no flat stretch longer than 30 s.**
    Check: sorted `node_t` list has all gaps `<= 30 s`.
    Evidence: 163.com corpus: "every 20-30 seconds set an emotional node" (B); vendor retention blogs place the mid-drop at 40-60% of runtime and prescribe a mid re-hook (C).
    Why: the retention curve's second cliff is the middle; nodes are what the curve is measuring.

11. **Middle is "substantive": each line and each action advances plot, reveals character under pressure, or sets up the button. Zero "water".**
    Check: every dialogue element carries at least one tag in `{plot, character, setup_button}`; untagged lines are rejected.
    Evidence: Hongguo official guide: each line "must advance plot, reveal character, or create suspense"; "water dialogue" banned (B, platform); Filmustage: "dialogue that doesn't move the scene forward is a scene you don't have" (B).
    Why: at 90 s a wasted line is 3-5% of the episode.

12. **Two to three speaking characters, one or two locations per episode.**
    Check: `len(speaking) <= 3`; `len(locations) <= 2` (warn at 3).
    Evidence: ScreenWeaver: one location default, 2-3 characters (B); InkTip: "one or two characters per scene works best" (B); Douyin paper: 2-3 core characters, environment "weakened" in favour of close-ups (A).
    Why: 9:16 has no room for geography; every new face or place is setup the viewer pays for.

### Dialogue and voice-over (VO over cutaways)

13. **Speech length: max two caption lines per speech (~12-14 words); the second line is the one that lands. Split or cut anything longer.**
    Check: `words_per_speech <= 14` (hard 18); verbatim lines over the cap are trimmed to their landing clause and re-tagged `adapted`.
    Evidence: ScreenWeaver script format: "Two lines per speech, and the second line is the one that lands. Remove first lines that only serve as setup" (B); Hongguo: five-six consecutive lines of dialogue "severely damages pacing", ornamental phrasing is "the rhythm killer" (B); 163.com: "dialogue short, fragmented, sharp" (B).
    Why: a long speech is a static frame; in VO-over-cutaways it also outruns the shot it sits on.
    Sources: https://www.screenweaver.ai/blog/short-drama-script-format

14. **VO occupies at most ~55-60% of runtime; leave at least one silent gap of >= 2 s before the button.**
    Check: `sum(line_durations) / duration <= 0.60`; a gap `>= 2 s` with no VO exists in `[button_start - 8, button_start]`.
    Evidence: pace arithmetic: 130-160 wpm typical narration, 145 wpm explainer, 160-170 wpm fast Shorts (script-length calculators, C); the screenplay's own scene 1 on the chosen line set = 122 words = 49 s at 150 wpm = 54% of 90 s. Chinese chapter->episode conversion: ~600 Chinese characters of script per 1-2 min episode (woshipm, B).
    Why: the cutaways must carry the beats the VO does not; a wall of VO is a podcast with a screensaver.
    Sources: https://sumera.io/blog/how-long-should-youtube-script-be , https://www.woshipm.com/share/6112301.html

15. **Unseen action must be reacted to aloud or shown; a payoff's plant must be visible on mute earlier in the episode.**
    Check: every `payoff` beat references a `plant` beat with `t < payoff.t` whose shot contains the plant object (e.g. stick/limp before "Afghanistan").
    Evidence: radio-drama convention: "If a character draws a weapon, someone in the scene must react verbally, because the audience cannot see it happen" (Theatrecrafts, B); duanju twist rule: "fast, ruthless, logical, with clever foreshadowing so audiences experience an aha moment" (lmtw, B).
    Why: with no lip-sync the ear leads and the eye confirms; a deduction with no visible evidence reads as a cheat.
    Sources: https://theatrecrafts.com/pages/home/topics/sound/radio-drama/ , https://lmtw.com/mzw/content/detail/id/241607/keyword_id/-1

16. **Compose close and centred: faces, hands, objects. Reaction shots carry the VO; wide shots only as a <= 2 s transition.**
    Check: `wide` shots `<= 2 s` each and `<= 2` per episode; every dialogue line is covered by a shot containing a face or the object being spoken about.
    Evidence: Filmustage: frame "filled with a face the vast majority of the time" (B); Character.app: "reaction shots carry a disproportionate share of the storytelling" (C); Douyin paper: environment abandoned for close-ups so the audience is "forced to focus their attention on the main characters" (A); InkTip: "faces, hands, and intimacy over wide shots" (B).
    Why: on a phone a wide shot is a postage stamp; a face is the only thing that reads at thumb distance. Note: the current screenplay scene 1 shot list is 10/12 locked-off with several wides/two-shots; the episode cut needs re-coverage, not the feature coverage.

### Captions

17. **Burned-in captions on every line, phrase-segmented (not full sentences), 1-2 lines, bold sans-serif, high contrast, inside the common safe zone.**
    Check: caption cues exist for 100% of dialogue; `chars_per_line <= 32`; `lines <= 2`; caption box within x 90-990, y 260-1600 on 1080x1920 (common safe zone), never in bottom 320 px.
    Evidence: Verizon Media/Publicis survey (N=5,616 US adults, 2019): 69% watch with sound off in public, 25% in private; 80% more likely to finish a video with captions (A); Kruger et al. 2013 (ACM): short segments improve reading speed and comprehension vs sentence-length subtitles (A, via ContentFries; paywalled); safe-zone numbers: TikTok bottom ~250-320 px, Reels ~310-320 px, Shorts ~300 px; common zone 900x1400 centred (Kreatli 2026-01, AdaptlyPost; C but consistent).
    Why: most viewers read the episode; a caption under the UI is a line that was never delivered.
    Sources: https://www.3playmedia.com/blog/verizon-media-and-publicis-media-find-viewers-want-captions/ , https://www.contentfries.com/blog/the-science-of-video-captions-how-they-impact-audience-retention , https://kreatli.com/guides/safe-zone-guide , https://adaptlypost.com/en/blog/social-media-safe-zones-2026-complete-guide

18. **Speaker identification on VO: label the speaker on their first line in the episode and on any line where the speaker is not the face on screen.**
    Check: for each dialogue cue, `speaker_on_screen or cue.has_label`; first cue of each speaker has a label.
    Evidence: DCMP Captioning Key: identify the speaker when not visible or when more than one person is on screen; name on its own line in parentheses; do not identify by name before the audio/graphic introduces the name (A, standard).
    Why: VO-over-cutaways breaks the default "the moving mouth is the speaker" inference; the label restores it. Practical form: a small-caps name chip above the caption (`STAMFORD`), not colour-only (colour-per-speaker is not a standard and fails for colour-blind viewers).
    Source: https://dcmp.org/learn/603-captioning-key---speaker-identification

### Continuity, recap, ending

19. **No "previously on" inside the episode. Continuity = episode chip + recurring visual cue + the pair rule. Each episode must stand alone for a discovery viewer.**
    Check: no element tagged `recap`; a top-safe `EP n` chip is present from 0:00 for <= 3 s; the hook line does not depend on the previous episode.
    Evidence: Influencers-Time episodic brief: two viewer journeys (followers vs discovery), solved "through contextual hooks and recurring visual cues, not recap narration" (B); Chinese regulator caps TV recaps at 30 s and duanju practice drops them entirely: "almost no setup, flashback or white space" (thepaper.cn, B); Buka: "one continuous story told in many short chapters ... each episode leading directly into the next" (C).
    Why: a recap is the swipe window spent on the last episode.
    Sources: https://www.influencers-time.com/episodic-creator-briefs-for-tiktok-and-meta-series-hubs/ , https://m.thepaper.cn/newsDetail_forward_26618824

20. **Ending is a cliffhanger, not a loop. End chip ("Ep 2 ->" / series title) <= 2 s, after the cut to black, never before the last line.**
    Check: `end_card_duration <= 2 s`; `end_card_start >= black_at`.
    Evidence: series content: the ending should "summarize the current payoff, create the next question, and make the next video easy to recognize" (CapCut guide, C); seamless-loop endings are a different strategy for standalone Shorts (C).
    Why: a loop rewards rewatching this episode; a series needs the tap on the next one.
    Sources: https://www.capcut.com/create/cliffhanger-endings-short-form-video-series

21. **Series identity is carried by constants, not by text: same two voices, same recurring object (the stick, the test-tube), same title chip position.**
    Check: `voice_ids` identical to series manifest; at least one `series_cue` object appears in the first 10 s.
    Evidence: AI-series tooling and creator guides converge on voice/character consistency as the retention lever (Narration Box, Videee; C); Hongguo: "don't lose characters mid-narrative" (B).
    Why: for a feed viewer the chip is the only proof this is the show they watched yesterday.

### Retention targets the skill can report (grade C unless stated; use as smoke alarms, not goals)

22. **Report: 3-s hold, mid-point hold, APV, swipe-away.** Targets quoted by multiple vendors: >= 80% at 3 s (65-70% minimum viable), >= 60% at midpoint, APV >= 70%, swipe-away 10-30% (>40% = hook failure). Official metric names: YouTube Studio "Viewed vs. swiped away" and "Shown in feed" (A, definition only); TikTok Creator Academy retention graph "shows the exact moment ... viewers lost interest" (A, definition only). No platform publishes benchmark numbers.
    Sources: https://humbleandbrag.com/blog/youtube-shorts-benchmarks , https://buffer.com/resources/the-creators-guide-to-youtube-shorts-analytics/ , https://www.tiktok.com/creator-academy/en/article/analytics-tool-video-performance

---

## 2. Compression procedure: chapter screenplay -> 90-120 s episode

Input: the chapter's screenplay scene(s) (elements with `kind`, `character`, `provenance`, `source`), the chapter's next-scene first elements (for the pair rule), the series manifest (voices, cues, previous button type).
Output: an ordered beat list with `t_start`, `t_end`, element indices, shot, VO text, caption cue, and tags.

**Step 0 - Pick the episode's one event.** Read the chapter's scenes; find the single moment where the world does something to the lead that cannot be undone (Revelation/Reversal/Deadline/Intrusion). If a chapter has two such moments >= 2 scenes apart, it is two episodes (Study in Scarlet ch.1 already is: the screenplay splits it at the haemoglobin line).

**Step 1 - Fix the button (last 5 s).** Choose the line/image. Constraints: not spoken by the protagonist; leaves the question open; type != previous episode's type. Record the reaction line that follows it in the book: that is the next episode's hook (rule 6).

**Step 2 - Fix the hook (first 5 s).** Find the latest element that (a) contains conflict or a question, (b) reads on mute with one caption, (c) still leaves the button set up. Everything before it is cut or demoted to a picture plant.

**Step 3 - Score every dialogue element** with tags: `plot` (needed for the button to make sense), `char` (reveals character under pressure), `iconic` (verbatim line the audience expects), `setup_button` (plants the payoff). Untagged -> cut. Tagged only `iconic` -> keep only its landing clause, re-tag `adapted`.

**Step 4 - Budget.** `vo_budget_words = duration_s * 150/60 * 0.55` (90 s -> ~124 words; 120 s -> ~165). Sum surviving words; if over, cut in this order: lines tagged only `char`; first halves of two-part speeches; adapted lines duplicating a picture. If under by > 20%, restore in reverse.

**Step 5 - Place beats on the shape (section 3).** Turn at 60%; first payoff <= 35 s; emotional nodes every 20-30 s; silent gap >= 2 s before the button. Convert action elements into cutaway shots that carry the beats between lines.

**Step 6 - Validate** against rules 1-21 (all checks are computable from the beat list) and emit the report of rule 22 fields for post-publish comparison.

### Worked pass: A Study in Scarlet, chapter 1 -> Episode 1 (90 s)

Chapter 1 in the screenplay = scene 1 (elements 0-23) + scene 2 elements 0-17 (proposal, street, hotel); ch.2 begins at scene 2 element 18. The screenplay's scene 1 is already the first event; scene 2 is the second.

Step 0 - Event: Holmes reads Watson's war service off his body ("You have been in Afghanistan, I perceive", el.19) and refuses to explain (el.23). Type: **Revelation** (with an Intrusion flavour - the blood).
Step 1 - Button: el.22-23: Holmes turns back to the tube, pricks his finger, "Never mind. The question now is about haemoglobin." Not the protagonist; leaves "how did he know?" open exactly as the book does until ch.2. Next episode's hook = scene 2 el.12, "By the way, how the deuce did he know that I had come from Afghanistan?" - the pair rule maps onto Doyle's own structure without invention.
Step 2 - Hook: el.8, Stamford: "You mustn't blame me if you don't get on with him." A warning about an unseen man = a question, reads on mute, and the stick/limp plant (el.1, el.4) is carried as picture in the same shot. Elements 0-3 (hansom, "Whatever have you been doing", the 22-word lodgings speech) are cut: pure exposition, 12 s, nothing later depends on them except "Watson needs rooms", which el.5-6 supply in 8 s.
Step 3-4 - Line scoring and budget (150 wpm):

| el | speaker / line | words | s | tag | keep |
|---|---|---|---|---|---|
| 2 | Stamford "Whatever have you been doing..." | 8 | 3.2 | - | cut |
| 3 | Watson "Looking for lodgings..." | 22 | 8.8 | plot(weak) | cut; want carried by el.6 |
| 5 | Stamford "A fellow at the chemical laboratory has rooms. He wants someone to go halves with him." | 16 | 6.4 | plot | keep |
| 6 | Watson "...I am the very man for him." | 19 | 7.6 | plot, char | keep tail only: "I am the very man for him." (7 w, 2.8 s) -> adapted |
| 8 | Stamford "You mustn't blame me if you don't get on with him." | 11 | 4.4 | plot, setup_button | keep = HOOK |
| 9 | Watson "It seems to me, Stamford, that you have some reason for washing your hands of the matter." | 17 | 6.8 | char | keep (node 1) |
| 10 | Stamford "Holmes is a little too scientific for my tastes - it approaches to cold-bloodedness." | 12 | 4.8 | char, iconic | keep |
| 12 | Watson "Beating the subjects!" | 3 | 1.2 | plot, iconic | keep = first payoff |
| 13 | Stamford "Yes, to verify how far bruises may be produced after death. I saw him at it with my own eyes." | 20 | 8.0 | plot, iconic | keep; over the 14-word cap - split into two caption cues at the full stop |
| 16 | Holmes "I've found it! I've found it." | 6 | 2.4 | char, iconic | keep |
| 18 | Stamford "Dr. Watson, Mr. Sherlock Holmes." | 5 | 2.0 | plot | keep = TURN (Stamford commits) |
| 19 | Holmes "How are you? You have been in Afghanistan, I perceive." | 10 | 4.0 | plot, iconic | keep = SPIKE |
| 21 | Watson "How on earth did you know that?" | 7 | 2.8 | plot | keep (protagonist reacts; not the last line) |
| 23 | Holmes "Never mind. The question now is about haemoglobin." | 8 | 3.2 | plot, iconic | keep = BUTTON |

Surviving VO: 122 words = 48.8 s = 54% of 90 s (budget 124). Cut: 30 words / 12 s of pure setup.

Step 5 - Timeline (90 s):

| t | section | picture (cutaway) | VO / caption | rule |
|---|---|---|---|---|
| 0:00-0:05 | HOOK | Close: a narrow side-door; Stamford glances back; Watson's hand white on the stick, a limp. `EP 1` chip top-safe. | STAMFORD: "You mustn't blame me if you don't get on with him." | 7, 9, 15 (plant: stick) |
| 0:05-0:14 | SETUP | Corridor two-shot, close; Watson's drawn face. | STAMFORD: "A fellow at the chemical laboratory has rooms. He wants someone to go halves with him." WATSON: "I am the very man for him." | 7 (setup 9 s) |
| 0:14-0:27 | FRICTION 1 | Walking; Stamford does not meet his eye. | WATSON: "It seems to me, Stamford, that you have some reason for washing your hands of the matter." STAMFORD: "Holmes is a little too scientific for my tastes - it approaches to cold-bloodedness." | 10 (node 1 at ~0:25) |
| 0:27-0:38 | FIRST PAYOFF | Insert: a stick beside a covered body on a slab; Watson stops. | WATSON: "Beating the subjects!" STAMFORD: "Yes, to verify how far bruises may be produced after death." / "I saw him at it with my own eyes." | 8 (payoff at 0:28), 13 (split) |
| 0:38-0:48 | TRANSITION (silent) | Dolly in through the open lab door; glassware; a figure bent over a tube. Music only. | - | 14 (silence), 16 |
| 0:48-0:52 | - | Holmes springs up, tube raised, plaster on one finger (plant). | HOLMES: "I've found it! I've found it." | 15 (plant: finger) |
| 0:52-0:55 | TURN (60% = 0:54) | Three-shot, Stamford's hand between them. | STAMFORD: "Dr. Watson, Mr. Sherlock Holmes." | 3 |
| 0:55-1:00 | SPIKE | Holmes's eyes travel: coat, hand, stick (the plant paid). | HOLMES: "How are you? You have been in Afghanistan, I perceive." | 15 |
| 1:00-1:06 | REACTION | Dolly in on Watson; grip tightens. | WATSON: "How on earth did you know that?" | 5 (not the last line) |
| 1:06-1:12 | RUN-OUT | Holmes turns away; pricks the plastered finger; a drop hangs. | - (2+ s silence) | 14 |
| 1:12-1:16 | BUTTON | Close on the tube; the drop falls. | HOLMES: "Never mind. The question now is about haemoglobin." | 3, 5 (Holmes speaks last) |
| 1:16-1:23 | - | The liquid darkens to mahogany; brown dust settles; Watson's face, unanswered. | - | 2 (world's answer is the blood) |
| 1:23-1:24 | cut to black | | | 3 |
| 1:24-1:26 | END CHIP | "A STUDY IN SCARLET - EP 2" | | 20 |

Runtime 86 s (trim slack sits in the transition and run-out; stretch to 90 with the darkening beat, never with VO).

Discarded from ch.1 that the feature screenplay also omits: ch.1 scene 1 (Watson's biography, Maiwand, enteric fever, 11s.6d. a day) - carried entirely by the stick, the limp, the loose coat, and Stamford's glance (rule 15). Deferred to Episode 2: scene 2 el.0-17 (the confession exchange, the handshake, the street question, "knotty problem"). Episode 2 hook = el.12 (street, "how the deuce did he know"), turn = the handshake (el.8) at ~60%, button candidate = Stamford: "You'll find him a knotty problem, though." (el.16, Reversal-type warning, not the protagonist) or ch.2's boxes crossing the 221B threshold as an Intrusion; the ch.2 material (el.18-20) belongs to Episode 3.

120 s variant, if wanted: restore el.0-3 hansom opening (+12 s) only if the hook becomes the hansom interior with Stamford's warning moved to el.8's original place - this weakens rule 7 (setup 20 s) - or add the haemoglobin demonstration from the divergent `sc_0002.json` (Holmes "It gives us an infallible test for blood stains", +10 s) after the button - which violates rule 3. Neither is recommended; the evidence favours the 86-90 s cut.

---

## 3. Episode shape (time budget)

Fixed-second sections do not scale with runtime; proportional ones do.

| section | 90 s | 120 s | rule | what must be true |
|---|---|---|---|---|
| HOOK | 0:00-0:05 (fixed) | 0:00-0:05 | 7 | conflict in first image; one caption line; on-mute legible; series chip |
| SETUP | 0:05-0:15 (<= 10 s fixed) | 0:05-0:15 | 7, 9 | who, want, obstacle; nothing before the first conflict |
| FRICTION | 0:15-0:50 (39%) | 0:15-1:05 | 8, 10, 11 | first payoff by 0:35; node every 20-30 s; one silent transition |
| TURN | ~0:54 (60%) | ~1:12 | 2, 3 | a character's choice, one line |
| SPIKE | 0:55-1:10 (61-78%) | 1:13-1:35 | 15 | the biggest jolt; the plant is visibly paid |
| RUN-OUT | 1:10-1:20 | 1:35-1:52 | 14 | VO thins; >= 2 s silence; picture carries consequence |
| BUTTON | last 5 s (fixed) | last 5 s | 3, 5 | not the protagonist; unanswered; black within 1 s |
| END CHIP | <= 2 s after black | <= 2 s | 20 | next-episode pointer only |

VO share <= 60%; words <= duration * 1.375 (150 wpm x 0.55). Cliffhanger type rotates per episode. Two to three voices; one to two places.

---

## 4. What could not be verified

- **Reddit.** r/Filmmakers, r/Screenwriting, r/aivideo, r/StableDiffusion threads were not reachable: search engines returned no reddit results for the queries, and direct fetch of reddit.com is blocked in this environment. The community-practice half of the brief (what AI microdrama channels actually do with VO and cutaways) therefore rests on tooling pages and press (Vigloo's Bloodbound Luna uses "reference-based AI generation" and synthetic voices; whether it lip-syncs is not stated). Run `/browse` on reddit if this matters.
- **Retention numbers.** Every percentage in rule 22 and in the "30-50% leave in 0-3 s" claim comes from vendor blogs (Shortimize, Humble&Brag, Retensis, Opus Clip's "500 videos", Metricool's 82k accounts for view averages only). No platform publishes benchmark retention; YouTube and TikTok only define the metrics. Treat targets as smoke alarms.
- **The four cliffhanger types and the 60% turn** appear in ScreenWeaver and InkTip with near-identical wording; they may share an author. No hit-episode corpus with timestamps was found in English; the Chinese 163.com corpus claim ("100+ hits") is unverifiable.
- **Caption style.** Kruger et al. 2013 (ACM, short segments beat sentence subtitles) was only reachable via a secondary cite (ACM page 403). The "word-by-word captions +25-40% in first 5 s" figure is unsourced vendor copy and is not used in any rule.
- **Douyin academic paper** (Li, CUC) describes 2-5 min episodes from 2021-22; its structural claims (conflict moved to the opening, 2-3 characters, environment weakened) transfer, its timings do not.
- **Chapter-to-episode ratio.** Chinese guides state ~2,000-character web-novel chapter -> ~600-character script -> 1-2 min episode (roughly 1 chapter = 1 episode). Doyle's chapter 1 is ~4,000 English words; the 1:2 split the screenplay already makes is consistent with that ratio but not derived from it.
- **Not found:** any evidence distinguishing 90 s from 120 s retention for narrative (vs. talking-head) content; any documented craft rule set for VO-over-cutaways drama on TikTok/Shorts; ReelShort's internal writer guidelines (only John August's second-hand account of working conditions - https://johnaugust.com/2025/writing-for-microdramas-aka-verticals - which confirms heavy data-driven rewriting of the first ~10 episodes and nothing about episode-internal timing).
- **Fetch failures:** Real Reel (medium, 403), Zhihu per-second breakdown (403), CSDN (521), Zenodo micro-drama preprint (504), verticalserieslaunch.com (404), microdrama.com (refused). Their claims are cited only where a search snippet carried the specific number.

## Source index (all URLs used)

- https://www.screenweaver.ai/blog/short-drama-episode-structure
- https://www.screenweaver.ai/blog/short-drama-script-format
- https://filmustage.com/blog/how-to-write-a-vertical-drama-script/
- https://www.inktip.com/articles/writing-for-vertical-video-scripts
- https://www.stage32.com/blog/the-vertical-microdrama-screenwriting-challenge-part-1-4499
- https://medium.com/real-reel/hooked-by-ten-the-writers-playbook-for-high-retention-vertical-dramas-7835e12f063d
- https://johnaugust.com/2025/writing-for-microdramas-aka-verticals
- https://www.finaldraft.com/blog/how-to-use-the-final-draft-micro-drama-and-verticals-templates
- https://www.character.app/blog/what-is-a-vertical-drama
- https://watchbuka.com/insights/micro-drama-complete-guide
- https://www.influencers-time.com/episodic-creator-briefs-for-tiktok-and-meta-series-hubs/
- https://www.163.com/dy/article/L30RCS1005340TH8.html
- https://www.juben.pro/a/1-1783.html
- https://www.juben.pro/a/2-1790.html
- https://news.qq.com/rain/a/20251031A04KVO00
- https://www.thepaper.cn/newsDetail_forward_31865950
- https://m.thepaper.cn/newsDetail_forward_26618824
- https://lmtw.com/mzw/content/detail/id/241607/keyword_id/-1
- https://lmtw.com/mzw/content/detail/id/242101/keyword_id/-1
- https://www.woshipm.com/share/6112301.html
- https://pdfs.semanticscholar.org/9cc6/206949c7e2e704bd55c74ba7478ff559ce50.pdf
- https://www.yalejournal.org/publications/micro-drama-as-soft-power-yedbr
- https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/short-form-video-series.html
- https://www.shortimize.com/blog/youtube-shorts-retention-rate
- https://humbleandbrag.com/blog/youtube-shorts-benchmarks
- https://retensis.com/blog/tiktok-retention-rate-benchmarks-2026
- https://www.opus.pro/blog/tiktok-length-format-retention-data
- https://metricool.com/youtube-shorts-algorithm/
- https://buffer.com/resources/the-creators-guide-to-youtube-shorts-analytics/
- https://www.tiktok.com/creator-academy/en/article/analytics-tool-video-performance
- https://kreatli.com/guides/safe-zone-guide
- https://adaptlypost.com/en/blog/social-media-safe-zones-2026-complete-guide
- https://dcmp.org/learn/603-captioning-key---speaker-identification
- https://www.3playmedia.com/blog/verizon-media-and-publicis-media-find-viewers-want-captions/
- https://www.contentfries.com/blog/the-science-of-video-captions-how-they-impact-audience-retention
- https://theatrecrafts.com/pages/home/topics/sound/radio-drama/
- https://nofilmschool.com/start-late-leave-early
- https://www.capcut.com/create/cliffhanger-endings-short-form-video-series
- https://sumera.io/blog/how-long-should-youtube-script-be
- https://www.c21media.net/news/vigloo-unveils-ya-microdrama-made-in-just-two-months-by-tiny-team-using-ai/
