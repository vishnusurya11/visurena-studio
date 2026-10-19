"""prompt_lint: the deterministic take-prompt lints P1-P18 (audit 2026-10-15,
docs/audit/2026-10-15_jekyll_ep01_ref_audit/02_prompts.md). Every "catches"
quote from the audit must fire; one clean phrase per rule must not. $0: strings
and tmp files only."""
import json
import os
import time

from studio import prompt_lint as pl

FACES = ["gabriel_john_utterson", "richard_enfield"]
FACTS = {
    "faces": FACES,
    "aliases": {"gabriel_john_utterson": ["the lawyer"], "edward_hyde": ["the little man"]},
    "cast_names": {"gabriel_john_utterson": ["Mr. Utterson", "Utterson"],
                   "richard_enfield": ["Mr. Enfield", "Enfield"],
                   "henry_jekyll": ["Dr. Jekyll", "Jekyll", "Henry Jekyll"],
                   "edward_hyde": ["Mr. Hyde", "Hyde"]},
    "own": {1: "gabriel_john_utterson", 2: "richard_enfield"},
    "photoreal": False, "extras": 0, "crowd": "", "frames": 192,
}
DEF1 = ("<Subject 1> is Mr. Utterson in <Picture 1>: Lank grey hair falling to his collar; "
        "black bowler hat. A lean, long, bony, dry man of about forty, with a long face. "
        "<Picture 1> defines this man alone; each shot keeps the framing its own words describe.")
DEF2 = ("<Subject 2> is Mr. Enfield in <Picture 2>: Receding brown hair; clean-shaven; light-brown top hat. "
        "<Picture 2> defines this man alone; each shot keeps the framing its own words describe.")
CLEAN_SHOT = ("[Shot 1] From 00:00 to 00:08. The shot opens on a wide of the blistered door as <Subject 1> "
              "and <Subject 2> stop short on the near pavement. The camera is on the near pavement at the "
              "LEFT corner, at shoulder height; the grey daylight comes from the LEFT. At the first frame "
              "the focus of the picture is the door at the CENTRE. The camera tilts up from the pavement "
              "to the plaster forehead, from 00:00 to 00:03. At 00:03 <Subject 2> points his cane at the door. "
              "By 00:08 the camera is tilting up through the last frame, with the scorched door now in frame.")


def prompt(shot: str = CLEAN_SHOT, defs: str = f"{DEF1}\n{DEF2}") -> str:
    return (f"subject_definitions:\n{defs}\n\nsummary:\nOne take.\n\nretention_analysis:\n"
            f"<Subject 1> (the man in [Shot 1]): kept.\n\ndetailed_description:\n"
            f"Hand-drawn 2D gothic anime.\n{shot}\n\noverall_soundscape: Open air.\n")


def rules(faults: list[str]) -> set[str]:
    return {f.split()[0] for f in faults}


# ---- sections ----------------------------------------------------------------
def test_section_reads_one_block():
    assert pl.section(prompt(), "summary").strip() == "One take."
    assert "[Shot 1]" in pl.section(prompt(), "detailed_description")
    assert pl.section("no sections", "summary") == ""


def test_clean_prompt_is_clean():
    assert pl.take_faults(prompt(), FACTS) == []


# ---- P1 / P2 / P3 --------------------------------------------------------------
def test_p1_case_garble():
    assert pl.p1_case("At the first frame tHE FOCUS OF THE PICTURE IS the door")
    assert not pl.p1_case("<Subject 1> on IPv6 and the THE FOCUS line")


def test_p2_capital_preposition():
    assert pl.p2_camera_is("The camera is On the near pavement at the LEFT corner")
    assert pl.p2_camera_is("The camera is Over <Subject 2>'s shoulder")
    assert not pl.p2_camera_is("The camera is on the near pavement")


def test_p3_cure_lead_as_noun_phrase():
    assert pl.p3_cure_lead("The shot opens on only the named people stand in the picture and everything else is the place.")
    assert pl.p3_cure_lead("The shot opens on the frame is cut as a medium shot.")
    assert pl.p3_cure_lead("The shot opens on each person in the picture appears exactly once")
    assert pl.p3_cure_lead("The shot opens on the named subject stands large at the CENTRE")
    assert not pl.p3_cure_lead("The shot opens on a wide of the house")


def test_p3_plan_frame_starting_with_a_cure():
    assert pl.cure_led("Only the named people stand in the picture and everything else is the place. Medium of him")
    assert not pl.cure_led("Medium close of Mr. Enfield on the near pavement")


# ---- P4 / P5 -------------------------------------------------------------------
def test_p4_uncited_subject_and_free_alias():
    shot = CLEAN_SHOT.replace("<Subject 1>", "the lawyer")
    got = pl.p4_binding(prompt(shot), FACTS)
    assert any("<Subject 1>" in f for f in got)
    assert any("the lawyer" in f for f in got)
    assert pl.p4_binding(prompt(), FACTS) == []


def test_p4_unstaged_alias_is_not_p4():
    shot = CLEAN_SHOT + " the little man watches."
    assert pl.p4_binding(prompt(shot), FACTS) == []


def test_p5_second_description():
    d = "Medium close of <Subject 1> (light-brown top hat, fashionable dark frock coat) on the pavement"
    assert pl.p5_parenthetical(d, FACTS)
    d2 = "a wide as the lawyer (long, gaunt, rugged, unsmiling face, black bowler hat) stops"
    assert pl.p5_parenthetical(d2, FACTS)
    assert not pl.p5_parenthetical("<Subject 1> (S1), on screen, a lean, long man of forty", FACTS)


# ---- P6 ------------------------------------------------------------------------
def test_definitions_parsed():
    got = pl.definitions(prompt())
    assert set(got) == {1, 2}
    assert got[1][0] == "Mr. Utterson" and got[1][1].startswith("Lank grey hair")


def test_p6_debris_sentence():
    assert pl.p6_definition(1, "Mr. Utterson", "A lean dry man, narrow-chested, with a long. Wearing: a dark suit.", FACTS)
    assert pl.p6_definition(1, "Mr. Utterson", "Lank. Grey hair falling to his collar.", FACTS)
    assert not pl.p6_definition(1, "Mr. Utterson", "A lean dry man with a long face. Wearing: a dark suit.", FACTS)


def test_p6_other_cast_name_and_meta():
    hyde = ("A small or little man, repeatedly described as shorter and lighter than Henry Jekyll. "
            "He is associated with respectable clothing and access to Jekyll's house, a furnished Soho residence.")
    got = pl.p6_definition(1, "Mr. Hyde", hyde, {**FACTS, "own": {1: "edward_hyde"}})
    assert any("Jekyll" in f for f in got) and any("associated with" in f for f in got)
    assert not pl.p6_definition(1, "Mr. Hyde", "A small pale man named Hyde in a black coat.", {**FACTS, "own": {1: "edward_hyde"}})


def test_p6_younger_than_jekyll():
    got = pl.p6_definition(1, "Mr. Utterson", "A lean man of about forty, younger than Jekyll, narrow-chested.", FACTS)
    assert got and "Jekyll" in got[0]


def test_cast_names_list_form_excludes_own_header():
    facts = {**FACTS, "cast_names": ["Utterson", "Jekyll"], "own": {}}
    assert not pl.p6_definition(1, "Mr. Utterson", "A lean man whom Utterson's clerks fear.", facts)
    assert pl.p6_definition(1, "Mr. Utterson", "A lean man, younger than Jekyll, quite dry.", facts)


# ---- P7 / P8 / P9 / P10 ------------------------------------------------------------
def test_p7_stub_speaker():
    assert pl.p7_speaker("<Subject 1> (S1), on screen, lank, with a clipped English voice")
    assert pl.p7_speaker("<Subject 1> (S1), on screen, receding brown hair; clean-shaven; light-brown top hat. "
                         "A compact, with a clipped English voice at an even pace, says")
    assert not pl.p7_speaker("<Subject 1> (S1), on screen, a lean, long, bony man of about forty, with a dry voice")


def test_p8_line_ended_yet_speaking():
    assert pl.p8_line_ends("At 00:05, as the line ends, his free hand opens toward the lawyer as he speaks, and the opening continues.")
    assert not pl.p8_line_ends("At 00:05, as the line ends, his free hand opens toward the door.")
    assert not pl.p8_line_ends("At 00:04 his lean hand opens toward <Subject 2> as he speaks.")


def test_p9_noun_continues_without_verb():
    assert pl.p9_continues("At 00:04 his lean hands swing at his sides, and the lean continues to the last frame.")
    assert pl.p9_continues("his free hand opens toward the lawyer as he speaks, and the opening continues to the last frame")
    assert not pl.p9_continues("as the lawyer leans in close and presses him, and the lean continues to the last frame")


def test_p9_end_noun_garble():
    assert pl.p9_end_noun("By 00:08 the camera is rising through the last frame, with the now in frame.")
    assert pl.p9_end_noun("with the knuckly hand turns the key now in frame, and the action continues")
    assert pl.p9_end_noun("with the two men face now in frame, and the action continues")
    assert not pl.p9_end_noun("with the little man's sneering face now in frame")
    assert not pl.p9_end_noun("with the soot-black houses now in frame")


def test_p10_closed_mouth_bound_to_the_wrong_person():
    t8 = "<Subject 2>'s mouth is closed from 00:00 to 00:06 while his lean hand opens toward <Subject 2> as he speaks."
    assert pl.p10_mouth(t8)
    ok = "<Subject 2>'s mouth is closed from 00:00 to 00:06 while he thrusts his cane out at the door."
    assert not pl.p10_mouth(ok)


# ---- P11 -------------------------------------------------------------------------
def test_p11_dangling_camera_aim():
    assert pl.p11_dangling("The camera tracks beside the gold coins to the folded as the knuckly hand pushes")
    assert pl.p11_dangling("The camera tracks beside the lawyer across to the door's as <Subject 1> lifts his cane")
    assert pl.p11_dangling("tracks beside the gold coins to the folded; the two men walk")
    assert pl.p11_dangling("The camera pushes in toward the;")
    assert not pl.p11_dangling("The camera tracks beside the gold coins to the door as the hand pushes")
    assert not pl.p11_dangling("The camera pushes in toward the folded cheque; the hand opens.")


def test_p11_take_reads_camera_sentences_only():
    shot = CLEAN_SHOT + " The camera tracks beside the gold coins to the folded as the hand pushes."
    assert "P11" in rules(pl.take_faults(prompt(shot), FACTS))


# ---- P13 -------------------------------------------------------------------------
def test_p13_unstaged_person_noun():
    assert pl.p13_people("a ragged tramp strikes a match on the panels", FACTS)
    assert pl.p13_people("the lawyer watches as he speaks", {**FACTS, "faces": ["richard_enfield"]})
    assert not pl.p13_people("a ragged tramp strikes a match", {**FACTS, "extras": 1})
    assert not pl.p13_people("a ragged tramp strikes a match", {**FACTS, "crowd": "a few tramps"})


def test_p13_ignores_past_relative_clause_staged_alias_and_possessive():
    assert not pl.p13_people("a wide of the house of the man who trampled a child: the block", FACTS)
    assert not pl.p13_people("the lawyer turns his long face", FACTS)
    hyde = {**FACTS, "faces": ["edward_hyde"]}
    assert not pl.p13_people("the little man walks on, the little man's pale face", hyde)
    assert not pl.p13_people("as he gives the man's name", FACTS)


# ---- P14 / P15 -------------------------------------------------------------------
def test_p14_lettering_bait():
    assert pl.p14_lettering("holding out gold coins and a folded cheque to the hand", "")
    assert not pl.p14_lettering("holding out gold coins and a folded cheque", "Every surface is plain, wordless paint.")
    assert not pl.p14_lettering("holding out gold coins", "")


def test_p15_lens_in_a_drawn_book():
    assert pl.p15_lens("On the near pavement, a 35mm lens; the light", photoreal=False)
    assert not pl.p15_lens("On the near pavement, a 35mm lens", photoreal=True)
    assert not pl.p15_lens("On the near pavement at head height", photoreal=False)


# ---- P17 -------------------------------------------------------------------------
def test_p17_over_the_shoulder_side():
    bad = ("The camera is over the lawyer's shoulder, a yard behind his LEFT side. "
           "The lawyer's dark shoulder and bowler fill the LEFT edge.")
    good = ("The camera is over the lawyer's shoulder, a yard behind his RIGHT side. "
            "The lawyer's dark shoulder and bowler fill the LEFT edge.")
    t3 = ("The camera is at the near kerb behind <Subject 1>'s LEFT shoulder. "
          "Mr. Enfield's dark shoulder and top hat fill the BOTTOM LEFT corner.")
    assert pl.p17_shoulder(bad) and pl.p17_shoulder(t3)
    assert not pl.p17_shoulder(good)


def test_p17_pan_that_is_a_tilt():
    t16 = ("At the first frame the focus of the picture is the lawyer's bony hands clasped at the CENTRE. "
           "The soot-black houses close the far end of the street small at the TOP third. "
           "The camera pans from the lawyer's clasped hands across to the soot-black houses at the far end.")
    assert pl.p17_pan(t16)
    assert pl.p17_pan("The camera pans from the steps at the BOTTOM third up to the roofline at the TOP third.")
    side = ("the little man at the LEFT third. The cab waits at the RIGHT third. "
            "The camera pans from the little man across to the cab.")
    assert not pl.p17_pan(side)


# ---- P18 density -----------------------------------------------------------------
def test_shot_blocks_and_window():
    blocks = pl.shot_blocks(pl.section(prompt(), "detailed_description"))
    assert len(blocks) == 1 and blocks[0][0] == 8.0


def test_p18_density():
    t12 = ("[Shot 1] From 00:00 to 00:01. The shot opens on a medium shot of the two men. "
           "The camera pulls back from the two men across the whole shot as <Subject 2> lifts his cane, from 00:00 to 00:01. "
           "Then the lawyer nods and falls into step beside him.")
    assert pl.p18_density(t12, frames=39)
    assert not pl.p18_density(CLEAN_SHOT, frames=192)


def test_action_count():
    assert pl.actions("The camera pans left. At 00:02 he nods, then he turns. Then he walks.") == 4
    assert pl.actions("The shot opens on a wide of the door.") == 0


# ---- whole take ------------------------------------------------------------------
def test_take_faults_flags_the_audit_take():
    shot = ("[Shot 1] From 00:00 to 00:06. The shot opens on only the named people stand in the picture and "
            "everything else is the place. Medium close of <Subject 2> (light-brown top hat) on the pavement. "
            "The camera is On the near pavement, a 50mm lens. At the first frame tHE FOCUS OF THE PICTURE IS "
            "<Subject 2>'s face at the CENTRE. At 00:05, as the line ends, his free hand opens toward the lawyer "
            "as he speaks, and the opening continues to the last frame.")
    got = rules(pl.take_faults(prompt(shot), {**FACTS, "faces": ["richard_enfield"], "own": {1: "richard_enfield"}}))
    assert {"P1", "P2", "P3", "P5", "P8", "P9", "P15"} <= got   # "toward the lawyer" aims off frame (iter5)


def test_fault_format():
    got = pl.take_faults(prompt(CLEAN_SHOT.replace("The camera is on", "The camera is On")), FACTS)
    assert got and got[0].startswith("P2 ") and ": " in got[0]


# ---- P12 plan ----------------------------------------------------------------------
ROWS = {
    "child_of_hyde_incident": "fair hair in two plaits; small soft grey woollen bonnet; dark-red long-sleeved blouse; plain grey pinafore dress and black boots",
    "gabriel_john_utterson": "lank grey hair; long, gaunt, rugged, unsmiling face; black bowler hat",
}


def plan_of(**shot) -> dict:
    base = {"frame": "", "motion": "", "at_rest": "", "end": "", "camera": "", "setup": "s",
            "faces": ["child_of_hyde_incident"], "extras": 0, "crowd": ""}
    return {"setups": {"s": {"crowd": ""}}, "shots": [{**base, **shot}]}


def test_p12_stale_fragment():
    frame = "Wide as the girl (fair hair in two plaits, small knitted woollen bonnet, plain grey pinafore dress) runs"
    got = pl.plan_faults(plan_of(frame=frame), ROWS)
    assert any(f.startswith("P12") and "small knitted woollen bonnet" in f for f in got)


def test_p12_current_fragment_clean():
    frame = "Wide as the girl (fair hair in two plaits, small soft grey woollen bonnet) runs"
    assert pl.plan_faults(plan_of(frame=frame), ROWS) == []


def test_plan_p11_and_p13():
    got = rules(pl.plan_faults(plan_of(
        frame="Only the named people stand in the picture and everything else is the place. Wide of the street "
              "as a ragged tramp strikes a match",
        motion="The camera tracks beside the gold coins to the folded; the hand pushes"), ROWS))
    assert {"P11", "P13"} <= got and "P3" not in got


def test_plan_p13_covered_by_extras_or_setup_crowd():
    shot = {"frame": "Wide as a ragged tramp strikes a match", "extras": 1}
    assert pl.plan_faults(plan_of(**shot), ROWS) == []
    plan = plan_of(frame="Wide as a ragged tramp strikes a match", extras=1)
    plan["setups"]["s"]["crowd"] = "two tramps"
    assert pl.plan_faults(plan, ROWS) == []
    # the setup's crowd covers a shot only when that shot declares extras (ep01 retro, P03)
    plan = plan_of(frame="Wide as a ragged tramp strikes a match")
    plan["setups"]["s"]["crowd"] = "two tramps"
    assert "P13" in rules(pl.plan_faults(plan, ROWS))


def test_plan_p17_over_the_shoulder():
    got = pl.plan_faults(plan_of(camera="Over his shoulder, a yard behind his LEFT side.",
                                 at_rest="His dark shoulder fills the LEFT edge."), ROWS)
    assert "P17" in rules(got)


# ---- P18 files ---------------------------------------------------------------------
def write_take(d, idx: int, graph_prompt: str, graph_age: float) -> None:
    mp4, graph = d / f"T{idx:02d}.mp4", d / f"T{idx:02d}.graph.json"
    mp4.write_bytes(b"x")
    graph.write_text(json.dumps({"8": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"prompt": graph_prompt}}}))
    now = time.time()
    os.utime(mp4, (now, now))
    os.utime(graph, (now - graph_age, now - graph_age))


def test_file_faults(tmp_path):
    (tmp_path / "prompts.json").write_text(json.dumps([{"index": 0, "prompt": "A"}, {"index": 1, "prompt": "B"}]))
    write_take(tmp_path, 0, "A", 0)
    write_take(tmp_path, 1, "old", pl.RENDER_CEILING + 3600)
    got = pl.file_faults(tmp_path)
    assert len(got) == 2 and all(f.startswith("P18") and "T01" in f for f in got)


def test_graph_prompt_reads_the_render_node():
    g = {"3": {"class_type": "LoadImage", "inputs": {"image": "x"}},
         "8": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"prompt": "P"}}}
    assert pl.graph_prompt(g) == "P"
    assert pl.graph_prompt({}) is None


# ---- episode ----------------------------------------------------------------------
def make_book(root):
    ep = root / "episodes" / "ep01"
    (ep / "takes" / "r2v").mkdir(parents=True)
    (root / "refs").mkdir()
    (root / "refs" / "refs.json").write_text(json.dumps({"refs": [
        {"kind": "character", "entity_id": "gabriel_john_utterson", "display": "Mr. Utterson",
         "physical": "Lank grey hair; long, gaunt, rugged, unsmiling face; black bowler hat",
         "wardrobe": {"indoor": "long black overcoat"}},
        {"kind": "location", "entity_id": "door", "display": "the door", "physical": "a door"}]}))
    (root / "refs" / "look.json").write_text(json.dumps({"look": "anime_gothic"}))
    shot = {"index": 0, "setup": "s", "faces": ["gabriel_john_utterson"], "extras": 0, "crowd": "",
            "frame": "Wide as the lawyer (black bowler hat) stops", "motion": "", "at_rest": "", "end": "", "camera": ""}
    (ep / "plan.json").write_text(json.dumps({"setups": {"s": {"crowd": ""}}, "shots": [shot]}))
    defs = ("<Subject 1> is Mr. Utterson in <Picture 1>: Lank grey hair; black bowler hat. "
            "<Picture 1> defines this man alone; each shot keeps the framing its own words describe.")
    text = prompt(CLEAN_SHOT.replace(" and <Subject 2>", "").replace("<Subject 2>", "<Subject 1>"), defs)
    (ep / "takes" / "r2v" / "prompts.json").write_text(json.dumps([
        {"index": 0, "shots": [0], "faces": ["gabriel_john_utterson"], "frames": 192, "prompt": text}]))
    return ep


def test_facts_for(tmp_path):
    make_book(tmp_path)
    rec = json.loads((tmp_path / "episodes/ep01/takes/r2v/prompts.json").read_text())[0]
    plan = json.loads((tmp_path / "episodes/ep01/plan.json").read_text())
    facts = pl.facts_for(tmp_path, rec, plan)
    assert facts["faces"] == ["gabriel_john_utterson"] and facts["own"] == {1: "gabriel_john_utterson"}
    assert facts["aliases"] == {"gabriel_john_utterson": ["the lawyer"]}
    assert "Utterson" in facts["cast_names"]["gabriel_john_utterson"]
    assert facts["photoreal"] is False and facts["extras"] == 0


def test_lint_episode_clean_and_cli(tmp_path, capsys):
    make_book(tmp_path)
    got = pl.lint_episode(tmp_path, 1)
    assert got == {"takes": {0: []}, "plan": [], "files": []}
    from scripts.episode import prompt_lint as cli
    assert cli.main([str(tmp_path), "1"]) == 0
    assert capsys.readouterr().out.strip().splitlines()[-1] == "PROMPT LINT: clean"


def test_cli_counts_faults(tmp_path, capsys):
    ep = make_book(tmp_path)
    path = ep / "takes" / "r2v" / "prompts.json"
    recs = json.loads(path.read_text())
    recs[0]["prompt"] = recs[0]["prompt"].replace("The camera is on", "The camera is On")
    path.write_text(json.dumps(recs))
    from scripts.episode import prompt_lint as cli
    assert cli.main([str(tmp_path), "1"]) == 1
    out = capsys.readouterr().out.strip().splitlines()
    assert out[-1] == "PROMPT LINT: 1 faults" and out[0].startswith("T00 P2")


# ---- calibrated on the real ep01 prompts (2026-10-15) ---------------------------------
def test_p13_ignores_spoken_words():
    assert not pl.p13_people("says: <d>[English] It was a man of the name of Hyde.</d> His mouth", FACTS)


def test_p11_take_reads_only_sentences_led_by_the_camera():
    shot = CLEAN_SHOT + " By 00:10 the camera is rising, the little man past her; <Subject 1> runs."
    assert "P11" not in rules(pl.take_faults(prompt(shot), FACTS))


def test_p17_pan_position_is_read_in_the_nouns_own_clause():
    t16 = ("The camera is behind the lawyer at the height of his hands, a yard back; the daylight comes from the LEFT. "
           "At the first frame the focus is the lawyer's bony hands clasped at the small of his back at the CENTRE. "
           "The flagstones run along the BOTTOM third; the soot-black houses close the street at the TOP third. "
           "The camera pans from the lawyer's clasped hands across to the soot-black houses at the far end.")
    assert pl.p17_pan(t16)


def test_p18_graph_written_before_its_render_is_not_stale(tmp_path):
    (tmp_path / "prompts.json").write_text(json.dumps([{"index": 0, "prompt": "A"}]))
    write_take(tmp_path, 0, "A", 1800)
    assert pl.file_faults(tmp_path) == []
    write_take(tmp_path, 0, "A", pl.RENDER_CEILING + 60)
    assert pl.file_faults(tmp_path)


def test_face_to_face_is_a_phrase_not_a_verb():
    from studio import prompt_lint as pl
    assert pl.p9_end_noun("By 00:07 the camera is pushing, with the two men face to face now in frame.") == []


def test_a_plan_frame_led_by_a_panel_cure_is_the_drawers_and_not_a_plan_fault():
    """The panel ladder leads the SHARED frame with its cure for the drawer; the take
    builder drops it (episode_ref_official.without_cures); P3 judges the TAKE text."""
    from studio import prompt_lint as pl
    plan = {"shots": [{"index": 1, "frame": "Only the named people stand in the picture and everything "
                                             "else is the place. Medium close of Mr. Enfield", "faces": []}],
            "setups": {}}
    assert not [f for f in pl.plan_faults(plan, {}) if f.startswith("P3")]


def test_a_person_the_motion_aims_toward_is_off_frame_not_staged():
    from studio import prompt_lint as pl
    facts = {"faces": ["e"], "aliases": {"u": ["the lawyer"]}, "extras": 0, "crowd": ""}
    assert pl.p13_people("his free hand opens toward the lawyer as he speaks", facts) == []
