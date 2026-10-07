"""ep19 (2026-10-06): WotW Book Two, ch. II speaks no line -- its one quotation is
the narrator citing a writer -- yet G-STORY refused every draft for a 89.6 s
narration-only run against a fixed 75 s wall.  Three writer rounds could only
invent speech.  The wall follows the chapter, as the first-dialogue wall does:
an episode may run as long without dialogue as its chapter's longest quote-free
stretch, as a share of the runtime, and never shorter than the fixed wall.  A
dialogue line second on its shot (G-SYNC) is cured for free by opening the next
shot with it.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_cures
from studio import plan_gates as pg

TALKY = ['"Come," he said.', 'We went.', '"Now," she said.', 'We ran.', '"Stop!" I cried.']
SILENT = ['We crouched in the dark.' * 4, 'A quotation: "repulsive to a rabbit".', 'We watched.' * 80]


def test_a_talky_chapter_is_hardly_quiet():
    assert pg.quiet_share(TALKY) < 0.3


def test_a_chapter_without_speech_is_mostly_quiet():
    assert pg.quiet_share(SILENT) > 0.6
    assert pg.quiet_share([]) is None


def test_the_wall_never_drops_below_the_fixed_wall():
    assert pg.narration_wall(120.0, None) == pg.NARRATION_RUN_S
    assert pg.narration_wall(120.0, 0.1) == pg.NARRATION_RUN_S


def test_the_wall_stretches_to_the_chapter_quiet():
    assert pg.narration_wall(120.0, 0.9) == 108.0


def test_g_sync_cure_opens_the_next_shot_with_the_dialogue():
    doc = {"shots": [{"index": 0}, {"index": 1}, {"index": 2}],
           "lines": [{"index": 0, "kind": "narration", "shot": 0},
                     {"index": 1, "kind": "narration", "shot": 1},
                     {"index": 2, "kind": "dialogue", "shot": 1},
                     {"index": 3, "kind": "narration", "shot": 2}]}
    assert [l["shot"] for l in plan_cures.dialogue_first(doc)["lines"]] == [0, 1, 2, 2]
    assert plan_cures.cure_for("G-SYNC line 2: a dialogue line must be the first line") == "dialogue_first"


def test_g_sync_cure_leaves_a_last_shot_dialogue_alone():
    doc = {"shots": [{"index": 0}],
           "lines": [{"index": 0, "kind": "narration", "shot": 0},
                     {"index": 1, "kind": "dialogue", "shot": 0}]}
    assert [l["shot"] for l in plan_cures.dialogue_first(doc)["lines"]] == [0, 0]


def test_chapter_faults_reads_both_walls_from_the_chapter(monkeypatch):
    seen = {}
    monkeypatch.setattr(pg, "faults", lambda ep, quote_at=None, quiet=None, speech=None:
                        seen.update(q=quote_at, z=quiet, s=speech) or [])
    assert pg.chapter_faults(object(), SILENT) == []
    assert seen == {"q": pg.quote_share(SILENT), "z": pg.quiet_share(SILENT), "s": pg.speech_share(SILENT)}


def test_scare_quotes_and_citations_are_not_speech():
    """ch. II's only marks: 'splashed' (a scare quote) and a citation mid-sentence."""
    ch = ['the earth had “splashed”—splashed is the only word' * 3,
          'that was the hand, “teacher and agent of the brain.” While the rest dwindled' * 3]
    assert pg.quiet_share(ch) == 1.0
    assert pg.quiet_share(['“Come along now,” he said.' + ' We went.' * 40]) < 0.99


def _lines(*spec):
    return [{"index": i, "kind": k, "shot": s, "text": f"t{i}"} for i, (k, s) in enumerate(spec)]


def test_g_sync_cure_moves_the_narration_back_when_the_next_shot_is_full():
    doc = {"shots": [{"index": i} for i in range(3)],
           "lines": _lines(("narration", 0), ("narration", 1), ("dialogue", 1), ("narration", 2), ("narration", 2))}
    assert [l["shot"] for l in plan_cures.dialogue_first(doc)["lines"]] == [0, 0, 1, 2, 2]


def test_g_sync_cure_swaps_within_the_shot_when_both_neighbours_are_full():
    """ep19 line 3: shots 0 and 2 each carry the contract's two lines."""
    doc = {"shots": [{"index": i} for i in range(3)],
           "lines": _lines(("narration", 0), ("narration", 0), ("narration", 1), ("dialogue", 1),
                           ("narration", 2), ("narration", 2))}
    got = plan_cures.dialogue_first(doc)["lines"]
    assert [(l["index"], l["kind"], l["text"]) for l in got[2:4]] == [(2, "dialogue", "t3"), (3, "narration", "t2")]
    assert [l["shot"] for l in got] == [0, 0, 1, 1, 2, 2]


# ---- the dialogue dial's floor follows the chapter (ep22, 2026-10-07) --------------
# WotW II.v "The Stillness" has no spoken line; the contract's 5% floor refused every
# honest draft three times a rung, and the ladder judged the stale disk plan instead.

def test_speech_share_is_the_chapters_spoken_words_over_all_its_words():
    assert pg.speech_share(TALKY) > 0.2
    assert pg.speech_share(['"Come along now," he said.' + ' We went.' * 40]) < 0.1
    assert pg.speech_share(SILENT) == 0.0 and pg.speech_share([]) is None


def test_the_dial_floor_is_the_lesser_of_the_contract_and_the_chapter():
    from studio.episode_spec import DIALOGUE_SHARE
    assert pg.dial_floor(None) == DIALOGUE_SHARE[0]
    assert pg.dial_floor(0.5) == DIALOGUE_SHARE[0]
    assert pg.dial_floor(0.02) == 0.02 and pg.dial_floor(0.0) == 0.0


def _ep_with_dialogue(share_words: int, total: int):
    narration = " ".join(["w"] * (total - share_words))
    lines = [SimpleNamespace(kind="narration", text=narration, shot=0)]
    if share_words:
        lines.append(SimpleNamespace(kind="dialogue", text=" ".join(["d"] * share_words), shot=0))
    return SimpleNamespace(lines=lines)


def test_a_quiet_plan_of_a_quiet_chapter_is_not_refused_but_of_a_talky_one_is():
    assert pg.dial_faults(_ep_with_dialogue(0, 100), speech=0.0) == []
    assert pg.dial_faults(_ep_with_dialogue(1, 100), speech=0.3)
    assert not pg.dial_faults(_ep_with_dialogue(8, 100), speech=0.3)
