"""Only what is needed goes in: a sheet for a face that READS, a real length.

OWNER 2026-09-13: "clean up inputs .. only put what are needed ... not too many
images of same person as ref".

MEASURED on episode 3: 6 cast sheets were staged for faces no segment shows,
and T04 staged BOTH Watson and Holmes for a take whose segments declare no
readable face at all -- two of its seven reference slots spent on men nobody
sees. Each one is a whole-frame studio portrait competing with the storyboard
cell for the same man.
"""
import importlib.util
import sys

import pytest

spec = importlib.util.spec_from_file_location("takes_r2v", "scripts/episode/takes_r2v.py")
tr = importlib.util.module_from_spec(spec)
sys.modules["takes_r2v"] = tr
spec.loader.exec_module(tr)

from studio.episode_ref_official import take_end, stated_end


class Cut:
    def __init__(self, faces=(), **kw):
        self.faces = list(faces)
        for k in ("frame", "motion", "camera", "at_rest", "end", "changed"):
            setattr(self, k, kw.get(k, ""))


class Shot(Cut):
    def __init__(self, index=0, faces=(), cuts=(), **kw):
        super().__init__(faces, **kw)
        self.index, self.cuts = index, list(cuts)


def test_a_face_that_reads_gets_its_sheet():
    assert tr.faces_of([Shot(0, ["john_watson"])]) == ["john_watson"]


def test_a_take_with_no_readable_face_stages_no_sheet():
    """Episode 3 T04: two sheets for a take that declares no face."""
    assert tr.faces_of([Shot(0, [], cuts=[Cut([])])]) == []


def test_being_NAMED_in_the_prose_no_longer_earns_a_whole_picture():
    """Owner 2026-09-12 gave a sheet to anyone the text NAMED, after Watson was
    rendered without his moustache. Measured a day later, that rule staged a
    full-length studio portrait of a man no shot shows -- a second whole-frame
    composition of him for the render to reach for. The prose still names him;
    he simply does not get his own picture unless his face must read."""
    shot = Shot(0, [], motion="Holmes turns from the fire toward Watson.")
    assert tr.faces_of([shot], ["john_watson", "sherlock_holmes"]) == []


def test_a_sub_shot_face_still_counts():
    assert tr.faces_of([Shot(0, [], cuts=[Cut(["sherlock_holmes"])])]) == ["sherlock_holmes"]


# ---- D: the prompt states the length the video actually has ----------------

def test_the_stated_end_is_the_real_latent_not_the_ceiling():
    """`take_end` ceils: a 294-frame take (12.25 s) was announced as 13 s, so the
    model laid three shots across 0.75 s that does not exist. 16 of 22 prompts
    overran, by up to 0.75 s."""
    assert take_end(294) == 13          # the old ceiling, still used for coverage
    assert stated_end(294) == 12         # what the take actually reaches


def test_an_exact_take_is_unchanged():
    assert stated_end(288) == 12 and take_end(288) == 12


def test_the_stated_end_never_goes_below_one_second():
    assert stated_end(6) == 1
