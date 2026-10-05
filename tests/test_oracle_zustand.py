"""Orakel auf anderem Rechenweg: Zustandssuche über ALLE Spielfolgen mit Zeitgewicht (Einzelspiel 10, Doppelspiel r10), Rückwärtsrekursion über die verbleibenden Zahlen je Stapel.

Johnson (Spielzahl und Kranzeit), die gierige Paarung `play`, die Kurzform `cycles_of` und die untere Schranke werden gegen dieses Optimum geprüft, für jedes Verhältnis 1,0 bis 1,9."""
import itertools
import random
from functools import lru_cache

import pytest

import dsp_rules as R
import dsp_scenario as SC


def optimum(u, l, r10):
    """(kleinste Zeit in Zehnteln, kleinste Spielzahl bei dieser Zeit) über alle Spielfolgen."""
    n = len(u)

    @lru_cache(maxsize=None)
    def f(state):
        ru, rl = state[:n], state[n:]
        if not any(state):
            return (0, 0)
        best = None
        for k in range(n):
            if ru[k]:
                nu = ru[:k] + (ru[k] - 1,) + ru[k + 1:]
                options = [(10, nu, rl)]
                options += [(r10, nu, rl[:j] + (rl[j] - 1,) + rl[j + 1:]) for j in range(n) if j != k and ru[j] == 0 and rl[j]]
                for cost, a, b in options:
                    c = f(a + b)
                    cand = (c[0] + cost, c[1] + 1)
                    best = cand if best is None or cand < best else best
            elif rl[k]:
                c = f(ru + rl[:k] + (rl[k] - 1,) + rl[k + 1:])
                cand = (c[0] + 10, c[1] + 1)
                best = cand if best is None or cand < best else best
        return best

    return f(tuple(u) + tuple(l))


def test_hand_example_for_the_state_search():
    # zwei Stapel: u=(1,0), l=(0,1): löschen aus 0, dann laden in 1 geht im Doppelspiel zugleich nur, wenn 1 schon leer ist (u1=0): ein Doppelspiel
    assert optimum((1, 0), (0, 1), 14) == (14, 1)
    # ein Stapel kann nicht mit sich selbst paaren: zwei Spiele
    assert optimum((1,), (1,), 14) == (20, 2)


@pytest.mark.parametrize("seed", range(60))
def test_johnson_is_the_true_optimum_in_cycles_and_in_time_for_every_ratio(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 5)
    top = 3 if n <= 4 else 2
    u = tuple(rng.randint(0, top) for _ in range(n))
    l = tuple(rng.randint(0, top) for _ in range(n))
    if not sum(u) + sum(l):
        u = (1,) + u[1:]
    bay = SC.custom_bay(u, l)
    r10 = rng.choice([10, 12, 14, 16, 19])
    best_time, best_cycles = optimum(u, l, r10)
    order = R.johnson(bay)
    seq = R.play(bay, order)
    assert R.verify(bay, seq) == ()
    assert (R.time10(seq, r10), len(seq)) == (best_time, best_cycles) == (R.time10(seq, r10), R.cycles_of(bay, order))
    assert R.lower_bound(bay) <= best_cycles and R.time_lower10(bay, r10) <= best_time
    for p in itertools.islice(itertools.permutations(range(n)), 60):
        s = R.play(bay, p)
        assert len(s) == R.cycles_of(bay, p) >= best_cycles and R.time10(s, r10) >= best_time


@pytest.mark.parametrize("text", ["--3", "1_0", "+3", "3.5", "٣", "1e2"])
def test_parse_counts_rejects_non_integers_with_the_german_message(text):
    with pytest.raises(ValueError, match="keine ganze Zahl"):
        SC.parse_counts(text)
