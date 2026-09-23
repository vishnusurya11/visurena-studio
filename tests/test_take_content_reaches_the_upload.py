"""The take content verdict uses the plan's declared people, and the upload
can see it.

Audit item 4, 2026-09-22: the take content checker lived in a session folder,
wrote its verdict nowhere the upload reads, and `take_faults` never passed a
shot's size or declared extras through, so a take was judged by the rules the
panel gate had just dropped.
"""
import json

from studio.judged import unjudged_takes
from studio.panel_content import Seen
from studio.take_content import take_faults


def seen(people=1, text=False):
    return Seen(landform="flat", people=people, lookalikes=0, text=text, hour="day",
                subjects=["a man"])


def judge(reads, **kw):
    base = dict(planned=0, crowd=False, flat=False, night=False, physical="", frame="a road")
    base.update(kw)
    return take_faults(reads, **base)


def test_an_undeclared_person_in_a_take_is_a_fault():
    assert judge([seen(people=1)])


def test_a_declared_extra_is_not():
    assert not judge([seen(people=1)], extras=1)


def test_lettering_is_excused_on_a_newspaper_insert():
    assert not judge([seen(people=0, text=True)],
                     frame="Insert on the front page of an evening newspaper", size="insert")


def test_lettering_is_not_excused_on_a_wide_that_mentions_a_poster():
    assert judge([seen(people=0, text=True)], frame="Wide on the platform, a poster", size="wide")


def room(tmp_path, dq=True, content=True):
    (tmp_path / "shots.json").write_text(json.dumps([{"index": 0}]))
    (tmp_path / "T00.mp4").write_bytes(b"mp4")
    if dq:
        (tmp_path / "T00.dq.json").write_text(json.dumps({"passed": True}))
    if content:
        (tmp_path / "T00.content.json").write_text(json.dumps({"passed": True}))
    return tmp_path


def test_a_take_with_both_verdicts_is_judged(tmp_path):
    assert unjudged_takes(room(tmp_path), kinds=("dq", "content")) == []


def test_a_take_missing_its_content_verdict_is_not(tmp_path):
    assert unjudged_takes(room(tmp_path, content=False), kinds=("dq", "content")) == ["T00"]


def test_the_default_still_asks_only_for_the_take_gate(tmp_path):
    assert unjudged_takes(room(tmp_path, content=False)) == []
