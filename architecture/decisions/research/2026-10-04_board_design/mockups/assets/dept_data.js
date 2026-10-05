/* captured read-only 2026-10-05T02:33:12+00:00 by scratchpad/capture.py */
window.BOARD={
"captured": "2026-10-05T02:33:12+00:00",
"steps": [
"bind",
"plan",
"places",
"record",
"timeline",
"prompts",
"board",
"panels",
"shoot",
"edit",
"qc",
"deliver"
],
"gates": [
"PLAN",
"LAYOUT",
"EYE_PANELS",
"EYE_TAKES",
"MASTER",
"RENDER"
],
"dept": {
"books": {
"20260822113400": "A Study in Scarlet",
"20260827135508": "The War of the Worlds"
},
"counts": {
"running": 1,
"flagged": 5,
"queued": 3,
"blocked": 7,
"done": 15
},
"rows": [
{
"codex_id": "20260827135508",
"unit": "ep17",
"state": "running",
"shown": "running",
"step_id": "07",
"step_name": "board",
"progress": null,
"attempts": 3,
"flags": 3,
"blocked_on": null,
"updated_at": "2026-10-05T02:24:18Z",
"gpu_seconds": 1100.3,
"cost_usd": 0.34584,
"elapsed": "2h12",
"started_at": "2026-10-05T00:21:11.929009Z",
"gates": {
"PLAN": [
16,
"APPROVE",
"",
"⚑16",
"judge:plan@1"
]
},
"steps": {
"01": [
"skipped",
1,
""
],
"02": [
"done",
4,
""
],
"03": [
"skipped",
1,
""
],
"04": [
"skipped",
1,
""
],
"05": [
"skipped",
1,
""
],
"06": [
"done",
2,
""
],
"07": [
"running",
1,
""
]
},
"title": "The Thunder Child",
"face": "episodes/ep17/storyboard/shot_04.png",
"frames": [
"episodes/ep17/storyboard/shot_00.png",
"episodes/ep17/storyboard/shot_02.png",
"episodes/ep17/storyboard/shot_04.png",
"episodes/ep17/storyboard/shot_06.png",
"episodes/ep17/storyboard/shot_08.png",
"episodes/ep17/storyboard/shot_10.png",
"episodes/ep17/storyboard/shot_12.png",
"episodes/ep17/storyboard/shot_14.png"
],
"contact": null,
"face_src": "storyboard panel",
"iters": 0,
"eta": "21:35",
"elapsed_s": 2263.403507232666,
"work_s": 6759.203507232666
},
{
"codex_id": "20260827135508",
"unit": "ep12",
"state": "done",
"shown": "flagged",
"step_id": "12",
"step_name": "deliver",
"progress": "12/12",
"attempts": 31,
"flags": 4,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:42Z",
"gpu_seconds": 35227.1,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-25T03:20:52.945136Z",
"gates": {
"PLAN": [
7,
"APPROVE",
"",
"⚑7",
"judge:plan@1"
],
"EYE_PANELS": [
531,
"flagged",
"keep_best",
"⚑531",
"judge:panel_eye@1"
],
"EYE_TAKES": [
0,
"pass",
"",
"✓",
"judge:take_eye@1"
],
"MASTER": [
3,
"",
"flag",
"⚑3",
"judge:master_eye@1"
]
},
"steps": {},
"title": "Weybridge and Shepperton",
"face": "episodes/ep12/storyboard/shot_06.png",
"frames": [
"episodes/ep12/storyboard/shot_00.png",
"episodes/ep12/storyboard/shot_03.png",
"episodes/ep12/storyboard/shot_06.png",
"episodes/ep12/storyboard/shot_09.png",
"episodes/ep12/storyboard/shot_12.png",
"episodes/ep12/storyboard/shot_15.png",
"episodes/ep12/storyboard/shot_18.png",
"episodes/ep12/storyboard/shot_21.png"
],
"contact": "episodes/ep12/review/contact_faf11c8f.png",
"face_src": "storyboard panel",
"iters": 7
},
{
"codex_id": "20260827135508",
"unit": "ep13",
"state": "done",
"shown": "flagged",
"step_id": "12",
"step_name": "deliver",
"progress": "2/12",
"attempts": 52,
"flags": 20,
"blocked_on": null,
"updated_at": "2026-09-28T14:19:21Z",
"gpu_seconds": 75790.7,
"cost_usd": 0.759764,
"elapsed": "",
"started_at": "2026-09-25T17:40:25.848105Z",
"gates": {
"PLAN": [
0,
"APPROVE",
"",
"✓",
"judge:plan@1"
],
"EYE_PANELS": [
4,
"flagged",
"keep_best",
"⚑4",
"judge:panel_eye@1"
],
"EYE_TAKES": [
2,
"flagged",
"keep_best",
"⚑2",
"judge:take_eye@1"
],
"MASTER": [
3,
"",
"flag",
"⚑3",
"judge:master_eye@1"
]
},
"steps": {
"01": [
"skipped",
2,
""
],
"02": [
"skipped",
17,
""
],
"03": [
"skipped",
0,
""
],
"04": [
"skipped",
2,
""
],
"05": [
"skipped",
4,
""
],
"06": [
"skipped",
19,
""
],
"07": [
"skipped",
13,
""
],
"08": [
"skipped",
15,
"keep_best"
],
"09": [
"skipped",
15,
"keep_best"
],
"10": [
"skipped",
6,
""
],
"11": [
"done",
10,
"flag"
],
"12": [
"done",
1,
""
]
},
"title": "How I Fell in with the Curate",
"face": "episodes/ep13/storyboard/shot_06.png",
"frames": [
"episodes/ep13/storyboard/shot_00.png",
"episodes/ep13/storyboard/shot_03.png",
"episodes/ep13/storyboard/shot_06.png",
"episodes/ep13/storyboard/shot_09.png",
"episodes/ep13/storyboard/shot_12.png",
"episodes/ep13/storyboard/shot_15.png",
"episodes/ep13/storyboard/shot_18.png",
"episodes/ep13/storyboard/shot_21.png"
],
"contact": "episodes/ep13/review/contact_3927e8c3.png",
"face_src": "storyboard panel",
"iters": 13
},
{
"codex_id": "20260827135508",
"unit": "ep15",
"state": "done",
"shown": "flagged",
"step_id": "12",
"step_name": "deliver",
"progress": null,
"attempts": 36,
"flags": 27,
"blocked_on": null,
"updated_at": "2026-10-01T17:45:14Z",
"gpu_seconds": 10622.2,
"cost_usd": 4.11154,
"elapsed": "",
"started_at": "2026-10-01T04:42:45.477187Z",
"gates": {
"PLAN": [
2,
"APPROVE",
"",
"⚑2",
"judge:plan@1"
],
"EYE_PANELS": [
13,
"flagged",
"keep_best",
"⚑13",
"judge:panel_eye@1"
],
"EYE_TAKES": [
12,
"flagged",
"still",
"⚑12",
"judge:take_eye@1"
],
"MASTER": [
11,
"",
"flag",
"⚑11",
"judge:master_eye@1"
]
},
"steps": {
"01": [
"skipped",
1,
""
],
"02": [
"skipped",
25,
""
],
"03": [
"skipped",
7,
""
],
"04": [
"skipped",
2,
""
],
"05": [
"skipped",
2,
""
],
"06": [
"skipped",
8,
""
],
"07": [
"skipped",
1,
""
],
"08": [
"skipped",
1,
"keep_best"
],
"09": [
"skipped",
5,
"still"
],
"10": [
"done",
7,
""
],
"11": [
"done",
7,
"flag"
],
"12": [
"done",
1,
""
]
},
"title": "What Had Happened in Surrey",
"face": "episodes/ep15/storyboard/shot_04.png",
"frames": [
"episodes/ep15/storyboard/shot_00.png",
"episodes/ep15/storyboard/shot_02.png",
"episodes/ep15/storyboard/shot_04.png",
"episodes/ep15/storyboard/shot_06.png",
"episodes/ep15/storyboard/shot_08.png",
"episodes/ep15/storyboard/shot_10.png",
"episodes/ep15/storyboard/shot_12.png",
"episodes/ep15/storyboard/shot_14.png"
],
"contact": "episodes/ep15/review/contact_13dd9d77.png",
"face_src": "storyboard panel",
"iters": 5
},
{
"codex_id": "20260827135508",
"unit": "ep16",
"state": "done",
"shown": "flagged",
"step_id": "12",
"step_name": "deliver",
"progress": null,
"attempts": 31,
"flags": 37,
"blocked_on": null,
"updated_at": "2026-10-05T00:21:09Z",
"gpu_seconds": 9784.3,
"cost_usd": 2.692382,
"elapsed": "",
"started_at": "2026-10-01T17:45:15.006368Z",
"gates": {
"PLAN": [
6,
"APPROVE",
"",
"⚑6",
"judge:plan@1"
],
"EYE_PANELS": [
23,
"flagged",
"keep_best",
"⚑23",
"judge:panel_eye@1"
],
"EYE_TAKES": [
21,
"flagged",
"still",
"⚑21",
"judge:take_eye@1"
],
"MASTER": [
5,
"",
"flag",
"⚑5",
"judge:master_eye@1"
]
},
"steps": {
"01": [
"skipped",
1,
""
],
"02": [
"skipped",
14,
""
],
"03": [
"skipped",
8,
""
],
"04": [
"skipped",
3,
""
],
"05": [
"skipped",
4,
""
],
"06": [
"done",
18,
""
],
"07": [
"skipped",
12,
""
],
"08": [
"skipped",
12,
"keep_best"
],
"09": [
"skipped",
17,
"still"
],
"10": [
"done",
8,
""
],
"11": [
"done",
9,
"flag"
],
"12": [
"done",
7,
""
]
},
"title": "The Exodus Northward",
"face": "episodes/ep16/storyboard/shot_06.png",
"frames": [
"episodes/ep16/storyboard/shot_00.png",
"episodes/ep16/storyboard/shot_03.png",
"episodes/ep16/storyboard/shot_06.png",
"episodes/ep16/storyboard/shot_09.png",
"episodes/ep16/storyboard/shot_12.png",
"episodes/ep16/storyboard/shot_15.png",
"episodes/ep16/storyboard/shot_18.png",
"episodes/ep16/storyboard/shot_21.png"
],
"contact": "episodes/ep16/review/contact_3969b71b.png",
"face_src": "storyboard panel",
"iters": 3
},
{
"codex_id": "20260827135508",
"unit": "ep14",
"state": "done",
"shown": "flagged",
"step_id": "12",
"step_name": "deliver",
"progress": null,
"attempts": 34,
"flags": 26,
"blocked_on": null,
"updated_at": "2026-10-01T04:42:41Z",
"gpu_seconds": 122276.6,
"cost_usd": 2.804519,
"elapsed": "",
"started_at": "2026-09-28T14:19:21.505151Z",
"gates": {
"PLAN": [
2,
"APPROVE",
"",
"⚑2",
"judge:plan@1"
],
"EYE_PANELS": [
21,
"flagged",
"keep_best",
"⚑21",
"judge:panel_eye@1"
],
"EYE_TAKES": [
10,
"flagged",
"keep_best",
"⚑10",
"judge:take_eye@1"
],
"MASTER": [
8,
"",
"flag",
"⚑8",
"judge:master_eye@1"
]
},
"steps": {
"01": [
"skipped",
1,
""
],
"02": [
"skipped",
12,
""
],
"03": [
"skipped",
1,
""
],
"04": [
"skipped",
3,
""
],
"05": [
"skipped",
2,
""
],
"06": [
"skipped",
15,
""
],
"07": [
"skipped",
6,
""
],
"08": [
"skipped",
8,
"keep_best"
],
"09": [
"skipped",
18,
"keep_best"
],
"10": [
"skipped",
8,
""
],
"11": [
"done",
7,
"flag"
],
"12": [
"done",
1,
""
]
},
"title": "The Great Panic",
"face": "episodes/ep14/storyboard/shot_06.png",
"frames": [
"episodes/ep14/storyboard/shot_00.png",
"episodes/ep14/storyboard/shot_03.png",
"episodes/ep14/storyboard/shot_06.png",
"episodes/ep14/storyboard/shot_09.png",
"episodes/ep14/storyboard/shot_12.png",
"episodes/ep14/storyboard/shot_15.png",
"episodes/ep14/storyboard/shot_18.png",
"episodes/ep14/storyboard/shot_21.png"
],
"contact": "episodes/ep14/review/contact_abf09823.png",
"face_src": "storyboard panel",
"iters": 8
},
{
"codex_id": "20260827135508",
"unit": "ep01",
"state": "queued",
"shown": "queued",
"step_id": null,
"step_name": "",
"progress": null,
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:26Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": null,
"gates": {},
"steps": {},
"title": "The Eve of the War",
"face": null,
"frames": [],
"contact": "episodes/ep01/review/contact_b2c111e9.png",
"face_src": "",
"iters": 6
},
{
"codex_id": "20260827135508",
"unit": "ep02",
"state": "queued",
"shown": "queued",
"step_id": null,
"step_name": "",
"progress": null,
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:26Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": null,
"gates": {},
"steps": {},
"title": "The Falling Star",
"face": null,
"frames": [],
"contact": "episodes/ep02/review/contact_ac23326a.png",
"face_src": "",
"iters": 4
},
{
"codex_id": "20260827135508",
"unit": "ep05",
"state": "queued",
"shown": "queued",
"step_id": null,
"step_name": "",
"progress": null,
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:27Z",
"gpu_seconds": 8461.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": null,
"gates": {},
"steps": {},
"title": "The Heat-Ray",
"face": "episodes/ep05/storyboard/shot_06.png",
"frames": [
"episodes/ep05/storyboard/shot_00.png",
"episodes/ep05/storyboard/shot_03.png",
"episodes/ep05/storyboard/shot_06.png",
"episodes/ep05/storyboard/shot_09.png",
"episodes/ep05/storyboard/shot_12.png",
"episodes/ep05/storyboard/shot_15.png",
"episodes/ep05/storyboard/shot_18.png",
"episodes/ep05/storyboard/shot_21.png"
],
"contact": null,
"face_src": "storyboard panel",
"iters": 4
},
{
"codex_id": "20260822113400",
"unit": "ep01",
"state": "blocked",
"shown": "blocked",
"step_id": null,
"step_name": "",
"progress": null,
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:23Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": null,
"gates": {},
"steps": {},
"title": "A Study in Scarlet",
"face": "episodes/ep01/boards/plates/plate_corridor.png",
"frames": [
"episodes/ep01/boards/plates/plate_bench.png",
"episodes/ep01/boards/plates/plate_cab.png",
"episodes/ep01/boards/plates/plate_corridor.png",
"episodes/ep01/boards/plates/plate_criterion.png",
"episodes/ep01/boards/plates/plate_gateway.png",
"episodes/ep01/boards/plates/plate_lab.png",
"episodes/ep01/boards/plates/plate_street.png"
],
"contact": null,
"face_src": "board plate",
"iters": 11
},
{
"codex_id": "20260822113400",
"unit": "ep02",
"state": "blocked",
"shown": "blocked",
"step_id": null,
"step_name": "",
"progress": null,
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:23Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": null,
"gates": {},
"steps": {},
"title": "The Science of Deduction",
"face": "episodes/ep02/boards/panels/Q03_0E.before.png",
"frames": [
"episodes/ep02/boards/panels/Q00_0E.before.png",
"episodes/ep02/boards/panels/Q02_0E.before.png",
"episodes/ep02/boards/panels/Q03_0E.before.png",
"episodes/ep02/boards/panels/Q04_1E.before.png",
"episodes/ep02/boards/panels/Q05_0E.before.png",
"episodes/ep02/boards/panels/Q22_0.before.png",
"episodes/ep02/boards/panels/panel_Q00_0E.png",
"episodes/ep02/boards/panels/panel_Q02_0E.png"
],
"contact": null,
"face_src": "board plate",
"iters": 3
},
{
"codex_id": "20260822113400",
"unit": "ep10",
"state": "blocked",
"shown": "blocked",
"step_id": null,
"step_name": "",
"progress": null,
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:24Z",
"gpu_seconds": 17932.6,
"cost_usd": 0.0,
"elapsed": "",
"started_at": null,
"gates": {},
"steps": {},
"title": "John Ferrier Talks with the Prophet",
"face": "episodes/ep10/boards/panels/Q20_0.before.png",
"frames": [
"episodes/ep10/boards/panels/Q13_0.before.png",
"episodes/ep10/boards/panels/Q16_0.before.png",
"episodes/ep10/boards/panels/Q20_0.before.png",
"episodes/ep10/boards/panels/Q25_0.before.png",
"episodes/ep10/boards/panels/panel_Q13_0.png",
"episodes/ep10/boards/panels/panel_Q16_0.png",
"episodes/ep10/boards/panels/panel_Q20_0.png",
"episodes/ep10/boards/panels/panel_Q25_0.png"
],
"contact": "episodes/ep10/review/contact_514491f8.png",
"face_src": "board plate",
"iters": 4
},
{
"codex_id": "20260822113400",
"unit": "ep11",
"state": "blocked",
"shown": "blocked",
"step_id": null,
"step_name": "",
"progress": null,
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:24Z",
"gpu_seconds": 18548.1,
"cost_usd": 0.0,
"elapsed": "",
"started_at": null,
"gates": {},
"steps": {},
"title": "A Flight for Life",
"face": "episodes/ep11/boards/panels/Q13_0.before.png",
"frames": [
"episodes/ep11/boards/panels/Q00_0.before.png",
"episodes/ep11/boards/panels/Q07_0.before.png",
"episodes/ep11/boards/panels/Q13_0.before.png",
"episodes/ep11/boards/panels/Q26_0.before.png",
"episodes/ep11/boards/panels/panel_Q00_0.png",
"episodes/ep11/boards/panels/panel_Q07_0.png",
"episodes/ep11/boards/panels/panel_Q13_0.png",
"episodes/ep11/boards/panels/panel_Q26_0.png"
],
"contact": "episodes/ep11/review/contact_395b8b9a.png",
"face_src": "board plate",
"iters": 1
},
{
"codex_id": "20260822113400",
"unit": "ep12",
"state": "blocked",
"shown": "blocked",
"step_id": null,
"step_name": "",
"progress": null,
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:24Z",
"gpu_seconds": 13070.6,
"cost_usd": 0.0,
"elapsed": "",
"started_at": null,
"gates": {},
"steps": {},
"title": "The Avenging Angels",
"face": "episodes/ep12/boards/plates/plate_drebber_house_bier.png",
"frames": [
"episodes/ep12/boards/plates/plate_camp_night.png",
"episodes/ep12/boards/plates/plate_camp_nook_dusk.png",
"episodes/ep12/boards/plates/plate_drebber_house_bier.png",
"episodes/ep12/boards/plates/plate_eagle_canyon_day.png",
"episodes/ep12/boards/plates/plate_mountain_defile_dawn.png"
],
"contact": "episodes/ep12/review/contact_3834c9c5.png",
"face_src": "board plate",
"iters": 1
},
{
"codex_id": "20260822113400",
"unit": "ep13",
"state": "blocked",
"shown": "blocked",
"step_id": null,
"step_name": "",
"progress": null,
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:24Z",
"gpu_seconds": 10918.7,
"cost_usd": 0.0,
"elapsed": "",
"started_at": null,
"gates": {},
"steps": {},
"title": "A Continuation of the Reminiscences of John Watson, M.D.",
"face": "episodes/ep13/boards/panels/panel_Q04_0.png",
"frames": [
"episodes/ep13/boards/panels/Q04_0.before.png",
"episodes/ep13/boards/panels/panel_Q04_0.png"
],
"contact": "episodes/ep13/review/contact_f69b1444.png",
"face_src": "board plate",
"iters": 1
},
{
"codex_id": "20260822113400",
"unit": "ep14",
"state": "blocked",
"shown": "blocked",
"step_id": null,
"step_name": "",
"progress": null,
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:24Z",
"gpu_seconds": 11223.7,
"cost_usd": 0.0,
"elapsed": "",
"started_at": null,
"gates": {},
"steps": {},
"title": "The Conclusion",
"face": "episodes/ep14/boards/plates/plate_garden_path_morning.png",
"frames": [
"episodes/ep14/boards/plates/plate_cab_rank_afternoon.png",
"episodes/ep14/boards/plates/plate_cell_dawn.png",
"episodes/ep14/boards/plates/plate_garden_path_morning.png",
"episodes/ep14/boards/plates/plate_lauriston_front_room.png",
"episodes/ep14/boards/plates/plate_sitting_room_evening.png"
],
"contact": "episodes/ep14/review/contact_08835219.png",
"face_src": "board plate",
"iters": 2
},
{
"codex_id": "20260822113400",
"unit": "ep03",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "4/12",
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:40Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-13T08:03:06Z",
"gates": {},
"steps": {},
"title": "The Lauriston Gardens Mystery",
"face": "episodes/ep03/boards/panels/Q12_0E.before.png",
"frames": [
"episodes/ep03/boards/panels/Q05_0E.before.png",
"episodes/ep03/boards/panels/Q10_0.before.png",
"episodes/ep03/boards/panels/Q12_0E.before.png",
"episodes/ep03/boards/panels/panel_Q06_0.png",
"episodes/ep03/boards/panels/panel_Q11_0.png",
"episodes/ep03/boards/panels/panel_Q23_0.png",
"episodes/ep03/boards/panels/seq_corner_wall_0_strict.png",
"episodes/ep03/boards/panels/seq_garden_path_0.png"
],
"contact": null,
"face_src": "board plate",
"iters": 6
},
{
"codex_id": "20260827135508",
"unit": "ep03",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "6/12",
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:42Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-18T20:40:51Z",
"gates": {},
"steps": {},
"title": "On Horsell Common",
"face": null,
"frames": [],
"contact": null,
"face_src": "",
"iters": 4
},
{
"codex_id": "20260822113400",
"unit": "ep04",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "4/12",
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:41Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-14T04:36:03Z",
"gates": {},
"steps": {},
"title": "What John Rance Had to Tell",
"face": "episodes/ep04/boards/plates/plate_lauriston_gate.png",
"frames": [
"episodes/ep04/boards/plates/plate_audley_court.png",
"episodes/ep04/boards/plates/plate_cab.png",
"episodes/ep04/boards/plates/plate_lauriston_gate.png",
"episodes/ep04/boards/plates/plate_rance_parlour.png"
],
"contact": null,
"face_src": "board plate",
"iters": 1
},
{
"codex_id": "20260827135508",
"unit": "ep04",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "6/12",
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:42Z",
"gpu_seconds": 1404.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-18T20:40:51Z",
"gates": {},
"steps": {},
"title": "The Cylinder Opens",
"face": null,
"frames": [],
"contact": null,
"face_src": "",
"iters": 4
},
{
"codex_id": "20260822113400",
"unit": "ep05",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "4/12",
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:41Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-14T20:55:19Z",
"gates": {},
"steps": {},
"title": "Our Advertisement Brings a Visitor",
"face": "episodes/ep05/boards/panels/Q20_0.before.png",
"frames": [
"episodes/ep05/boards/panels/Q13_0.before.png",
"episodes/ep05/boards/panels/Q13_0E.before.png",
"episodes/ep05/boards/panels/Q20_0.before.png",
"episodes/ep05/boards/panels/Q21_0.before.png",
"episodes/ep05/boards/panels/Q22_0.before.png",
"episodes/ep05/boards/panels/panel_Q13_0.png",
"episodes/ep05/boards/panels/panel_Q13_0E.png",
"episodes/ep05/boards/panels/panel_Q20_0.png"
],
"contact": null,
"face_src": "board plate",
"iters": 1
},
{
"codex_id": "20260822113400",
"unit": "ep06",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "4/12",
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:41Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-15T02:33:03Z",
"gates": {},
"steps": {},
"title": "Tobias Gregson Shows What He Can Do",
"face": "episodes/ep06/boards/plates/plate_breakfast_morning.png",
"frames": [
"episodes/ep06/boards/plates/plate_armchair_gregson.png",
"episodes/ep06/boards/plates/plate_boarding_parlour.png",
"episodes/ep06/boards/plates/plate_breakfast_morning.png",
"episodes/ep06/boards/plates/plate_carpet_irregulars.png",
"episodes/ep06/boards/plates/plate_landing_door.png",
"episodes/ep06/boards/plates/plate_window_street.png"
],
"contact": null,
"face_src": "board plate",
"iters": 1
},
{
"codex_id": "20260827135508",
"unit": "ep06",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "5/12",
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:42Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-18T20:40:51Z",
"gates": {},
"steps": {},
"title": "The Heat-Ray in the Chobham Road",
"face": "episodes/ep06/storyboard/shot_06.png",
"frames": [
"episodes/ep06/storyboard/shot_00.png",
"episodes/ep06/storyboard/shot_03.png",
"episodes/ep06/storyboard/shot_06.png",
"episodes/ep06/storyboard/shot_09.png",
"episodes/ep06/storyboard/shot_12.png",
"episodes/ep06/storyboard/shot_15.png",
"episodes/ep06/storyboard/shot_18.png",
"episodes/ep06/storyboard/shot_21.png"
],
"contact": null,
"face_src": "storyboard panel",
"iters": 3
},
{
"codex_id": "20260822113400",
"unit": "ep07",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "4/12",
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:41Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-15T13:21:19Z",
"gates": {},
"steps": {},
"title": "Light in the Darkness",
"face": "episodes/ep07/boards/plates/plate_hearth_dog.png",
"frames": [
"episodes/ep07/boards/plates/plate_halliday_corridor.png",
"episodes/ep07/boards/plates/plate_hearth_council.png",
"episodes/ep07/boards/plates/plate_hearth_dog.png",
"episodes/ep07/boards/plates/plate_landing_arrest.png",
"episodes/ep07/boards/plates/plate_mews_lane.png",
"episodes/ep07/boards/plates/plate_stangerson_room.png"
],
"contact": null,
"face_src": "board plate",
"iters": 2
},
{
"codex_id": "20260827135508",
"unit": "ep07",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "5/12",
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:42Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-18T20:40:51Z",
"gates": {},
"steps": {},
"title": "How I Reached Home",
"face": "episodes/ep07/storyboard/shot_06.png",
"frames": [
"episodes/ep07/storyboard/shot_00.png",
"episodes/ep07/storyboard/shot_03.png",
"episodes/ep07/storyboard/shot_06.png",
"episodes/ep07/storyboard/shot_09.png",
"episodes/ep07/storyboard/shot_12.png",
"episodes/ep07/storyboard/shot_15.png",
"episodes/ep07/storyboard/shot_18.png",
"episodes/ep07/storyboard/shot_21.png"
],
"contact": null,
"face_src": "storyboard panel",
"iters": 2
},
{
"codex_id": "20260822113400",
"unit": "ep08",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "4/12",
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:41Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-16T05:47:51Z",
"gates": {},
"steps": {},
"title": "On the Great Alkali Plain",
"face": "episodes/ep08/boards/plates/plate_caravan_far.png",
"frames": [
"episodes/ep08/boards/plates/plate_bluff_base.png",
"episodes/ep08/boards/plates/plate_caravan_column.png",
"episodes/ep08/boards/plates/plate_caravan_far.png",
"episodes/ep08/boards/plates/plate_crag_top.png",
"episodes/ep08/boards/plates/plate_plain_vista.png",
"episodes/ep08/boards/plates/plate_young_waggon.png"
],
"contact": null,
"face_src": "board plate",
"iters": 4
},
{
"codex_id": "20260827135508",
"unit": "ep08",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "5/12",
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:42Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-18T20:40:51Z",
"gates": {},
"steps": {},
"title": "Friday Night",
"face": "episodes/ep08/storyboard/shot_04.png",
"frames": [
"episodes/ep08/storyboard/shot_00.png",
"episodes/ep08/storyboard/shot_02.png",
"episodes/ep08/storyboard/shot_04.png",
"episodes/ep08/storyboard/shot_06.png",
"episodes/ep08/storyboard/shot_08.png",
"episodes/ep08/storyboard/shot_10.png",
"episodes/ep08/storyboard/shot_12.png",
"episodes/ep08/storyboard/shot_14.png"
],
"contact": null,
"face_src": "storyboard panel",
"iters": 3
},
{
"codex_id": "20260822113400",
"unit": "ep09",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "3/12",
"attempts": 0,
"flags": 0,
"blocked_on": "refs/04",
"updated_at": "2026-09-26T09:52:41Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-16T13:27:40Z",
"gates": {},
"steps": {},
"title": "The Flower of Utah",
"face": "episodes/ep09/boards/plates/plate_ferrier_land.png",
"frames": [
"episodes/ep09/boards/plates/plate_farm_gate.png",
"episodes/ep09/boards/plates/plate_farm_parlour.png",
"episodes/ep09/boards/plates/plate_ferrier_land.png",
"episodes/ep09/boards/plates/plate_high_road.png",
"episodes/ep09/boards/plates/plate_the_drove.png",
"episodes/ep09/boards/plates/plate_valley_rim.png"
],
"contact": null,
"face_src": "board plate",
"iters": 3
},
{
"codex_id": "20260827135508",
"unit": "ep09",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "5/12",
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:42Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-18T20:40:51Z",
"gates": {},
"steps": {},
"title": "The Fighting Begins",
"face": "episodes/ep09/storyboard/shot_04.png",
"frames": [
"episodes/ep09/storyboard/shot_00.png",
"episodes/ep09/storyboard/shot_02.png",
"episodes/ep09/storyboard/shot_04.png",
"episodes/ep09/storyboard/shot_06.png",
"episodes/ep09/storyboard/shot_08.png",
"episodes/ep09/storyboard/shot_10.png",
"episodes/ep09/storyboard/shot_12.png",
"episodes/ep09/storyboard/shot_14.png"
],
"contact": null,
"face_src": "storyboard panel",
"iters": 1
},
{
"codex_id": "20260827135508",
"unit": "ep10",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "5/12",
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:42Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-18T20:40:51Z",
"gates": {},
"steps": {},
"title": "In the Storm",
"face": "episodes/ep10/storyboard/shot_04.png",
"frames": [
"episodes/ep10/storyboard/shot_00.png",
"episodes/ep10/storyboard/shot_02.png",
"episodes/ep10/storyboard/shot_04.png",
"episodes/ep10/storyboard/shot_06.png",
"episodes/ep10/storyboard/shot_08.png",
"episodes/ep10/storyboard/shot_10.png",
"episodes/ep10/storyboard/shot_12.png",
"episodes/ep10/storyboard/shot_14.png"
],
"contact": null,
"face_src": "storyboard panel",
"iters": 1
},
{
"codex_id": "20260827135508",
"unit": "ep11",
"state": "done",
"shown": "done",
"step_id": "11",
"step_name": "qc",
"progress": "5/12",
"attempts": 0,
"flags": 0,
"blocked_on": null,
"updated_at": "2026-09-26T09:52:42Z",
"gpu_seconds": 0.0,
"cost_usd": 0.0,
"elapsed": "",
"started_at": "2026-09-18T20:40:51Z",
"gates": {},
"steps": {},
"title": "At the Window",
"face": "episodes/ep11/storyboard/shot_04.png",
"frames": [
"episodes/ep11/storyboard/shot_00.png",
"episodes/ep11/storyboard/shot_02.png",
"episodes/ep11/storyboard/shot_04.png",
"episodes/ep11/storyboard/shot_06.png",
"episodes/ep11/storyboard/shot_08.png",
"episodes/ep11/storyboard/shot_10.png",
"episodes/ep11/storyboard/shot_12.png",
"episodes/ep11/storyboard/shot_14.png"
],
"contact": null,
"face_src": "storyboard panel",
"iters": 2
}
]
},
"shelf": [
{
"id": "20260822113400",
"name": "A Study in Scarlet",
"author": "Arthur Conan Doyle",
"chapters": 14,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": true,
"refs": true,
"episodes": true
},
"orders": {
"analysis": [
"done",
0
],
"episode": [
"blocked",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 7,
"units": 14,
"flagged": 0
},
"published": 14,
"last": "2026-09-07T08:34:22.409036Z",
"gpu_h": 19.9,
"slug": "a-study-in-scarlet"
},
{
"id": "20260825235949",
"name": "Frankenstein; Or, The Modern Prometheus",
"author": "Mary Wollstonecraft Shelley",
"chapters": 28,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T03:07:47.710386Z",
"gpu_h": 0.0,
"slug": "frankenstein-or-the-modern-prometheus"
},
{
"id": "20260825235950",
"name": "Dracula",
"author": "Bram Stoker",
"chapters": 27,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T08:49:20.517366Z",
"gpu_h": 0.0,
"slug": "dracula"
},
{
"id": "20260825235951",
"name": "Pride and Prejudice",
"author": "Jane Austen",
"chapters": 61,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T08:48:35.460601Z",
"gpu_h": 0.0,
"slug": "pride-and-prejudice"
},
{
"id": "20260825235952",
"name": "The Adventures of Tom Sawyer",
"author": "Mark Twain",
"chapters": 35,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T02:29:07.615763Z",
"gpu_h": 0.0,
"slug": "the-adventures-of-tom-sawyer"
},
{
"id": "20260825235953",
"name": "Peter Pan",
"author": "J. M. Barrie",
"chapters": 17,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T22:24:42.921895Z",
"gpu_h": 0.0,
"slug": "peter-pan"
},
{
"id": "20260825235954",
"name": "Moby Dick; Or, The Whale",
"author": "Herman Melville",
"chapters": 135,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T11:18:16.847998Z",
"gpu_h": 0.0,
"slug": "moby-dick-or-the-whale"
},
{
"id": "20260825235955",
"name": "Metamorphosis",
"author": "Franz Kafka",
"chapters": 3,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T18:49:31.813190Z",
"gpu_h": 0.0,
"slug": "metamorphosis"
},
{
"id": "20260827135504",
"name": "The Strange Case of Dr. Jekyll and Mr. Hyde",
"author": "Robert Louis Stevenson",
"chapters": 10,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": true,
"refs": true,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-09-02T04:49:57.973324Z",
"gpu_h": 0.0,
"slug": "the-strange-case-of-dr-jekyll-and-mr-hyde"
},
{
"id": "20260827135505",
"name": "The Picture of Dorian Gray",
"author": "Oscar Wilde",
"chapters": 20,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T03:45:59.690210Z",
"gpu_h": 0.0,
"slug": "the-picture-of-dorian-gray"
},
{
"id": "20260827135506",
"name": "Heart of Darkness",
"author": "Joseph Conrad",
"chapters": 3,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T20:06:01.908526Z",
"gpu_h": 0.0,
"slug": "heart-of-darkness"
},
{
"id": "20260827135507",
"name": "The Time Machine",
"author": "H. G. Wells",
"chapters": 17,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T19:57:42.978612Z",
"gpu_h": 0.0,
"slug": "the-time-machine"
},
{
"id": "20260827135508",
"name": "The War of the Worlds",
"author": "H. G. Wells",
"chapters": 27,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": true,
"episodes": true
},
"orders": {
"analysis": [
"done",
0
],
"episode": [
"queued",
0
],
"refs": [
"done",
1
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 13,
"units": 17,
"flagged": 6
},
"published": 16,
"last": "2026-10-05T02:24:18.017272Z",
"gpu_h": 73.5,
"slug": "the-war-of-the-worlds"
},
{
"id": "20260827135509",
"name": "The Invisible Man",
"author": "H. G. Wells",
"chapters": 28,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T22:56:20.071591Z",
"gpu_h": 0.0,
"slug": "the-invisible-man"
},
{
"id": "20260827135553",
"name": "A Christmas Carol",
"author": "Charles Dickens",
"chapters": 5,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T19:27:54.213098Z",
"gpu_h": 0.0,
"slug": "a-christmas-carol"
},
{
"id": "20260827135554",
"name": "The Call of the Wild",
"author": "Jack London",
"chapters": 7,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T19:42:55.091858Z",
"gpu_h": 0.0,
"slug": "the-call-of-the-wild"
},
{
"id": "20260827135555",
"name": "Treasure Island",
"author": "Robert Louis Stevenson",
"chapters": 34,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T01:35:13.513678Z",
"gpu_h": 0.0,
"slug": "treasure-island"
},
{
"id": "20260827135556",
"name": "The Turn of the Screw",
"author": "Henry James",
"chapters": 25,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T21:56:01.567537Z",
"gpu_h": 0.0,
"slug": "the-turn-of-the-screw"
},
{
"id": "20260827135557",
"name": "Wuthering Heights",
"author": "Emily Brontë",
"chapters": 34,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T06:52:03.084454Z",
"gpu_h": 0.0,
"slug": "wuthering-heights"
},
{
"id": "20260827135558",
"name": "The Hound of the Baskervilles",
"author": "Arthur Conan Doyle",
"chapters": 15,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T23:18:28.200707Z",
"gpu_h": 0.0,
"slug": "the-hound-of-the-baskervilles"
},
{
"id": "20260827135559",
"name": "Alice's Adventures in Wonderland",
"author": "Lewis Carroll",
"chapters": 12,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T19:17:46.588750Z",
"gpu_h": 0.0,
"slug": "alice-s-adventures-in-wonderland"
},
{
"id": "20260827135600",
"name": "The Wonderful Wizard of Oz",
"author": "L. Frank Baum",
"chapters": 24,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T21:34:24.550046Z",
"gpu_h": 0.0,
"slug": "the-wonderful-wizard-of-oz"
},
{
"id": "20260827135601",
"name": "Robinson Crusoe",
"author": "Daniel Defoe",
"chapters": 20,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T07:47:46.728126Z",
"gpu_h": 0.0,
"slug": "robinson-crusoe"
},
{
"id": "20260827135602",
"name": "Around the World in Eighty Days",
"author": "Jules Verne",
"chapters": 37,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T00:49:38.866441Z",
"gpu_h": 0.0,
"slug": "around-the-world-in-eighty-days"
},
{
"id": "20260827135603",
"name": "Twenty Thousand Leagues under the Sea",
"author": "Jules Verne",
"chapters": 46,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T05:48:24.152783Z",
"gpu_h": 0.0,
"slug": "twenty-thousand-leagues-under-the-sea"
},
{
"id": "20260827135604",
"name": "The Secret Garden",
"author": "Frances Hodgson Burnett",
"chapters": 27,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T04:29:07.315101Z",
"gpu_h": 0.0,
"slug": "the-secret-garden"
},
{
"id": "20260827135605",
"name": "Black Beauty",
"author": "Anna Sewell",
"chapters": 30,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T20:33:01.054564Z",
"gpu_h": 0.0,
"slug": "black-beauty"
},
{
"id": "20260827135606",
"name": "The Prince and the Pauper",
"author": "Mark Twain",
"chapters": 1,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T01:53:15.941018Z",
"gpu_h": 0.0,
"slug": "the-prince-and-the-pauper"
},
{
"id": "20260827135607",
"name": "Dubliners",
"author": "James Joyce",
"chapters": 15,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-31T00:50:18.507201Z",
"gpu_h": 0.0,
"slug": "dubliners"
},
{
"id": "20260827135608",
"name": "Beowulf",
"author": null,
"chapters": 43,
"disk": {
"analysis": true,
"screenplay": true,
"trailer": false,
"refs": false,
"episodes": false
},
"orders": {
"analysis": [
"done",
0
],
"refs": [
"queued",
0
],
"screenplay": [
"queued",
0
],
"trailer": [
"queued",
0
]
},
"eps": {
"made": 0,
"units": 0,
"flagged": 0
},
"published": 0,
"last": "2026-08-30T20:57:32.640208Z",
"gpu_h": 0.0,
"slug": "beowulf"
}
],
"wotw": {
"published": [
"ep01",
"ep02",
"ep03",
"ep04",
"ep05",
"ep06",
"ep07",
"ep08",
"ep09",
"ep10",
"ep11",
"ep12",
"ep13",
"ep14",
"ep15",
"ep16"
],
"cast": [
{
"name": "albin",
"sheet": "refs/characters/albin/sheet.png"
},
{
"name": "artilleryman",
"sheet": "refs/characters/artilleryman/sheet.png"
},
{
"name": "astronomer_royal",
"sheet": "refs/characters/astronomer_royal/sheet.png"
},
{
"name": "captain",
"sheet": "refs/characters/captain/sheet.png"
},
{
"name": "curate",
"sheet": "refs/characters/curate/sheet.png"
},
{
"name": "denning",
"sheet": "refs/characters/denning/sheet.png"
},
{
"name": "deputation",
"sheet": "refs/characters/deputation/sheet.png"
},
{
"name": "four",
"sheet": "refs/characters/four/sheet.png"
},
{
"name": "gregg",
"sheet": "refs/characters/gregg/sheet.png"
},
{
"name": "gunners",
"sheet": "refs/characters/gunners/sheet.png"
},
{
"name": "henderson",
"sheet": "refs/characters/henderson/sheet.png"
},
{
"name": "hussars",
"sheet": "refs/characters/hussars/sheet.png"
},
{
"name": "lavelle",
"sheet": "refs/characters/lavelle/sheet.png"
},
{
"name": "lord_garrick",
"sheet": "refs/characters/lord_garrick/sheet.png"
},
{
"name": "lord_hilton",
"sheet": "refs/characters/lord_hilton/sheet.png"
},
{
"name": "major_eden",
"sheet": "refs/characters/major_eden/sheet.png"
},
{
"name": "markham",
"sheet": "refs/characters/markham/sheet.png"
},
{
"name": "marshall",
"sheet": "refs/characters/marshall/sheet.png"
},
{
"name": "marshall_son",
"sheet": "refs/characters/marshall_son/sheet.png"
},
{
"name": "martians",
"sheet": "refs/characters/martians/sheet.png"
},
{
"name": "miss_elphinstone",
"sheet": "refs/characters/miss_elphinstone/sheet.png"
},
{
"name": "mrs_elphinstone",
"sheet": "refs/characters/mrs_elphinstone/sheet.png"
},
{
"name": "narrators_brother",
"sheet": "refs/characters/narrators_brother/sheet.png"
},
{
"name": "narrators_wife",
"sheet": "refs/characters/narrators_wife/sheet.png"
},
{
"name": "ogilvy",
"sheet": "refs/characters/ogilvy/sheet.png"
},
{
"name": "police",
"sheet": "refs/characters/police/sheet.png"
},
{
"name": "sappers",
"sheet": "refs/characters/sappers/sheet.png"
},
{
"name": "schiaparelli",
"sheet": "refs/characters/schiaparelli/sheet.png"
},
{
"name": "snippy",
"sheet": "refs/characters/snippy/sheet.png"
},
{
"name": "soldiers",
"sheet": "refs/characters/soldiers/sheet.png"
},
{
"name": "stent",
"sheet": "refs/characters/stent/sheet.png"
},
{
"name": "unnamed_cabmen",
"sheet": "refs/characters/unnamed_cabmen/sheet.png"
},
{
"name": "unnamed_curate_companion",
"sheet": "refs/characters/unnamed_curate_companion/sheet.png"
},
{
"name": "unnamed_first_person_narrator",
"sheet": "refs/characters/unnamed_first_person_narrator/sheet.png"
},
{
"name": "unnamed_gardener",
"sheet": "refs/characters/unnamed_gardener/sheet.png"
},
{
"name": "unnamed_hussar",
"sheet": "refs/characters/unnamed_hussar/sheet.png"
},
{
"name": "unnamed_landlord",
"sheet": "refs/characters/unnamed_landlord/sheet.png"
},
{
"name": "unnamed_milkman",
"sheet": "refs/characters/unnamed_milkman/sheet.png"
},
{
"name": "unnamed_mounted_policeman",
"sheet": "refs/characters/unnamed_mounted_policeman/sheet.png"
},
{
"name": "unnamed_neighbour",
"sheet": "refs/characters/unnamed_neighbour/sheet.png"
},
{
"name": "unnamed_neighbours_wife",
"sheet": "refs/characters/unnamed_neighbours_wife/sheet.png"
},
{
"name": "unnamed_newspaper_boy",
"sheet": "refs/characters/unnamed_newspaper_boy/sheet.png"
},
{
"name": "unnamed_potman",
"sheet": "refs/characters/unnamed_potman/sheet.png"
},
{
"name": "unnamed_servant",
"sheet": "refs/characters/unnamed_servant/sheet.png"
},
{
"name": "unnamed_shopman",
"sheet": "refs/characters/unnamed_shopman/sheet.png"
},
{
"name": "unnamed_sweetstuff_dealer",
"sheet": "refs/characters/unnamed_sweetstuff_dealer/sheet.png"
},
{
"name": "unnamed_waggoner",
"sheet": "refs/characters/unnamed_waggoner/sheet.png"
}
],
"planned": 27
},
"sis": {
"published": [
"ep01",
"ep02",
"ep03",
"ep04",
"ep05",
"ep06",
"ep07",
"ep08",
"ep09",
"ep10",
"ep11",
"ep12",
"ep13",
"ep14"
]
}
};
