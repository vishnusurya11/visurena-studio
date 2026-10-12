# Jekyll and Hyde: style A scene samples (2026-10-12)

The owner chose **style A (photoreal gothic)**. Style C was dropped before any C render, so this pass rendered no C pictures and no C video.
Recipe: `image_krea2_turbo_t2i`, no LoRA, 1:1, 2 MP (1448²), refine off. The lead is the look test's (book refs words plus "fog, gaslight, deep shadow").
Each scene has one seed, `crc32("jekyll_samples/<scene>")`. Local ComfyUI, $0.

## Files

- Sheet (A × 6, #0f1012): `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-12_jekyll_style_samples\samples_sheet.jpg`
- Stills: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-12_jekyll_style_samples\A\`
  `1_door_walk.png`, `2_trampling.png`, `3_fireside.png`, `4_carew.png`, `5_lanyon.png`, `6_cabinet_door.png`
- H3 take (scene 3, 768², 90 frames, 3.75 s, with native audio): `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-12_jekyll_style_samples\A_3_fireside_h3.mp4`
- Prompts: `scenes.json`. Scripts: `render.py` (stills), `take.py` (H3), `make_sheet.py`. Per-render seconds and prompts: `times.jsonl`.

## Time

- Each still took **15.1 to 15.4 s** warm, so all six took 92 s.
- The H3 take (`video_minimax_h3_i2v_turbo`, unchanged, 8 steps) took **127 s** at 768² × 90 frames.

## Faults read by eye

1. **The door walk (ch1).** Utterson wears a bowler and Enfield a grey top hat; the two men are distinct. The building reads right: blank plaster above and a blistered door at the top of worn steps. But the plaster upper storey still has small windows at its left edge. This is better than the look test, not perfect.
2. **The trampling (ch1).** This is the weakest still. **Hyde reads as a stooped, long-haired *older* man.** He is not sinister and not young, his side-whiskers do not show, and his hat has a **tall crown (close to a top hat), not a low felt hat**. The child stands beside him instead of lying fallen, so the scene shows no menace. The lamp, fog and corner are good.
3. **Jekyll's fireside (ch3).** This is the strongest still. Jekyll (right) is visibly fifty: grey, smiling, with a wine glass. Utterson (left) is lean and unsmiling, but his hair came out **grey-fair rather than dust-fair**, so the two men read closer in age than the heads intend. There is no duplicate figure and no lettering.
4. **The Carew murder (ch4).** The moon, fog and railings work, and the cane is raised. Hyde is a backlit figure in a low-crowned hat, so he reads better here. But the cane renders as a **hooked crook** and Hyde is not small beside Carew. Both figures are lit rather than silhouetted.
5. **Lanyon stricken (ch6).** He has a shock of white hair and a grey, shaken face beside the lamp, with a skull on the shelf. The "ruddy" in the prompt is lost to the "stricken pale" wording, which is acceptable for this beat. He reads as older than fifty.
6. **The cabinet door (ch8).** Poole has grey mutton-chop whiskers and a tailcoat, and holds the axe over his shoulder. Utterson holds the poker, the red baize door is behind them, and his shadow is on the wall. The scene is good. Utterson's hair here is long and fair-grey, which does not match his look in scene 3.

None of the six has lettering, a signature or a ghost figure.

**The H3 take** opens on frame 0 of the still. Both identities hold through the take, and Jekyll lifts his glass while the fire flickers. **The push-in is barely visible over 3.75 s.** The take shows that the still animates cleanly, not the camera move. This matches the known H3 behaviour that the model obeys a move's direction but not its amount.

## Recommendation

Keep A. It delivers the setting, light and supporting cast (Enfield, Lanyon, Poole) from words alone. **Hyde is still the unsolved character.** Prompt words do not make him young and sinister, and "felt hat" drifts to a tall crown. Fix him at the reference-sheet stage, not per scene:

- Give Hyde his own base sheet, with an explicit young face (about twenty-five), a sneer, and a "soft, shapeless, low-crowned felt hat (a wideawake)".
- Stage that sheet into every Hyde scene.
- Pin Utterson's hair as pale sandy, so it does not drift to grey.
