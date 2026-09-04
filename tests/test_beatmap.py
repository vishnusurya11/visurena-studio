

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


class TestStructuralFitness:
    """Item 7: fitness reads the MEASURED metre, not the caption.

    Eight seeds of one caption ranged 0.31-0.97 bars-in-mode; a cue the walk
    cannot count in bars is worth less than one it can, and a cue with two
    troughs holds a hook AND a threat where one trough holds only one.
    """

    @staticmethod
    def envelope(troughs, seconds=100.0, level=-20.0, depth=10.0, hold=3.0):
        import numpy as np
        from studio.beatmap import WINDOW
        times = np.arange(int(seconds / WINDOW)) * WINDOW
        db = np.full(len(times), level)
        for start in troughs:
            db[int(start / WINDOW):int((start + hold) / WINDOW)] = level - depth
        return times, db

    @staticmethod
    def grid(bars_in_mode, bpm=120.0):
        from studio.beatmap import Grid
        return Grid(beats=[], downbeats=[], bpm=bpm, bar=240.0 / bpm,
                    beats_per_bar=4, bars_in_mode=bars_in_mode)

    def test_slots_are_troughs_held_a_bar_inside_the_middle(self):
        from studio.beatmap import slots
        times, db = self.envelope([10.0, 40.0, 60.0, 90.0])
        found = slots(times, db, self.grid(0.9))
        assert [round(s.start) for s in found] == [40, 60]
        assert all(s.seconds >= 2.0 for s in found)

    def test_fitness_ranks_metric_seed_above_rubato_seed(self):
        from studio.beatmap import trailer_fitness
        times, db = self.envelope([40.0, 60.0])
        assert (trailer_fitness(times, db, metre=self.grid(0.95))
                > trailer_fitness(times, db, metre=self.grid(0.31)))

    def test_fitness_prefers_cue_with_two_slots(self):
        from studio.beatmap import trailer_fitness
        two = self.envelope([40.0, 60.0])
        one = self.envelope([40.0])
        assert (trailer_fitness(*two, metre=self.grid(0.9))
                > trailer_fitness(*one, metre=self.grid(0.9)))

    def test_tempo_term_rewards_the_cuttable_band(self):
        from studio.beatmap import tempo_term
        assert tempo_term(100) == 1.0 > tempo_term(150) > tempo_term(200)
