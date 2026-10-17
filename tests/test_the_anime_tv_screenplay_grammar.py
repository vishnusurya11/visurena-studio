"""The anime-TV screenplay grammar (owner 2026-10-17; research 04_screenplay.md).

A 22-minute anime episode is cold open, A part, the act-out (the eyecatch
break), B part, button, preview.  At 150 s each part is one beat:

- a COLD OPEN: the first line 10 words at most, a sound at 0 s (the swipe is
  decided in 2-3 s; Jekyll ep01's hook was 16 words of scenery, no sound);
- an ACT-OUT at 35-55 % of the runtime: a hold of 1.2 s or more and the bed
  changing tone (ep01: the bed already turns at shots 6 and 8);
- narration never CAPTIONS the frame (CAPTION_WALL, now a wall);
- a silent REACTION after each exchange (the Kuleshov frame);
- the holds concentrated: three or more of 1.2 s (ep01: 11 of 18 holds were
  0.4-0.5 s crumbs);
- the INNER voice sits over its speaker's own face.

Every measure reads the voice ruler (`placed`), never the rate alone.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import screenplay_grammar as sg


def _shot(i, section="setup", faces=("lead",), beat=0.0, coda=0.0, sounds=(), setup="room"):
    return SimpleNamespace(index=i, section=section, faces=list(faces), beat_s=beat, coda_s=coda,
                           sounds=[SimpleNamespace(sound=s, at=a) for s, a in sounds], setup=setup,
                           frame="", motion="The camera holds a locked-off frame; he turns; he lifts")


def _line(i, shot, kind="narration", speaker="narrator", text="one two three four"):
    return SimpleNamespace(index=i, shot=shot, kind=kind, speaker=speaker, text=text)


def _ep(shots, lines=(), beds=(), **kw):
    return SimpleNamespace(shots=list(shots), lines=list(lines), beds=list(beds), omit=[], **kw)


def _placed(lengths):
    t, out = 0.0, []
    for i, sec in enumerate(lengths):
        out.append({"index": i, "t_start": t, "seconds": sec})
        t += sec
    return {"duration_s": t, "shots": out}


def test_a_cold_open_is_ten_words_and_a_sound_at_zero():
    ok = _ep([_shot(0, "hook", sounds=[("a scream", 0.0)])], [_line(0, 0, text="A man trampled a child, and walked on.")])
    assert sg.cold_open_faults(ok) == []
    long = _ep([_shot(0, "hook", sounds=[("a scream", 0.0)])],
               [_line(0, 0, text="A blind door on a bright Sunday street. Through it comes a man")])
    assert [f.split(":")[0] for f in sg.cold_open_faults(long)] == ["G-COLD line 0"]
    late = _ep([_shot(0, "hook", sounds=[("a scream", 1.0)])], [_line(0, 0)])
    assert [f.split(":")[0] for f in sg.cold_open_faults(late)] == ["G-COLD shot 0"]


def test_one_act_out_at_35_to_55_percent_holding_and_changing_the_bed():
    shots = [_shot(i) for i in range(10)]
    shots[4] = _shot(4, "act_out", beat=0.7, coda=0.6)
    shots[7] = _shot(7, "turn")
    beds = [{"from_shot": 0, "tone": "uneasy"}, {"from_shot": 5, "tone": "grave"}]
    assert sg.act_out_faults(_ep(shots, beds=beds), _placed([10] * 10)) == []


def test_an_act_out_missing_misplaced_unheld_or_under_one_bed_is_refused():
    shots = [_shot(i) for i in range(10)]
    shots[7] = _shot(7, "turn")
    assert [f.split(":")[0] for f in sg.act_out_faults(_ep(shots), _placed([10] * 10))] == ["G-ACT plan"]
    shots[8] = _shot(8, "act_out", beat=0.2)
    got = sg.act_out_faults(_ep(shots, beds=[{"from_shot": 0, "tone": "grave"}]), _placed([10] * 10))
    assert len(got) == 4          # past 55 %, a short hold, one bed tone, after the turn


def test_a_caption_line_over_the_wall_is_refused():
    shots = [_shot(0)]
    shots[0].frame, shots[0].motion = "The lawyer walks on along the pavement", "he walks on; his cane taps"
    ep = _ep(shots, [_line(0, 0, text="The lawyer walks on along the pavement.")])
    assert [f.split(":")[0] for f in sg.caption_faults(ep)] == ["G-CAPTION line 0"]


def test_each_exchange_is_followed_by_a_silent_face():
    shots = [_shot(0), _shot(1), _shot(2), _shot(3)]
    lines = [_line(0, 0, "dialogue", "a"), _line(1, 1, "dialogue", "b"), _line(2, 3)]
    assert sg.reaction_faults(_ep(shots, lines)) == []
    lines = [_line(0, 0, "dialogue", "a"), _line(1, 1, "dialogue", "b"), _line(2, 2)]
    assert [f.split(":")[0] for f in sg.reaction_faults(_ep(shots, lines))] == ["G-REACT shot 2"]


def test_an_inner_line_counts_as_the_silent_reaction():
    shots = [_shot(0), _shot(1), _shot(2)]
    lines = [_line(0, 0, "dialogue", "a"), _line(1, 1, "dialogue", "b"), _line(2, 2, "inner", "lead")]
    assert sg.reaction_faults(_ep(shots, lines)) == []


def test_one_speaker_is_not_an_exchange():
    shots = [_shot(0), _shot(1), _shot(2)]
    lines = [_line(0, 0, "dialogue", "a"), _line(1, 1, "dialogue", "a"), _line(2, 2)]
    assert sg.reaction_faults(_ep(shots, lines)) == []


def test_three_held_beats_of_a_second_and_a_fifth():
    held = [_shot(i, beat=1.2) for i in range(3)] + [_shot(3, beat=0.4)]
    assert sg.ma_faults(_ep(held)) == []
    thin = [_shot(i, beat=0.5, coda=0.4) for i in range(6)]
    assert [f.split(":")[0] for f in sg.ma_faults(_ep(thin))] == ["G-MA plan"]


def test_an_inner_line_sits_over_its_speakers_face():
    shots = [_shot(0, faces=("lead",)), _shot(1, faces=("other",))]
    lines = [_line(0, 0, "inner", "lead"), _line(1, 1, "inner", "lead")]
    assert [f.split(":")[0] for f in sg.inner_faults(_ep(shots, lines))] == ["G-INNER line 1"]
    assert sg.inner_advisories(_ep(shots, lines))


def test_a_tease_loops_to_the_hooks_place():
    setups = {"door": SimpleNamespace(location="door"), "desk": SimpleNamespace(location="study")}
    shots = [_shot(0, "hook", setup="door"), _shot(1, "button"), _shot(2, "tease", setup="desk", faces=())]
    ep = _ep(shots, setups=setups, tease="the lawyer at his desk")
    assert sg.tease_advisories(ep)
    shots[2].setup = "door"
    assert sg.tease_advisories(ep) == []


def test_the_screenplay_numbers_are_one_table():
    band = sg.band()
    assert band["cold_open_words"] == 10 and band["act_out_band"] == [0.35, 0.55]
    assert band["hold_s"] == 1.2 and band["min_holds"] == 3 and band["inner_max_words"] == 8


def test_the_witness_narrating_his_own_act_is_not_a_caption():
    """Calibration replay (2026-10-17): the wall's one fire on an owner-liked episode
    is WotW ep03 line 15, "I left the staring crowd behind me and slid down the hot
    sand to him" over the narrator sliding down -- the memoir's witness acting
    (`episode_spec.narrator_acts`), which the silent-narrator rule asks for."""
    shot = _shot(0)
    shot.frame, shot.motion = "The narrator slides down the hot sand past the staring crowd", "he slides; he lands"
    ep = _ep([shot], [_line(0, 0, text="I left the staring crowd behind me and slid down the hot sand.")])
    assert sg.caption_faults(ep) == []


def test_a_slanting_surface_is_not_a_dutch_angle():
    from studio import framing_grammar as fg
    seg = SimpleNamespace(frame="the mahogany surface runs at a slant across the glass", motion="", camera="",
                          at_rest="", end="", size="insert", faces=[])
    assert fg.unsupported_hit(seg) == ""
