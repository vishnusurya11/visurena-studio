"""The gate that Watson and Holmes shipped past at cosine 0.420.

Everything here runs without a model.  The weights answer "who is this";
these tests answer "is the question being asked correctly", and the four
defects the audit found all lived in the second half.
"""
from __future__ import annotations

import numpy as np
import pytest

from studio.identity import (ARCFACE_TEMPLATE, FACE_FLOOR, UNVERIFIABLE_BELOW,
                             align, cosine, similarity_transform, verdict)


class TestSimilarityTransform:
    """Umeyama, so the crop matches what the recogniser was trained on."""

    def test_the_template_maps_to_itself(self):
        matrix = similarity_transform(ARCFACE_TEMPLATE, ARCFACE_TEMPLATE)
        assert np.allclose(matrix[:2, :2], np.eye(2), atol=1e-6)
        assert np.allclose(matrix[:2, 2], 0.0, atol=1e-6)

    def test_a_scaled_and_shifted_face_is_recovered(self):
        moved = ARCFACE_TEMPLATE * 2.0 + np.array([30.0, -12.0])
        matrix = similarity_transform(moved, ARCFACE_TEMPLATE)
        got = moved @ matrix[:2, :2].T + matrix[:2, 2]
        assert np.allclose(got, ARCFACE_TEMPLATE, atol=1e-6)

    def test_a_rotated_face_is_recovered(self):
        angle = np.deg2rad(17.0)
        rotation = np.array([[np.cos(angle), -np.sin(angle)],
                             [np.sin(angle), np.cos(angle)]])
        moved = ARCFACE_TEMPLATE @ rotation.T
        matrix = similarity_transform(moved, ARCFACE_TEMPLATE)
        got = moved @ matrix[:2, :2].T + matrix[:2, 2]
        assert np.allclose(got, ARCFACE_TEMPLATE, atol=1e-6)

    def test_it_never_reflects(self):
        """Umeyama without the det<0 guard mirrors a face and still 'fits'."""
        mirrored = ARCFACE_TEMPLATE * np.array([-1.0, 1.0])
        matrix = similarity_transform(mirrored, ARCFACE_TEMPLATE)
        assert np.linalg.det(matrix[:2, :2]) > 0


class TestAlign:
    def test_it_returns_the_shape_the_recogniser_expects(self):
        image = np.zeros((400, 400, 3), dtype=np.uint8)
        crop = align(image, ARCFACE_TEMPLATE * 2.0 + 80.0)
        assert crop.shape == (112, 112, 3)

    def test_it_keeps_channel_order(self):
        """insightface loads BGR then sets swapRB, so the NET sees RGB.

        'Matching insightface' by swapping cost a measured 0.931 cosine on the
        same face -- enough to move a pair across a threshold, silently.
        """
        image = np.zeros((400, 400, 3), dtype=np.uint8)
        image[..., 0] = 200  # red channel only
        crop = align(image, ARCFACE_TEMPLATE * 2.0 + 80.0)
        assert crop[56, 56, 0] > crop[56, 56, 2]


class TestCosine:
    def test_identical_vectors_score_one(self):
        v = np.array([3.0, 4.0, 0.0])
        assert cosine(v, v) == pytest.approx(1.0)

    def test_it_normalises_so_magnitude_cannot_leak_in(self):
        v = np.array([3.0, 4.0, 0.0])
        assert cosine(v, v * 17.0) == pytest.approx(1.0)

    def test_orthogonal_vectors_score_zero(self):
        assert cosine(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(0.0)


class TestVerdict:
    """Arc2Face's uniqueness line at 0.30; insightface's same-person line at 0.40."""

    def test_a_distinct_pair_passes(self):
        assert verdict(0.187, face_px=180) == "pass"

    def test_the_shipped_watson_holmes_pair_fails(self):
        assert verdict(0.420, face_px=180) == "fail"

    def test_the_band_between_is_review_not_a_quiet_pass(self):
        assert verdict(0.360, face_px=180) == "review"

    def test_the_boundaries_belong_to_the_stricter_side(self):
        assert verdict(0.30, face_px=180) == "review"
        assert verdict(0.40, face_px=180) == "fail"

    def test_a_face_too_small_to_read_returns_unverifiable_not_a_score(self):
        """At 32px the model loses as much self-similarity as a real
        difference is worth, and small faces read wrong in BOTH directions."""
        assert verdict(0.05, face_px=UNVERIFIABLE_BELOW - 1) == "unverifiable"
        assert verdict(0.99, face_px=UNVERIFIABLE_BELOW - 1) == "unverifiable"

    def test_our_shipped_sheets_sit_under_the_floor(self):
        """Measured 57-66px wide; the gate refuses to score them."""
        assert FACE_FLOOR == 64
        assert verdict(0.29, face_px=60) in ("review", "unverifiable")


class TestRecogniserCarriesItsOwnPreprocessing:
    """MEASURED: the same crops score 0.887-0.987 under the wrong scaling and
    0.097-0.540 under the right one.  A backbone's normalisation is not a
    house style -- it is part of the weights."""

    def test_sface_takes_raw_bytes_and_arcface_takes_zero_centred(self):
        from studio.identity import ARCFACE, SFACE
        assert SFACE.zero_centred is False
        assert ARCFACE.zero_centred is True

    def test_each_backbone_carries_its_own_same_person_line(self):
        from studio.identity import ARCFACE, SFACE
        assert SFACE.same_person_at == 0.363     # OpenCV's published value
        assert ARCFACE.same_person_at == 0.40    # insightface's buffalo_l

    def test_only_the_permissively_licensed_backbone_may_ship(self):
        """insightface's zoo is non-commercial; this feeds a monetised channel."""
        from studio.identity import ARCFACE, SFACE
        assert SFACE.ships and not ARCFACE.ships

    def test_a_verdict_uses_the_threshold_of_the_backbone_that_scored_it(self):
        from studio.identity import ARCFACE, SFACE
        assert verdict(0.38, face_px=180, using=SFACE) == "fail"
        assert verdict(0.38, face_px=180, using=ARCFACE) == "review"

    def test_the_shipped_watson_holmes_pair_fails_on_the_backbone_that_ships(self):
        """MEASURED 0.546 on SFace over the a-study-in-scarlet sheets."""
        from studio.identity import SFACE
        assert verdict(0.546, face_px=98, using=SFACE) == "fail"

    def test_scaling_a_normalised_input_is_not_a_free_choice(self):
        from studio.identity import normalise_input
        raw = np.full((112, 112, 3), 200, dtype=np.uint8)
        from studio.identity import ARCFACE, SFACE
        assert normalise_input(raw, SFACE).max() == pytest.approx(200.0)
        assert normalise_input(raw, ARCFACE).max() == pytest.approx(0.568, abs=1e-3)
