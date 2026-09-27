"""A picture the vision model has already read is not read again.

MEASURED on ep13 (2026-09-27, speed plan #5): panel_content ran 28 full passes
(430 min) and the eye ~26 more (~300 min) -- 675+ reads of 25 panels, at most
177 of them pictures that had changed.  Every read costs ~27.5 s.

The cache keeps the model's RAW answer, keyed on everything that makes it: the
workflow (model, node settings), its inject map and the values -- the staged
image name is content-addressed, so the key carries the picture's bytes.  The
judging still runs in code on every read, so a judge fix still applies.  An
answer the caller cannot read is never kept: it is asked again next time.
"""
from studio import comfy

TEMPLATE = ({"1": {"inputs": {"model": "Qwen3-VL-8B", "prompt": ""}}}, {"prompt": ["1", "prompt"]})


def fake_engine(monkeypatch, answers):
    asked = []
    monkeypatch.setattr(comfy, "load_workflow", lambda name: TEMPLATE)
    monkeypatch.setattr(comfy, "run_text", lambda name, values, timeout=600.0: asked.append(values) or answers.pop(0))
    return asked


def test_the_same_picture_and_prompt_is_read_once(monkeypatch, tmp_path):
    asked = fake_engine(monkeypatch, ['{"people": 1}'])
    values = {"image_1": "abc123_shot_00.png", "prompt": "list"}
    first = comfy.cached_text("caption", values, readable=lambda t: True, root=tmp_path)
    again = comfy.cached_text("caption", values, readable=lambda t: True, root=tmp_path)
    assert first == again == '{"people": 1}' and len(asked) == 1


def test_a_changed_picture_is_read(monkeypatch, tmp_path):
    asked = fake_engine(monkeypatch, ["a", "b"])
    comfy.cached_text("caption", {"image_1": "abc123_x.png"}, readable=lambda t: True, root=tmp_path)
    comfy.cached_text("caption", {"image_1": "def456_x.png"}, readable=lambda t: True, root=tmp_path)
    assert len(asked) == 2


def test_a_changed_workflow_is_read(monkeypatch, tmp_path):
    fake_engine(monkeypatch, ["a"])
    key = comfy.text_key("caption", {"image_1": "abc123_x.png"})
    monkeypatch.setattr(comfy, "load_workflow", lambda name: ({"1": {"inputs": {"model": "Qwen3-VL-4B"}}}, {}))
    assert comfy.text_key("caption", {"image_1": "abc123_x.png"}) != key


def test_an_unreadable_answer_is_never_kept(monkeypatch, tmp_path):
    asked = fake_engine(monkeypatch, ['{"people": ', '{"people": 2}'])
    values = {"image_1": "abc123_x.png"}
    readable = lambda t: t.endswith("}")
    assert comfy.cached_text("caption", values, readable=readable, root=tmp_path) == '{"people": '
    assert comfy.cached_text("caption", values, readable=readable, root=tmp_path) == '{"people": 2}'
    assert len(asked) == 2


def test_a_reply_the_content_reader_cannot_parse_is_not_readable():
    from studio import panel_content as pc
    assert not pc.readable("I cannot see the picture.")


def test_the_panel_eye_reads_through_the_cache_and_keeps_only_json(monkeypatch, tmp_path):
    """The eye's own reads (~300 min on ep13) share the cache; only an answer
    that parses as JSON is kept, so a garbled one is asked again."""
    from studio.judges import panel_eye
    asked = fake_engine(monkeypatch, ["not json", '{"a": 1}', "unused"])
    monkeypatch.setattr(comfy, "TEXT_CACHE", tmp_path)
    run = panel_eye.cached_run
    values = {"image_1": "abc123_x.png"}
    assert run("pose", values) == "not json"
    assert run("pose", values) == '{"a": 1}'
    assert run("pose", values) == '{"a": 1}' and len(asked) == 2
