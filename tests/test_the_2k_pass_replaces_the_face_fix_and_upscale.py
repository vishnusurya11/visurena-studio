"""The 4-step 2K pass (owner 2026-10-29: "if it takes references and fixes faces and flickering ... we
should eliminate our previous face fix and upscale steps"; "4 step 2k"; "Fluttering is definitely gone").

Open-H3-Regenerate-2K on every take of the judged cut, from the take's own references, replaces the face
refine (switched off, not deleted) and, shot by shot, the av3 upscale (kept as the fallback).  A take whose
faces outnumber its reference sheets is not regenerated: ep04 T07's two constables had no sheet and came
back as a hatched mesh (bench 2026-10-29).  The pass spends what the episode's 6 h clock has left."""
import pytest

from studio import regen_2k as rg


def test_the_pass_is_on_unless_switched_off():
    assert rg.on({}) is True
    assert rg.on({rg.SETTING: "1"}) is True
    assert rg.on({rg.SETTING: "0"}) is False


def test_the_face_refine_is_switched_off_while_the_pass_is_on(monkeypatch):
    from studio import face_refine
    card, dq = {"faces": ["utterson"]}, {"passed": True}
    monkeypatch.setattr(face_refine, "passed_but_warp", lambda dq: True)
    monkeypatch.setenv(rg.SETTING, "1")
    assert face_refine.eligible(card, ["close"], dq) is False
    monkeypatch.setenv(rg.SETTING, "0")
    assert face_refine.eligible(card, ["close"], dq) is True


def test_the_regen_draws_at_twice_the_canvas():
    assert rg.canvas(768, 768) == (1536, 1536)
    assert rg.canvas(576, 1024) == (1152, 2048)


@pytest.mark.parametrize("faces, refs, ok", [
    (1, ["refs/characters/mr_guest/sheet_front.png", "episodes/ep05/storyboard/h3/shot_21.png"], True),
    (2, ["refs/characters/mr_guest/sheet_front.png", "episodes/ep05/storyboard/h3/shot_21.png"], False),
    (2, ["episodes/ep04/storyboard/h3/shot_07.png"], False),           # ep04 T07: the constables
    (0, ["episodes/ep05/storyboard/h3/shot_11.png"], True),            # a place: nothing to garble
    (1, ["refs/characters/reginald_lanyon/looks/pale_fallen.png", "x/shot_06.png"], True),
])
def test_a_take_is_regenerated_only_when_every_face_has_a_sheet(faces, refs, ok):
    assert rg.covered(faces, refs) is ok


def test_takes_with_people_go_first_then_cut_order():
    jobs = [{"index": 3, "people": 0}, {"index": 1, "people": 2}, {"index": 7, "people": 0}, {"index": 4, "people": 1}]
    assert [j["index"] for j in rg.order(jobs)] == [1, 4, 3, 7]


def test_a_take_whose_face_warps_goes_before_any_other():
    """Jekyll ep06 (2026-10-29): the pass ran in cut order on its 60 min floor and T23, T25, T27 -- the takes the
    eye flagged for a face redrawn frame to frame, the flutter the pass cures -- sat last and were cut for time."""
    jobs = [{"index": 1, "people": 1}, {"index": 23, "people": 2, "warp": True}, {"index": 5, "people": 0},
            {"index": 27, "people": 1, "warp": True}]
    assert [j["index"] for j in rg.order(jobs)] == [23, 27, 1, 5]


def test_the_warped_takes_are_read_off_the_current_eye():
    eye = {"faults": [{"kind": "warp", "where": "T23"}, {"kind": "cut", "where": "T24"}, {"kind": "warp", "where": "T27"}]}
    assert rg.warped(eye) == {23, 27}
    assert rg.warped(None) == set()


def test_a_job_is_priced_from_the_measured_rate():
    assert rg.projected_s(100) == pytest.approx(100 * rg.SECONDS_PER_FRAME + rg.JOB_OVERHEAD_S)


def test_the_pass_gets_what_the_six_hour_clock_has_left():
    assert rg.left_s(spent=4 * 3600, limit=6 * 3600, reserve=1200) == pytest.approx(2 * 3600 - 1200)
    assert rg.left_s(spent=7 * 3600, limit=6 * 3600, reserve=1200) == rg.FLOOR_S    # a late episode: the floor
    assert rg.left_s(spent=5.2 * 3600, limit=6 * 3600, reserve=1200) == rg.FLOOR_S


def test_the_graph_names_every_reference_and_no_empty_slot():
    template = {"video": {"inputs": {"file": ""}}, "r2v": {"inputs": {"prompt": "", "width": 0, "height": 0, "length": 0}},
                "save": {"inputs": {"filename_prefix": ""}}, "noise": {"inputs": {"noise_seed": 0}}}
    inject = {"video": {"node": "video", "field": "file"}, "prompt": {"node": "r2v", "field": "prompt"},
              "width": {"node": "r2v", "field": "width"}, "height": {"node": "r2v", "field": "height"},
              "frames": {"node": "r2v", "field": "length"}, "filename_prefix": {"node": "save", "field": "filename_prefix"},
              "seed": {"node": "noise", "field": "noise_seed"}}
    card = {"index": 5, "prompt": "P", "frames": 121}
    g = rg.graph(template, inject, card, "T05_in.mp4", ["a.png", "b.png"], (1536, 1536), "regen2k/x")
    assert g["video"]["inputs"]["file"] == "T05_in.mp4"
    assert g["r2v"]["inputs"]["length"] == 121 and g["r2v"]["inputs"]["width"] == 1536
    assert g["r2v"]["inputs"]["ref_images.ref_image_0"] == ["ref0", 0]
    assert g["r2v"]["inputs"]["ref_images.ref_image_1"] == ["ref1", 0]
    assert "ref_images.ref_image_2" not in g["r2v"]["inputs"]
    assert g["ref1"] == {"class_type": "LoadImage", "inputs": {"image": "b.png"}}
    assert template["r2v"]["inputs"].get("ref_images.ref_image_0") is None      # the template is not touched


def test_a_regen_counts_only_for_the_take_bytes_it_was_drawn_from():
    assert rg.current({"take_sha8": "abcd1234"}, "abcd1234") is True
    assert rg.current({"take_sha8": "abcd1234"}, "ffff0000") is False
    assert rg.current(None, "abcd1234") is False


def test_the_cut_layout_becomes_segments_with_their_source():
    rows = [{"index": 0, "head": 0.0, "slow": 1.0, "still": False},
            {"index": 1, "head": 0.5, "slow": 1.0, "still": False},
            {"index": 2, "head": 0.0, "slow": 1.0, "still": True}]
    segs = rg.segments(rows, {0: 10, 1: 20, 2: 5}, done={0: "r0.mp4", 1: "r1.mp4", 2: "r2.mp4"}, guards={})
    assert [(s.start, s.frames, s.regen) for s in segs] == [(0, 10, "r0.mp4"), (10, 20, "r1.mp4"), (30, 5, None)]
    assert segs[1].head == 0.5


def test_a_regen_segment_is_built_the_way_the_cut_built_it():
    vf = rg.segment_filter(slow=1.0, guard=None, size=(3072, 3072), fps=24)
    assert vf.startswith("scale=3072:3072:force_original_aspect_ratio=increase:flags=lanczos,crop=3072:3072")
    guarded = rg.segment_filter(slow=1.25, guard=(700, 760, 34, 4), size=(3072, 3072), fps=24)
    assert guarded.startswith("crop=1400:1520:68:8,setpts=1.25*PTS,")     # the gutter crop at the regen's 2x


def test_the_splice_takes_regen_frames_where_they_exist_and_the_picture_elsewhere():
    segs = [rg.Segment(0, 2, 0, 0.0, 1.0, None, None), rg.Segment(2, 3, 1, 0.0, 1.0, None, "r1.mp4"),
            rg.Segment(5, 1, 2, 0.0, 1.0, None, None)]
    picture = iter([b"p0", b"p1", b"p2", b"p3", b"p4", b"p5", b"p6"])
    opened = {}

    def open_regen(seg):
        opened[seg.index] = iter([b"r0", b"r1", b"r2"])
        return lambda: next(opened[seg.index])
    wrote = []
    n = rg.pump(segs, total=7, read_picture=lambda: next(picture), open_regen=open_regen, write=wrote.append)
    assert wrote == [b"p0", b"p1", b"r0", b"r1", b"r2", b"p5", b"p6"] and n == 7


def test_a_regen_that_runs_dry_gives_its_frames_back_to_the_picture():
    segs = [rg.Segment(0, 3, 1, 0.0, 1.0, None, "r1.mp4")]
    picture = iter([b"pp0", b"pp1", b"pp2"])
    regen = iter([b"rr0", b""])
    wrote = []
    rg.pump(segs, 3, lambda: next(picture), lambda seg: lambda: next(regen, b""), wrote.append, nbytes=3)
    assert wrote == [b"rr0", b"pp1", b"pp2"]


def test_the_splice_swaps_exactly_the_regenerated_frames(tmp_path):
    import subprocess
    import numpy as np

    def clip(path, colour, frames):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c={colour}:s=32x32:r=24",
                        "-frames:v", str(frames), "-pix_fmt", "yuv420p", str(path)], check=True)
    picture, regen, out = tmp_path / "pic.mp4", tmp_path / "regen.mp4", tmp_path / "out.mp4"
    clip(picture, "red", 10)
    clip(regen, "blue", 8)
    segs = [rg.Segment(0, 3, 0, 0.0, 1.0, None, None), rg.Segment(3, 4, 1, 0.0, 1.0, None, str(regen)),
            rg.Segment(7, 2, 2, 0.0, 1.0, None, None)]
    assert rg.splice(picture, out, segs, (64, 64), 24, "cpu", total=10) == 10
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, 64, 64, 3)
    blue = [bool(f[..., 2].mean() > f[..., 0].mean()) for f in frames]
    assert len(frames) == 10 and blue == [False] * 3 + [True] * 4 + [False] * 3


def _episode(tmp_path, monkeypatch):
    from scripts.episode import regen_2k as runner
    from studio import episode_home
    takes = tmp_path / "takes" / "r2v"
    takes.mkdir(parents=True)
    monkeypatch.setattr(episode_home, "takes_dir", lambda book, number, engine="i2v": takes)
    return runner, takes, takes.parent / runner.ROOM


def test_a_regen_is_spliced_only_while_it_answers_the_take_on_disk(tmp_path, monkeypatch):
    from studio import youtube_publish as yp
    runner, takes, room = _episode(tmp_path, monkeypatch)
    room.mkdir()
    for k in (1, 2, 3):
        (takes / f"T0{k}.mp4").write_bytes(b"take%d" % k)
        (room / f"T0{k}.mp4").write_bytes(b"regen")
    runner.write_record(room, {"T01": {"take_sha8": yp.sha8(takes / "T01.mp4"), "drawn": True},
                               "T02": {"take_sha8": "00000000", "drawn": True},          # the take was retaken
                               "T03": {"take_sha8": yp.sha8(takes / "T03.mp4"), "drawn": False}})
    assert runner.done(tmp_path, 6, "r2v") == {1: str(room / "T01.mp4")}


def test_the_jobs_are_the_cuts_moving_takes_not_yet_drawn(tmp_path, monkeypatch):
    from studio import youtube_publish as yp
    runner, takes, _room = _episode(tmp_path, monkeypatch)
    for k in (0, 1, 2):
        (takes / f"T0{k}.mp4").write_bytes(b"take%d" % k)
    cards = {0: {"refs": ["refs/characters/a/sheet.png", "p.png"]}, 1: {"refs": ["p.png"]}, 2: {"refs": ["p.png"]}}
    rows = [{"index": 0}, {"index": 1}, {"index": 2, "still": True}]
    drawn = {"T00": {"take_sha8": yp.sha8(takes / "T00.mp4"), "drawn": True}}
    assert [j["index"] for j in runner.jobs_of(cards, rows, takes, drawn)] == [1]
    jobs = runner.jobs_of(cards, rows, takes, {})
    assert [(j["index"], j["people"]) for j in jobs] == [(0, 1), (1, 0)]


def test_step_11_draws_the_2k_pass_before_the_one_upscale(monkeypatch, tmp_path):
    from scripts.episode import step_11_qc as s11
    calls = []

    class Ctx:
        home = tmp_path

        def run_script(self, script, *extra, gpu=False, clock=None):
            calls.append(script)
    monkeypatch.setenv(rg.SETTING, "1")
    monkeypatch.setattr(s11, "pair", lambda home, engine: (tmp_path / "master_r2v.mp4", tmp_path / "qc_r2v.json"))
    monkeypatch.setattr(s11, "judged_pair", lambda home, engine: (tmp_path / "cut_r2v.mp4", tmp_path / "qc_cut.json"))
    monkeypatch.setattr(s11, "is_cut", lambda path: True)
    monkeypatch.setattr(s11.master_upscale, "made_from", lambda master: "")
    monkeypatch.setattr(s11.yp, "sha8", lambda path: "cafe0001")
    monkeypatch.setattr(s11, "carry", lambda ctx, engine: None)
    s11.deliver_master(Ctx(), [])
    assert calls == ["scripts/episode/regen_2k.py", "scripts/episode/assemble.py"]
    calls.clear()
    monkeypatch.setenv(rg.SETTING, "0")
    s11.deliver_master(Ctx(), [])
    assert calls == ["scripts/episode/assemble.py"]
