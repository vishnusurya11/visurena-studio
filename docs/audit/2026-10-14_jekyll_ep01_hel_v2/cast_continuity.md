# Jekyll HEL ep01 v2: cast continuity, shot by shot (2026-10-14)

L = the lawyer (Utterson), E = Enfield, H = Hyde (clean-shaven, per the ruling), G = the girl.
"present" = the setup's cast. "grid sheets" = whom the grid that drew the panel staged by sheet, read from the
grid prompt's `The person in <imageN> wears:` lines. "take sheets" = the cast sheets in the take's `refs`
(`takes/r2v/shots.json`). "panel people" / "take people" = how many people the content reader counted in the
panel and in the take.

G-PRESENT was **clean** before anything was drawn:
- every scene opens on a picture that holds its people;
- the girl's arrival is marked (`enters`, shot 5);
- Enfield is at the crossroads from its first shot, as the book's witness (shots 3, 6, 7);
- the girl's family and the doctor are framed out of the door scene (shots 8-10, tight over Enfield's shoulder) and of shot 7 (the writer's improve rung dropped them);
- v1's empty-set wides and word-drawn strangers are gone: shot 0 shows the two men from their sheets (`frames_every_10s.jpg`, 0.5 s).

| shot | setup | size | present (setup cast) | faces | extras | enters | grid sheets | take sheets | panel people | take people |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | door_day | wide | L,E | L,E | 0 | - | door_day_1x1_a: L,E | L,E | 2 | 2 |
| 1 | door_day | medium_close | L,E | E | 0 | - | door_day_1x1_s01: E | E | 1 | 1 |
| 2 | door_day | medium_close | L,E | L,E | 0 | - | door_day_1x1_s02: L,E | L,E | 1 | 2 |
| 3 | night_cross_street | full | E,H,G | E,H | 0 | - | night_cross_street_1x1_a: E,H | E,H | 2 | 1 |
| 4 | night_cross_street | medium | E,H,G | H | 0 | - | night_cross_street_1x1_b: H | H | 1 | 1 |
| 5 | night_cross_street | medium | E,H,G | G | 0 | G | night_cross_street_1x1_c: G | G | 2 | 1 |
| 6 | night_cross_street | full | E,H,G | H,G,E | 0 | - | night_cross_street_1x1_d: H | H,G,E | 3 | 3 |
| 7 | night_cross_street | full | E,H,G | E,H,G | 0 | - | night_cross_street_1x1_e: E | E,H,G | 3 | 3 |
| 8 | night_door | medium | E,H | H,E | 0 | - | night_door_1x1_a: H,E | H,E | 2 | 2 |
| 9 | night_door | insert | E,H | H | 0 | - | night_door_1x1_b: H | H | 1 | 1 |
| 10 | night_door | insert | E,H | H,E | 0 | - | night_door_1x1_c: H,E | H,E | 2 | 2 |
| 11 | pavement_day | medium | L,E | E,L | 0 | - | pavement_day_2x2_a: E,L | E,L | 2 | 2 |
| 12 | pavement_day | medium | L,E | L,E | 0 | - | pavement_day_2x2_a: E,L | L,E | 2 | 2 |
| 13 | sunday_street | medium | L,E | L,E | 0 | - | sunday_street_2x2_a: L,E | L,E | 2 | 2 |
| 14 | sunday_street | medium_close | L,E | E,L | 0 | - | sunday_street_2x2_a: L,E | E,L | 2 | 2 |
| 15 | sunday_street | medium | L,E | L,E | 0 | - | sunday_street_2x2_a: L,E | L,E | 2 | 2 |
| 16 | sunday_street | insert | L,E | L | 0 | - | sunday_street_2x2_a: L,E | L | 1 | 1 |
| 17 | sunday_street | medium_close | L,E | L | 0 | - | sunday_street_1x1_b: L | L | 1 | 1 |
| 18 | pavement_day | medium | L,E | E,L | 0 | - | pavement_day_2x2_a: E,L | E,L | 2 | 2 |
| 19 | pavement_day | medium_close | L,E | E,L | 0 | - | pavement_day_2x2_a: E,L | E,L | 2 | 2 |
| 20 | pavement_day | insert | L,E | L,E | 0 | - | pavement_day_1x1_b: L,E | L,E | 2 | 2 |
| 21 | pavement_day | medium_close | L,E | L | 0 | - | pavement_day_1x1_c: L | L | 1 | 1 |
| 22 | door_day | wide | L,E | L,E | 1 | - | door_day_1x1_b: L | L,E | 3 | 3 |

## Where staging and visibility part (flags, not refusals)

| shot | what | why |
|---|---|---|
| 2 | the panel lost Enfield's shoulder (1 person for 2 named) | panel eye keep_best. The take staged both sheets and shows 2 |
| 3 | the take shows 1 person; Enfield's shoulder and hat at the left edge leave the frame as the camera pans with Hyde | planned pan with the walker. Enfield stays present in the scene (G-PRESENT holds) |
| 5 | the panel holds 2 (the girl plus Enfield's foreground shoulder); plan said 1 + 0 extras | scene continuity; panel eye keep_best, flagged |
| 6, 7 | the grid staged only H (6) and only E (7) by sheet; the others were drawn from wardrobe words | over the slot ceiling `scene_cast.pick` kept the closest faces. The takes staged all three sheets and show 3 |
| 22 | the grid staged only L; Enfield drawn from words | slot ceiling. The take staged both and shows both, plus the tramp (extras 1) |
| 1 | the door behind Enfield reads red with brass fittings, unlike the blistered brown door of shot 0 | a room-chain drift in grid s01; panel_place is advisory |

No person appears from nowhere in the cut. The identity row flags Enfield DRIFT in T01 (0.74), T02 (0.72) and T19 (0.52):
advisory (`TAKE_IDENTITY_HARD = False`), read by the master eye.
