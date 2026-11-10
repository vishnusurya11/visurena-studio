# Testing YouTube growth on a small AI animation channel, and what to publish first

*Source date: 2026-10-21. An audit of one channel's public numbers, a pre-registered test plan, and a ranked list of open-source packages. The data was thin, most early plans did not survive review, and the one change that could be measured was made before the next round of tests.*

## The question

The studio makes short AI-animated episodes of public-domain books and posts them to one YouTube channel. Two questions came up:

1. What should the channel change to grow, and which changes can the studio actually tell apart from luck?
2. Which parts of the studio's code and research are worth publishing as public, reusable work?

Terms used below:

- **Short**: a YouTube video up to about three minutes in a square or vertical frame. Every episode here is a square Short of 2 to 3 minutes.
- **Long-form**: a normal YouTube video. The channel's long-form uploads are full-book audiobooks and two compilations.
- **YPP**: the YouTube Partner Program, the route to ad revenue. It needs watch hours or Shorts views, plus subscribers.
- **APV**: average percentage viewed, the share of a video that the average viewer watches.
- **Engaged views**: a YouTube count of views that go past the first frame or are played by a click.
- **PREREG**: a pre-registration, a written test plan with its statistic, sample size and win line, saved before any test runs.
- **Mann-Whitney test**: a rank test that compares two groups of videos without assuming a shape for the views.

## What existed before

- The channel had 65 subscribers, 13,921 public views and 136 videos, 134 public and 2 private, at the time of the read.
- The channel had no playlists for its series, no analytics permission in the stored login (so no retention or traffic-source data), and no caption step in its episode process.
- The public code repository was already visible on GitHub, with no licence file, no front-page README, two stray files in its root, and a copy 299 commits behind the local master.
- Earlier research folders on the face-fidelity benchmark had already produced results, but none had been run as a pre-registered test.

## Method

- **Data.** Read-only calls to the YouTube Data API for channel and video counts. The stored login had upload and force-ssl scopes only, so no analytics data was read. Every number in the series table was recomputed offline from the saved channel snapshot.
- **Research.** One research agent wrote the first report. It checked about 16 web sources and the official YouTube API references.
- **Debate.** Two critics reviewed the report, one a growth strategist and one an open-source maintainer. The skeptic raised 19 points (1 fatal, 9 major, 9 minor). The domain expert raised 12 points. One defender answered all 31 points in one rebuttal round, and the rebuttal re-measured several numbers.
- **Ruling.** A separate reviewer (the gavel) checked the disputed points against live sources and gave a ruling on each of 73 claims.
- **Power check.** The test sizes were checked with a t-based minimum-detectable-effect calculation on log views (within-series standard deviation about 0.71 to 0.72, 41 episodes) and an exact Mann-Whitney check at small n.
- **Pre-registration.** PREREG.md was written after the report, before any test ran. Every Part A comparison in the report is labelled exploratory, because the data was looked at before the comparisons were chosen.
- **Actions.** After the owner's go, the growth changes were applied through the API by a script with a fake-API test suite, followed by a read-only after-check of all 136 videos.
- **Agents.** Five agent roles took part (research, two critics, defender, gavel) in one critique round and one rebuttal. The later action and repository passes were run separately and are not counted here.

## Results

### Channel snapshot (all public counts, 2026-10-21)

| Measure | Value |
|---|---|
| Subscribers | 65 |
| Public views | 13,921 |
| Videos | 136 (134 public, 2 private) |
| Subscribers per 1,000 views | 4.67 |
| Series playlists before the change | none |
| Analytics scope on the stored login | no |

### Series Shorts and long-form

| Group | Episodes | Total views | Median views | Mean views | Likes per view | Comments |
|---|---|---|---|---|---|---|
| Scarlet Shorts | 14 | 2,512 | 130.5 | 179 | 0.022 | 0 |
| War of the Worlds Shorts | 27 | 4,149 | 107 | 154 | 0.025 | 0 |
| Jekyll and Hyde episode 1 | 1 | 74 | not enough data | not enough data | 2 likes | 0 |
| Compilations (long-form) | 2 | 95 | not enough data | not enough data | not enough data | not enough data |

The compilations are the full-length Scarlet (37:46) and War of the Worlds (1:09:57) cuts. A private duplicate of the Scarlet compilation with 2 views is not counted above.

### Where the views come from

| Group | Videos | Views | Share of all views | Views per day | Median age (days) | Runtime (hours) |
|---|---|---|---|---|---|---|
| 2025 full audiobooks | 31 | 6,094 | 43.2% | 15.7 | 401 | 158 |
| War of the Worlds Shorts | 27 | 4,149 | 29.4% | 208.9 | 21 | about 1 |
| Scarlet Shorts | 14 | 2,512 | 17.8% | 70.5 | 36 | about 1 |
| Other 2026 (Classics Reborn, fan film) | 4 | 868 | 6.2% | 11.0 | 106 | 0 |
| Generic AI stories (Jan and Feb 2026) | 55 | 312 | 2.2% | 1.2 | 264 | 69 |
| Compilations | 2 | 95 | 0.7% | 8.8 | 11 | 2 |
| Jekyll and Hyde episode 1 | 1 | 74 | 0.5% | 86.9 | 1 | 0 |

Views per day is each video's lifetime views divided by its age, summed over the group. Older videos have had more time to collect views, so the shares and the per-day rates are both skewed by age. The audiobooks are the largest share of views over time. The Shorts are the largest share of current daily views. An unreconciled point: the rebuttal says the series Shorts run at 366 views per day, 23 times the audiobooks. The table above adds to about 279 per day, about 18 times. This report uses the table.

### YPP arithmetic at today's rates

| Route | Requirement | Channel today | Gap |
|---|---|---|---|
| Shorts views | 10 million per 90 days (20 million from 2027-02-01) | about 15,600 per 90 days | about 639 times short (about 1,279 for the 2027 bar) |
| Watch hours (long-form) | 4,000 hours (8,000 from 2027-02-01) | projected 845 to 5,070 hours per year, depending on average view length | at 30-minute average view, the projected hours already meet the 4,000 bar |
| Subscribers | 1,000 | 4.67 per 1,000 views, about 1.9 per day | about 503 days |

The watch-hour row is the most uncertain. It assumes lifetime rates, not the last 365 days that YPP counts, and the average view length was not measured. The subscriber route is a second constraint that neither the first report nor the critics named.

### Minimum effect a two-group test can detect

The smallest views ratio a test can detect, at 80% power and alpha 0.05, using the spread of the series' views:

| Episodes per arm | 3 | 5 | 7 | 10 | 13 | 20 | 30 | 40 |
|---|---|---|---|---|---|---|---|---|
| Detectable views ratio | 8.76x | 4.24x | 3.21x | 2.58x | 2.27x | 1.92x | 1.69x | 1.57x |

A smaller sd (0.71, from the critic's run) gives 5.0x at 3 per arm and 1.6x at 40 per arm. Either way, the detectable effect at the first report's sizes is far larger than the +10 to +25% wins it proposed.

### Rate metrics

| Metric | Result | Reading |
|---|---|---|
| Likes per view | mean 0.024, between-video sd 0.0123, binomial floor 0.0152 | the spread is mostly count noise (ratio 0.80) |
| Subscribers per 1,000 views | 4.61 | about 0.49 subscribers per episode; a +30% change needs about 410 episodes per arm |
| Engaged views divided by views (the swipe proxy) | not yet readable | at the median of 106 views, a binomial floor of about plus or minus 4 points at 20 per arm |

### Comments

The series Shorts have 0 comments on 6,735 views. The other videos have 21 comments on 7,369 views. At the other videos' rate the series would have about 19 comments, and the chance of seeing 0 is about 4.6 in 10 billion. Comments are enabled and nothing is held for review, so the quiet audience is real, not a setting.

### The growth tests, after review

| Original item | Verdict after review | Why |
|---|---|---|
| Upload hour test | dropped | the worst bucket is the youngest videos; no signal |
| Retitle half of War of the Worlds | dropped as a test | needs a 2.27x ratio at 13 per arm; old Shorts get almost no new traffic |
| Fixed upload slot (18:00 against 10:00) | dropped as a test | needs a 4.24x effect at 5 per arm |
| Next-episode end tease | kept as craft, not tested | needs about 410 episodes per arm |
| Pick books by search demand | dropped | no search data was collected; the sign flips when corrected for age |
| Comment prompt | dropped | the audience leaves no comments |
| Hook text plus captions | kept as the one real Shorts test, re-sized | needs about 35 to 40 episodes per arm, not 20 |
| Micro-Short (20 to 45 seconds) | kept, as its own edit | a plain trim risks YouTube's repetition rules |

The review gave 73 rulings on the report and its debate: 25 holds, 32 holds with changes, 16 falls. Every win rule in the first report was retired.

### Public repository checks

| Check | Result |
|---|---|
| Secret scan, full history (regex stand-in, 1,028 commits) | 0 hits; 5 of 5 planted test keys caught |
| gitleaks over the full history (1,374 commits) | 0 leaks |
| gitleaks over the 350 commits pushed | 0 leaks |
| Licence before | none |
| Licence after | Apache License 2.0, detected by GitHub |
| Stray files in the root | a saved HTML error page named as a PDF, and an ffmpeg log; both removed |
| Commits behind local master before the push | 299 |
| Push | fast-forward only, 350 commits; no force push |

### Growth changes applied on 2026-10-21 (after the owner's go)

| Change | Count | Read back |
|---|---|---|
| Playlists created, in episode order | 3 (Scarlet 14 of 14; War of the Worlds 27 of 27; Jekyll and Hyde 1 of 10 at the time) | yes |
| Episode descriptions given a "watch in order" block | 42 | yes, old text kept |
| Compilations retitled with search-friendly titles | 2 | yes |
| Generic AI stories set to unlisted (not deleted) | 55 | yes |
| After-check across all videos and playlists | 0 faults | yes |

Three times during the run a read came back stale right after a write. The script halted, confirmed the live state, added a bounded re-read, and resumed without writing anything twice.

### Images

See the captions below. No H3-rendered video frames are in these cards.

## Images

![The first summary card, written before the debate. Look at the "My pick" box: it puts the face-fidelity benchmark paper first, a ranking the later rounds reversed.](images/summary_v1_initial_card.png)

![The card after the debate and rebuttal. Look at the "Tests" line: a views test needs a 2.3x to 8.8x effect to beat the noise, depending on sample size.](images/summary_v2_after_debate_card.png)

![The verdict card. Look at the "T1 sizing" line: the planned 20-per-arm hook test fails its own rule, and "Old item 2" shows a 3-versus-3 rank test cannot reach p below 0.05.](images/summary_v3_verdict_card.png)

## Verdict

- **Measure first.** The analytics permission is the instrument for everything else. The next weekly sign-in needs one extra permission tick, and the channel's per-video daily rows can then be back-filled for all 136 videos.
- **Most of the first growth plan does not hold.** Its win rules could not be told apart from noise at the sizes proposed.
- **The best-evidenced lever is long-form search.** The audiobooks carry 43% of all views and most of the watch hours. Re-titling the compilations for search, adding chapters and linking them from every episode is the strongest case, and YouTube's own title test can randomise it.
- **Hook text and captions stay as the one real Shorts test,** at about 35 to 40 episodes per arm.
- **Publishing order:** fix the public repository first (licence, README, stray files, history scan), then publish the replay tool for fake ComfyUI servers, which had no public equivalent in the searches made. A gate pull request to the existing face-refine pack (527 stars on GitHub) is the next step after that.
- **The benchmark paper waits.** Its headline claim (more pixels per face beats prompts, crops and upscalers) was a reading of tests that failed their own rules. It can be asked as a question, after the eye-metric check is validated and a pre-registered run covers at least 30 faces, 3 seeds and 2 open model families.
- **Legal flag only.** The licence question about the MiniMax-H3 model covers the whole channel, not only the benchmark clips, because all 42 public episodes use the model. It was logged for the studio's legal review. No view is given here.

## What changed in the pipeline

- The public repository received an Apache-2.0 licence file and a root README, and the two stray files were removed in one commit (c38d88f). The remote had been 299 commits behind the local master; the 350 commits in the push range were sent as a fast-forward.
- The growth applier was extended with a bounded re-read after writes, tested first with a fake API.
- The three playlists, the 42 episode description blocks, the two compilation retitles and the 55 unlistings were applied through the API. Nothing was deleted or re-uploaded.
- Not changed: the shared compilation code still builds the old titles, so a future compilation retitle would put them back. The fix is pending and must be tested first. Test & Compare title tests exist only in the YouTube Studio interface, not the API.
- Not yet built: pipeline steps that add a new episode to its playlist, and a "next episode" line on the previous one.

## Limits and open questions

- No retention, traffic-source or search data exists yet. Every growth number here is a lifetime public count from one channel with 42 series episodes.
- Views per day are lifetime averages. Recent rates need the analytics permission.
- The watch-hour projection depends on an average view length that was not measured.
- The engaged-views ratio is named as the swipe proxy, but on Shorts it may sit near 1 and show no spread. This is a day-one check, not a measured failure.
- Whether the "related video" link on Shorts is a usable route is unknown. Sources disagree.
- The "no comparable tool" claim for the fake ComfyUI server rests on searches. A missing search hit is not proof.
- The secret scans cover common key formats only.
- Before the push, the repository's test run had four failures in other work-in-progress code. The push did not re-run the suite.
- The public "2026" playlist still lists the 55 unlisted stories, which keeps them playable from the channel's Playlists tab. Making it private was not part of the go.
- The effort estimates in the packages plan (for example 33 hours for the replay tool, 20 to 40 hours for the face-gate contribution) are guesses with no stated basis.
- Peer-channel comparison (a cross-section of other channels, costing only API quota) was proposed but not run.

## Sources

- REPORT (research agent, 2026-10-21)
- DEBATE critic, skeptic (2026-10-21)
- DEBATE critic, domain expert (2026-10-21)
- REBUTTAL (defender, 2026-10-21)
- PREREG (growth tests, written 2026-10-21 before any test ran)
- VERDICT (gavel, 2026-10-21)
- RESULT, growth actions (2026-10-21)
- RESULT, public repository review (2026-10-21)
- Summary cards: 00_SUMMARY, 00_SUMMARY_v2, 00_SUMMARY_v3_verdict (2026-10-21)
