from pathlib import Path



class TestLimitingIsNotTheSound:
    """LIMITING_DB was raised to 5.5 to reach an average, and 5.5 dB of gain
    reduction is not a safety net -- it is the wall the owner heard.  The
    average is found before the limiter instead: the bed is peak-limited to
    -1 dBTP before the sum, and every levelled line to -3.

    This is the MASTERING allowance, not the acceptance gate: QC still
    measures the finished file and still refuses it outside -15.5..-12.5 with
    a true peak over -1.0 dBTP.
    """

    def test_the_limiter_only_catches_what_the_headroom_missed(self):
        from studio.trailer_assemble import LIMITING_DB
        assert LIMITING_DB <= 2.0

    def test_the_headroom_it_replaces_is_made_at_the_source(self):
        from studio.trailer_assemble import BED_TP, LINE_TP
        assert BED_TP <= -1.0 and LINE_TP <= -3.0

    def test_a_ceiling_is_asked_for_below_the_true_peak_it_has_to_hold(self):
        """alimiter is a sample-peak limiter; intersample peaks run over it."""
        from studio.trailer_assemble import LIMITER_MARGIN, db_to_linear, limiter
        assert LIMITER_MARGIN > 0.0
        assert limiter(-1.0) == f"alimiter=limit={db_to_linear(-1.5)}:level=disabled"


class TestConcatListing:
    """Scarlet run 6 died in step 08: the blind path hands `assemble` a
    repo-relative book dir, the listing said `file 'library/.../s000.mp4'`,
    and ffmpeg's concat demuxer resolves a relative entry against the LIST
    FILE's directory -- so it looked for work/library/.../work/s000.mp4.
    Three trailers had shipped from absolute dirs and never hit it."""

    def test_entries_are_relative_to_the_listing_not_the_cwd(self, tmp_path, monkeypatch):
        from studio.trailer_assemble import listing_lines
        monkeypatch.chdir(tmp_path)
        work = Path("library/book/trailer/main/work")
        work.mkdir(parents=True)
        lines = listing_lines([work / "s000.mp4", work / "s001.mp4"], work / "shots.txt")
        assert lines == ["file 's000.mp4'", "file 's001.mp4'"]

    def test_a_segment_outside_the_listing_dir_climbs_to_it(self, tmp_path, monkeypatch):
        from studio.trailer_assemble import listing_lines
        monkeypatch.chdir(tmp_path)
        lines = listing_lines([Path("clips/B00.mp4")], Path("main/work/shots.txt"))
        assert lines == ["file '../../clips/B00.mp4'"]
