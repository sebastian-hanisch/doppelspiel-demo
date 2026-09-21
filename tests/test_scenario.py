import pytest

import dsp_constants as C
import dsp_scenario as SC
from helpers import random_bay


def test_make_bay_is_deterministic_and_seed_dependent():
    a = SC.make_bay(10, 6, 50, 50, 657)
    assert a == SC.make_bay(10, 6, 50, 50, 657)
    assert a != SC.make_bay(10, 6, 50, 50, 658)


def test_counts_are_within_the_number_of_tiers_and_the_totals_add_up():
    for seed in range(40):
        bay = random_bay(seed)
        assert bay.n_stacks == len(bay.u) == len(bay.l) and bay.containers == bay.unloads + bay.loads == sum(bay.u) + sum(bay.l)
        assert all(0 <= x <= 10 for x in bay.u + bay.l)


def test_percent_extremes_are_exact():
    full = SC.make_bay(8, 6, 100, 100, 3)
    assert full.u == (6,) * 8 and full.l == (6,) * 8                              # 100 %: jede Lage (Ziehung 0..99 ist immer kleiner als 100)
    assert SC.make_bay(8, 6, 0, 100, 3).u == (0,) * 8                             # 0 % Entladen: nichts zu löschen
    none = SC.make_bay(8, 6, 0, 0, 3)
    assert none.containers == 1 and none.u[0] == 1                                # ganz ohne Container: ein Container im ersten Stapel


def test_percent_zero_never_draws_a_container_over_many_seeds():
    for seed in range(60):
        assert SC.make_bay(8, 6, 0, 50, seed).u == (0,) * 8


def test_mean_counts_follow_the_percentages():
    unload = [sum(SC.make_bay(20, 10, 30, 70, s).u) / 20 for s in range(50)]
    load = [sum(SC.make_bay(20, 10, 30, 70, s).l) / 20 for s in range(50)]
    assert 2.5 < sum(unload) / 50 < 3.5 and 6.5 < sum(load) / 50 < 7.5


@pytest.mark.parametrize("args", [(0, 6, 50, 50, 1), (5, 0, 50, 50, 1), (5, 6, -1, 50, 1), (5, 6, 101, 50, 1), (5, 6, 50, -1, 1), (5, 6, 50, 101, 1)])
def test_make_bay_rejects_invalid_values(args):
    with pytest.raises(ValueError):
        SC.make_bay(*args)


def test_every_slider_corner_gives_a_valid_bay():
    for s in (C.N_STACKS_RANGE[0], C.N_STACKS_RANGE[1]):
        for t in (C.TIERS_RANGE[0], C.TIERS_RANGE[1]):
            for u in (C.UNLOAD_PCT_RANGE[0], C.UNLOAD_PCT_RANGE[1]):
                for l in (C.LOAD_PCT_RANGE[0], C.LOAD_PCT_RANGE[1]):
                    assert SC.make_bay(s, t, u, l, 7).containers >= 1


def test_custom_bay_validates():
    ok = SC.custom_bay([3, 0], [1, 2])
    assert ok.u == (3, 0) and ok.l == (1, 2) and ok.containers == 6
    for u, l in (([], []), ([1, 2], [1]), ([-1, 2], [1, 1]), ([1.5, 2], [1, 1]), ([True, 1], [1, 1]), ([0, 0], [0, 0])):
        with pytest.raises(ValueError):
            SC.custom_bay(u, l)
    assert SC.custom_bay([0], [1]).loads == 1                                     # nur Laden ist erlaubt


def test_parse_counts_accepts_commas_semicolons_and_spaces():
    assert SC.parse_counts("3, 0, 5") == (3, 0, 5) and SC.parse_counts("3;0;5") == (3, 0, 5) and SC.parse_counts(" 3 0  5 ") == (3, 0, 5) and SC.parse_counts("") == ()
    for bad in ("3, x", "2.5", "1,,-a"):
        with pytest.raises(ValueError):
            SC.parse_counts(bad)
    assert SC.parse_counts("-2") == (-2,)                                         # das Vorzeichen prüft custom_bay, nicht die Zerlegung


def test_prefix_property_more_stacks_keep_the_first_stacks_counts_are_not_promised():
    """make_bay zieht je Stapel nacheinander: gleicher Seed und gleiche Lagen, mehr Stapel: die Zahlen des ersten Stapels bleiben gleich."""
    small, big = SC.make_bay(4, 6, 50, 50, 9), SC.make_bay(8, 6, 50, 50, 9)
    assert big.u[0] == small.u[0]


def test_load_percent_zero_and_hundred_are_exact_over_many_seeds():
    """Die Grenze 'kleiner als' zählt auch beim Laden: bei 0 % wird nie geladen, bei 100 % in jede Lage."""
    for seed in range(60):
        assert SC.make_bay(8, 6, 100, 0, seed).l == (0,) * 8
        assert SC.make_bay(8, 6, 0, 100, seed).l == (6,) * 8
