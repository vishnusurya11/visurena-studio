"""A reference handed back unchanged is a copy by hash: pHash within PHASH_COPY
bits of a staged input.  A crop of it hashes further off, so SSIM against the
reference's centre crops corroborates within PHASH_NEAR."""
import io

import numpy as np
from PIL import Image, ImageDraw

from studio.measure import copy as cp


def _picture(seed: int = 1) -> Image.Image:
    rng = np.random.default_rng(seed)
    base = rng.integers(40, 200, (16, 16, 3), dtype=np.uint8)
    im = Image.fromarray(base).resize((512, 512), Image.BILINEAR)
    d = ImageDraw.Draw(im)
    x, y = (int(v) for v in rng.integers(20, 200, 2))       # another picture has its own shapes
    d.rectangle((x, y + 40, x + 180, y + 300), fill=(20, 20, 30))
    d.ellipse((y + 130, x + 20, y + 270, x + 160), fill=(230, 220, 190))
    return im


def _resaved(im: Image.Image) -> Image.Image:
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=70)
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


def test_a_handed_back_reference_is_a_copy():
    ref = _picture()
    row = cp.compare(_resaved(ref), ref)
    assert row["phash"] <= cp.PHASH_COPY and cp.is_copy(row)


def test_another_picture_is_not_a_copy():
    row = cp.compare(_picture(2), _picture(1))
    assert row["phash"] > cp.PHASH_NEAR and not cp.is_copy(row)


def test_ssim_corroborates_a_crop():
    ref = _picture()
    crop = cp.centre_crop(ref, 0.8).resize((512, 512))
    assert cp.compare(crop, ref)["ssim"] >= cp.SSIM_COPY


def test_the_walls_are_hash_first_then_ssim_with_a_near_hash():
    assert cp.is_copy({"phash": 12, "ssim": 0.7})
    assert not cp.is_copy({"phash": 12, "ssim": 0.3})
    assert not cp.is_copy({"phash": 20, "ssim": 0.9})


def test_the_best_match_among_staged_inputs_is_named(tmp_path):
    ref, other = _picture(1), _picture(3)
    ref.save(tmp_path / "ref.png"), other.save(tmp_path / "other.png")
    best = cp.against(_resaved(ref), [tmp_path / "other.png", tmp_path / "ref.png"])
    assert best["path"].endswith("ref.png") and best["copy"]
