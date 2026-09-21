import itertools
import statistics

import pytest

import dsp_constants as C
import dsp_rules as R
import dsp_scenario as SC
from helpers import random_bay, simulate_time10, tiny_bay, true_optimum

ORDERS = {"bay": R.bay_order, "short": R.short_first, "johnson": R.johnson, "largest": R.largest_first}


def bay_of(u, l):
    return SC.Bay(tuple(u), tuple(l))


# ---------------------------------------------------------------------------------------------------
# Spielfolge
# ---------------------------------------------------------------------------------------------------
def test_play_pairs_each_unload_with_the_oldest_available_load_and_finishes_with_single_loads():
    bay = bay_of([1, 2, 0], [2, 1, 3])
    assert R.play(bay, (0, 1, 2)) == (("U", 0), ("D", 1, 0), ("D", 1, 0), ("L", 1), ("L", 2), ("L", 2), ("L", 2))


def test_play_none_is_all_unloads_then_all_loads():
    bay = bay_of([2, 1], [1, 2])
    assert R.play_none(bay) == (("U", 0), ("U", 0), ("U", 1), ("L", 0), ("L", 1), ("L", 1))


@pytest.mark.parametrize("name", ["bay", "short", "johnson", "largest"])
def test_every_order_gives_a_valid_play_with_exactly_the_predicted_cycles(name):
    for seed in range(120):
        bay = random_bay(seed, max_stacks=12)
        order = ORDERS[name](bay)
        seq = R.play(bay, order)
        assert sorted(order) == list(range(bay.n_stacks))
        assert R.verify(bay, seq) == () and len(seq) == R.cycles_of(bay, order)
        assert R.counts(seq)[2] == R.duals_of(bay, order) and len(seq) == bay.containers - R.duals_of(bay, order)


def test_play_none_is_valid_and_uses_one_cycle_per_container():
    for seed in range(60):
        bay = random_bay(seed)
        seq = R.play_none(bay)
        assert R.verify(bay, seq) == () and len(seq) == bay.containers and R.counts(seq) == (bay.unloads, bay.loads, 0)


def test_counts_and_time10_and_the_independent_time_simulation():
    seq = (("U", 0), ("D", 1, 0), ("L", 1))
    assert R.counts(seq) == (1, 1, 1)
    assert R.time10(seq, 14) == 10 + 14 + 10 == simulate_time10(seq, 14)
    for seed in range(40):
        bay = random_bay(seed)
        for r10 in (10, 14, 19):
            for order in (R.bay_order(bay), R.johnson(bay)):
                seq = R.play(bay, order)
                assert R.time10(seq, r10) == simulate_time10(seq, r10) == 10 * bay.containers - (20 - r10) * R.duals_of(bay, order)


# ---------------------------------------------------------------------------------------------------
# Unabhängige Prüfung
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("seq,expected", [
    ((("U", 0), ("U", 0), ("L", 0)), ()),
    ((("U", 0), ("L", 0)), ("Entladen", "Reihenfolge")),                       # ein Container bleibt drin, und der Stapel war beim Laden noch nicht leer
    ((("U", 0), ("U", 0), ("U", 0), ("L", 0)), ("Entladen",)),                  # zu oft gelöscht
    ((("U", 0), ("U", 0)), ("Beladen",)),                                      # nichts geladen
    ((("U", 0), ("U", 0), ("L", 0), ("L", 0)), ("Beladen",)),                   # zu oft geladen
    ((("U", 0), ("L", 0), ("U", 0)), ("Reihenfolge",)),                         # geladen, bevor der Stapel leer ist
    ((("U", 0), ("D", 0, 0)), ("Reihenfolge", "Selbst")),                       # Doppelspiel in den eigenen, noch nicht leeren Stapel
    ((("U", 5), ("U", 0), ("U", 0), ("L", 0)), ("Entladen",)),                  # unbekannter Stapel
    ((("U", 0), ("U", 0), ("L", 7)), ("Beladen",)),                             # unbekannter Ladestapel
])
def test_verify_flags_each_error_class(seq, expected):
    bay = bay_of([2], [1])
    assert R.verify(bay, seq) == expected


def test_verify_accepts_a_dual_cycle_into_an_already_empty_stack_and_rejects_the_same_cycle_before():
    bay2 = bay_of([1, 1], [1, 0])
    assert R.verify(bay2, (("U", 0), ("D", 1, 0))) == ()
    assert R.verify(bay2, (("D", 1, 0), ("U", 0))) == ("Reihenfolge",)             # Stapel 0 war noch nicht leer, als das Doppelspiel lud


# ---------------------------------------------------------------------------------------------------
# Reihenfolgen
# ---------------------------------------------------------------------------------------------------
def test_johnson_order_groups_and_tie_breaks():
    bay = bay_of([3, 1, 4, 2, 2], [1, 2, 2, 5, 2])
    # u <= l: Stapel 1 (1 <= 2), 3 (2 <= 5), 4 (2 <= 2) aufsteigend nach u (Gleichstand: Nummer) = 1, 3, 4; u > l: Stapel 0 (3 > 1), 2 (4 > 2) absteigend nach l = 2, 0
    assert R.johnson(bay) == (1, 3, 4, 2, 0)
    assert [R.johnson_group(bay, i) for i in range(5)] == [2, 1, 2, 1, 1]


def test_short_first_and_largest_first_are_sorted_with_stack_number_as_tie_break():
    bay = bay_of([2, 1, 2, 0], [0, 0, 0, 0])
    assert R.short_first(bay) == (3, 1, 0, 2) and R.largest_first(bay) == (0, 2, 1, 3) and R.bay_order(bay) == (0, 1, 2, 3)


@pytest.mark.parametrize("seed", range(200))
def test_johnson_equals_the_best_block_order_by_brute_force(seed):
    bay = tiny_bay(seed, n_stacks=6, max_count=6)
    assert R.cycles_of(bay, R.johnson(bay)) == R.brute_force(bay) == min(R.cycles_of(bay, p) for p in itertools.permutations(range(6)))


@pytest.mark.parametrize("seed", range(60))
def test_johnson_reaches_the_true_optimum_of_the_crane_model_without_the_block_assumption(seed):
    """Zustandssuche über alle Spielfolgen (auch teilweises Löschen mehrerer Stapel): das Optimum ist dasselbe wie der beste Block."""
    bay = tiny_bay(seed, n_stacks=4, max_count=3)
    assert R.cycles_of(bay, R.johnson(bay)) == true_optimum(bay)


def test_the_tiny_comparison_is_not_vacuous():
    gains = [len(R.play_none(tiny_bay(s))) - R.cycles_of(tiny_bay(s), R.johnson(tiny_bay(s))) for s in range(60)]
    assert sum(1 for g in gains if g > 0) >= 40 and sum(1 for s in range(60) if R.cycles_of(tiny_bay(s), R.johnson(tiny_bay(s))) > R.lower_bound(tiny_bay(s))) >= 3


def test_no_order_is_better_than_johnson_and_the_bound_holds():
    for seed in range(200):
        bay = random_bay(seed, max_stacks=12)
        j = R.cycles_of(bay, R.johnson(bay))
        for name in ("bay", "short", "largest"):
            assert R.cycles_of(bay, ORDERS[name](bay)) >= j
        assert j >= R.lower_bound(bay) == max(bay.unloads, bay.loads)
        assert j <= bay.containers                                                          # nie schlechter als ohne Doppelspiel


def test_measured_facts_on_ten_stacks():
    """Gemessen (10 Stapel, 6 Lagen, 50/50, 200 Bays): Johnson < kurze Entladung < Bay-Reihenfolge, 'größte zuerst' ist schlechter als die Bay-Reihenfolge."""
    bays = [SC.make_bay(10, 6, 50, 50, s) for s in range(200)]
    mean = {n: statistics.fmean(R.cycles_of(b, ORDERS[n](b)) for b in bays) for n in ORDERS}
    assert mean["johnson"] < mean["short"] < mean["bay"] < mean["largest"]


def test_brute_force_refuses_large_bays():
    with pytest.raises(ValueError):
        R.brute_force(SC.make_bay(C.BRUTE_FORCE_MAX_STACKS + 1, 3, 50, 50, 1))
    assert R.brute_force(SC.make_bay(C.BRUTE_FORCE_MAX_STACKS, 3, 50, 50, 1)) >= 1


# ---------------------------------------------------------------------------------------------------
# Randfälle
# ---------------------------------------------------------------------------------------------------
def test_only_unloading_and_only_loading_gain_nothing():
    for bay in (bay_of([3, 2], [0, 0]), bay_of([0, 0], [3, 2])):
        assert R.cycles_of(bay, R.johnson(bay)) == bay.containers == len(R.play_none(bay)) and R.duals_of(bay, R.johnson(bay)) == 0


def test_single_stack_cannot_pair_with_itself():
    bay = bay_of([3], [3])
    assert R.cycles_of(bay, (0,)) == 6 and R.duals_of(bay, (0,)) == 0 and R.verify(bay, R.play(bay, (0,))) == ()


def test_two_symmetric_stacks_pair_completely_except_the_first_unloads():
    bay = bay_of([2, 2], [2, 2])
    seq = R.play(bay, (0, 1))
    assert R.counts(seq) == (2, 2, 2) and len(seq) == 6                                     # erst 2 Einzel-Entladen, dann 2 Doppelspiele, dann 2 Einzel-Laden


def test_lower_bound_and_time_lower_bound_are_attained_only_when_everything_can_pair():
    bay = bay_of([0, 3], [3, 0])
    assert R.lower_bound(bay) == 3 and R.cycles_of(bay, R.johnson(bay)) == 3
    assert R.time_lower10(bay, 14) == 10 * (6 - 6) + 14 * 3 == 42
    assert R.time_lower10(bay_of([4], [0]), 14) == 40


def test_time_is_minimised_by_the_same_order_for_every_ratio_below_two():
    for seed in range(60):
        bay = random_bay(seed, max_stacks=8)
        orders = [R.bay_order(bay), R.short_first(bay), R.largest_first(bay), R.johnson(bay)]
        for r10 in (10, 14, 19):
            times = [R.time10(R.play(bay, o), r10) for o in orders]
            assert times[3] == min(times)
