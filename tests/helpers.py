"""Testhilfen: unabhängige Vergleichsimplementierungen (echtes Optimum durch Zustandssuche, Spiel-für-Spiel-Simulation) und Bay-Generatoren."""
import functools
import random

import dsp_scenario as SC


def random_bay(seed, max_stacks=20, max_tiers=10):
    """Zufälliger Bay innerhalb der Reglergrenzen der App."""
    rng = random.Random(seed)
    return SC.make_bay(rng.randint(4, max_stacks), rng.randint(2, max_tiers), rng.choice(range(10, 101, 10)), rng.choice(range(10, 101, 10)), rng.randint(0, 9999))


def tiny_bay(seed, n_stacks=4, max_count=3):
    """Winziger Bay (wenige Stapel, kleine Zahlen) für die Zustandssuche."""
    rng = random.Random(seed)
    u = [rng.randint(0, max_count) for _ in range(n_stacks)]
    l = [rng.randint(0, max_count) for _ in range(n_stacks)]
    if sum(u) + sum(l) == 0:
        u[0] = 1
    return SC.Bay(tuple(u), tuple(l))


def true_optimum(bay):
    """Kleinste Spielzahl im ECHTEN Kranmodell, ohne Annahme über Blöcke: Zustand = (gelöscht je Stapel, geladen je Stapel); ein Spiel ist Löschen, Laden oder beides zugleich
    (Laden nur in einen Stapel, der schon vor diesem Spiel leer war, und nie in den Stapel, aus dem gelöscht wird). Unabhängig von der Blockreihenfolge und der gierigen Paarung."""
    n = bay.n_stacks

    @functools.lru_cache(maxsize=None)
    def best(unloaded, loaded):
        if unloaded == bay.u and loaded == bay.l:
            return 0
        opts = []
        can_u = [k for k in range(n) if unloaded[k] < bay.u[k]]
        can_l = [j for j in range(n) if unloaded[j] == bay.u[j] and loaded[j] < bay.l[j]]
        for k in can_u:
            nu = unloaded[:k] + (unloaded[k] + 1,) + unloaded[k + 1:]
            opts.append(1 + best(nu, loaded))
            for j in can_l:
                if j != k:
                    nl = loaded[:j] + (loaded[j] + 1,) + loaded[j + 1:]
                    opts.append(1 + best(nu, nl))
        for j in can_l:
            nl = loaded[:j] + (loaded[j] + 1,) + loaded[j + 1:]
            opts.append(1 + best(unloaded, nl))
        return min(opts)

    return best((0,) * n, (0,) * n)


def simulate_time10(seq, ratio10):
    """Kranzeit Spiel für Spiel (unabhängig von dsp_rules.time10): Einzelspiel 10, Doppelspiel ratio10."""
    total = 0
    for c in seq:
        total += ratio10 if len(c) == 3 else 10
    return total
