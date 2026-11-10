# Visurena Studio: Research Archive

Visurena Studio turns public-domain books (Jekyll and Hyde, The War of the Worlds, A Study in Scarlet) into short AI-made video episodes on one local GPU. Every design choice is tested first, often with pre-registered rules, expert panels and a skeptic. This archive holds one write-up per research topic. Each folder has a README.md (question, method, numbers, verdict, limits), an images folder, and an audio folder where listening samples exist.

Failures are reported as plainly as wins. Several topics end in "not shown" or "rejected". That is the point of pre-registering a rule.

## Index

| # | Topic | Date | One line | Verdict | Images |
|---|-------|------|----------|---------|--------|
| 01 | [Face blur and eyes](01_face_blur_and_eyes/README.md) | 2026-10-19 | A face-crop refine pass on blurry anime faces | Ship refine for mid-size faces (about 33-68 px); faces under about 20 px need closer framing, not a refine | 9 |
| 02 | [Face warp fix](02_face_warp_fix/README.md) | 2026-10-19 | Refine pasted a whole square back and made hats and collars wobble | Face-only paste removes the ring change in replay; not yet a shipped fix (no GPU bench) | 7 |
| 03 | [Face debate, five rounds](03_face_debate_five_rounds/README.md) | 2026-10-21 | 8 proposals and 3 refutations per round, then a bounded GPU bench | Eye floor is the model's 32 px token; only more pixels per face moved the eye | 9 |
| 04 | [Singularity v1.3 vs v2](04_singularity_v1_3_vs_v2/README.md) | 2026-10-21 | Newer video-model fine-tune swapped into four small-face takes | Rejected: no clear face gain, 4.9x slower; production stays on v1.3 | 6 |
| 05 | [FastH3-Omni vs production](05_fasth3_omni_vs_production/README.md) | 2026-10-21 | Does another video model draw small faces better? | Production stays; eyes improved on 1 of 6 faces, rule needed 4 | 5 |
| 06 | [Take prompt rewrite bench](06_take_prompt_rewrite_bench/README.md) | 2026-10-21 | Pre-registered bench of a rewritten shot prompt | Full rewrite lost (2 of 4, needed 3); its push-in rule for held shots won both held takes | 5 |
| 07 | [Shot framework panel](07_shot_framework_panel/README.md) | 2026-10-21 | Ten-seat panel and gavel on shots the model can hold | Only rules the measurements supported were kept; slow push retired as a freeze cure | 7 |
| 08 | [Craft and process panel](08_craft_and_process_panel/README.md) | 2026-10-21 | Ten experts on how episodes are written and checked | 31 changes adopted, 26 built; the rest wait on samples | 0 |
| 09 | [Voice bench and speaker gate](09_voice_bench_and_speaker_gate/README.md) | 2026-10-21 | New open-weight TTS vs production; found a sample-rate bug | Keep IndexTTS-2; speaker gate bug passed 70 of 152 wrong voices, 3 of 152 after the fix | 3 (+4 audio) |
| 10 | [Lip sync and mouth ruler](10_lip_sync_and_mouth_ruler/README.md) | 2026-10-21 | Feeding the recorded line to H3 as an audio reference | Not shown; keep production; the mouth ruler failed its own tests | 4 (+8 audio) |
| 11 | [YouTube growth and open source](11_youtube_growth_and_open_source/README.md) | 2026-10-21 | Audit of a small channel, test plan, ranked open-source packages | Measure first; long-form search is the best-evidenced lever | 3 |
| 12 | [Proof harness and rehearsals](12_proof_harness_and_rehearsals/README.md) | 2026-10-21 | Can episode 2 be proven under 6 h before GPU spend? | No pass earned yet; time model within 15 percent on 2 of 9 episodes | 4 |
| 13 | [Deadline retro, 30 h to 6 h](13_deadline_retro_30h_to_6h/README.md) | 2026-10-20 | Why a 6.02 h machine run took 30.85 h wall time | Unmeasured picture faults and broken repairs drove the rework; 4.7 h projection unproven | 0 |
| 14 | [Five iterations, ten experts](14_five_iterations_ten_experts/README.md) | 2026-10-20 | Five review rounds, ten experts each, a chair checking claims | 31 h wall time became a 4.0 h projection; large wall gains depend on unbuilt items | 9 (+3 audio) |
| 15 | [Kawajiri episode 1 retro](15_kawajiri_ep01_retro/README.md) | 2026-10-19 | Overnight retro with many agents; 16 fixes built | Fixes tested and projected to fit; fit unproven until the next run | 0 |
| 16 | [Agent triggering and durable tasks](16_agent_triggering_and_durable_tasks/README.md) | 2026-10-22 | Can agent calls run as durable jobs that wait out the usage limit? | Limit defect fixed (a shut window now waits, no sleep); job runner passed its crash and classifier benches but failed its registered wall rule, so it is not built as the default | 8 |
| 17 | [Orchestration and parallel scheduling](17_orchestration_and_parallel_scheduling/README.md) | 2026-10-22 | Where episode machine time goes, and whether two episodes may share the GPU | The card is the bottleneck; step order saves about 0.1 min; sharing the card stays "no" under the registered rule (a risk call for the owner) | 5 (3 held: H3 frames) |
| 18 | [Audio, music, Foley, mix and acting](18_audio_music_foley_mix_acting/README.md) | 2026-10-22 | Pre-registered bench of the music bed, ambience, Foley, dialogue acting, mix and cue sheet on one episode | Nothing switched in production; one defect fixed (sung music tones are re-rolled); bed and acting choices wait for the owner's listen | 8 (+4 audio, HELD until the owner scores the blind listens) |

Total: 92 images, 19 audio files.

## Publication note

Images and audio rendered by MiniMax-H3 are held from publication until the studio's licence review clears them. The MiniMax-H3 licence question is with the studio owner's attorney. This note takes no legal view. Topics that contain H3 frames (01 to 07, 10, 14) are marked inside their READMEs. Topics 09 (voice), 11 (summary cards), 12 (Qwen-Image grids) and the text-only topics (08, 13, 15) hold no H3 video frames, though topic 10's audio is H3-generated and is covered by the hold.

## Conventions

- Dates are Seattle time (PDT).
- Absolute local paths, credentials and personal details are scrubbed.
- All numbers come from the studio's audit logs. Where a source is silent, the README says "not stated".
- Nothing here has been published.
