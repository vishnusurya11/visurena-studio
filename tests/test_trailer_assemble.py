

class TestLimitingHeadroom:
    """A more dynamic cue needs more limiting to reach the same average.

    LIMITING_DB was tuned against a cue with LRA 7.0.  The tone-matched cue has
    LRA 14.2 -- which is the improvement, not a fault -- and a higher crest
    factor means the true-peak ceiling binds sooner, so the same allowance
    landed the master at -17.0 LUFS against a -16.0 floor.

    This raises the MASTERING allowance, not the acceptance gate: QC still
    measures the finished file and still refuses it outside -16.0..-12.5 with
    a true peak over -1.0 dBTP.
    """

    def test_the_allowance_covers_a_high_crest_cue(self):
        from studio.trailer_assemble import LIMITING_DB
        # measured: -17.0 delivered with 2.0 dB, floor is -16.0
        assert LIMITING_DB >= 3.0

    def test_it_stays_within_what_a_trailer_master_would_do(self):
        """Past about 6 dB the limiter is the sound, not the safety net."""
        from studio.trailer_assemble import LIMITING_DB
        assert LIMITING_DB <= 6.0
