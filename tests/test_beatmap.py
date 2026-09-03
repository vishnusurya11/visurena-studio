

class TestLateDensity:
    """The arc asks for its fastest cutting at 85-90%; the cue has to have
    onsets there for `cut_points` to land on.

    MEASURED on the chosen Scarlet cue: its eighth decile (81.4-91.6s) holds
    ONE onset and the 86.5-91.6s window holds ZERO.  `trailer_fitness` counted
    TOTAL onsets and never asked where they were, so it scored a cue that
    cannot be cut to the arc exactly as highly as one that can.  One shot then
    stretched to 7.42 seconds at the climax.
    """

    def test_it_counts_onsets_in_the_window_the_arc_needs(self):
        from studio.beatmap import late_density
        dense = [i * 0.5 for i in range(200)]
        assert late_density(dense, 100.0) >= 3

    def test_a_cue_that_empties_out_late_scores_zero(self):
        from studio.beatmap import late_density
        early = [i * 0.5 for i in range(120)]  # nothing past 60s
        assert late_density(early, 100.0) == 0

    def test_fitness_prefers_the_cue_that_can_be_cut_to(self):
        from studio.beatmap import trailer_fitness
        import numpy as np
        times = np.linspace(0, 100, 400)
        db = np.linspace(-50, -5, 400)
        dense = [i * 0.5 for i in range(200)]
        sparse = [i * 0.5 for i in range(120)]
        assert trailer_fitness(times, db, dense) > trailer_fitness(times, db, sparse)
