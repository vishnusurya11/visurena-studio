"""ep19 rung 2 (2026-10-07 16:06Z): shot 16's camera read "Camera stands level
with the curate's face ... at face height" and G-LAID refused it -- the rule's
own wording, said with a name instead of a pronoun ("level with his face").
The gate reads 'level with <anyone>'s face/head/eyes' and 'at face height'
as seeing the laid person; the drawer's failure mode (standing them up) is
the camera that says neither."""
from __future__ import annotations

from types import SimpleNamespace

from studio import cell_gates


def _shot(camera: str) -> SimpleNamespace:
    return SimpleNamespace(index=16, size="medium_close", faces=["curate"],
                           frame="Medium-close view of the curate lying at the slit", at_rest="", camera=camera)


def test_level_with_a_named_face_is_seen():
    assert cell_gates.laid_unseen(_shot("Camera stands level with the curate's face inside the ruined kitchen")) is False


def test_at_face_height_is_seen_and_a_pronoun_still_is():
    assert cell_gates.laid_unseen(_shot("Camera at face height, one yard from him")) is False
    assert cell_gates.laid_unseen(_shot("Camera lies on the ground level with his face")) is False


def test_a_camera_that_says_neither_is_still_refused():
    assert cell_gates.laid_unseen(_shot("Camera stands low over him, a 50mm lens")) is True
