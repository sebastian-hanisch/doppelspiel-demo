"""Spielfolgen und Reihenfolgen: wie viele Kranspiele braucht ein Bay, und in welcher Reihenfolge der Stapel?

Eine Spielfolge ist ein Tupel von Spielen: ("U", k) Einzelspiel Entladen aus Stapel k, ("L", j) Einzelspiel Beladen von Stapel j, ("D", k, j) Doppelspiel: aus Stapel k löschen und in
Stapel j laden (j war schon vollständig geleert, j != k). Eine Reihenfolge ist eine Permutation der Stapel: Sie bestimmt, in welcher Folge die Stapel ganz geleert werden. Zu einer
Reihenfolge wird gierig gepaart. Die Spielzahl ist genau die Laufzeit eines Zwei-Maschinen-Flow-Shops (Löschen, Laden); darum ist die Johnson-Regel optimal (Goodchild und Daganzo 2006)."""

import itertools
from collections import deque

import dsp_constants as C


# ---------------------------------------------------------------------------------------------------
# Spielfolgen
# ---------------------------------------------------------------------------------------------------
def play(bay, order):
    """Spielfolge zu einer Reihenfolge: Stapel für Stapel löschen; jedes Löschspiel nimmt, wenn ein Stapel schon leer ist und noch Ladung offen hat, ein Ladespiel mit (Doppelspiel,
    ältester leerer Stapel zuerst). Nach dem Löschen bleibende Ladung geht in Einzelspielen."""
    avail = deque()                                   # [Stapel, noch zu ladende Container] der schon geleerten Stapel
    seq = []
    for k in order:
        for _ in range(bay.u[k]):
            if avail:
                j = avail[0][0]
                avail[0][1] -= 1
                if avail[0][1] == 0:
                    avail.popleft()
                seq.append(("D", k, j))
            else:
                seq.append(("U", k))
        if bay.l[k]:
            avail.append([k, bay.l[k]])
    for j, n in avail:
        seq.extend([("L", j)] * n)
    return tuple(seq)


def play_none(bay):
    """Ohne Doppelspiel: erst alle Container löschen, dann alle laden, jedes Spiel einzeln."""
    return tuple(("U", k) for k in range(bay.n_stacks) for _ in range(bay.u[k])) + tuple(("L", j) for j in range(bay.n_stacks) for _ in range(bay.l[j]))


def counts(seq):
    """(Einzelspiele Entladen, Einzelspiele Beladen, Doppelspiele)."""
    return sum(1 for c in seq if c[0] == "U"), sum(1 for c in seq if c[0] == "L"), sum(1 for c in seq if c[0] == "D")


def time10(seq, ratio10):
    """Kranzeit in Zehnteln eines Einzelspiels: Einzelspiel 10, Doppelspiel ratio10 (ganzzahlig)."""
    singles = sum(1 for c in seq if c[0] != "D")
    duals = len(seq) - singles
    return 10 * singles + ratio10 * duals


def cycles_of(bay, order):
    """Spielzahl einer Reihenfolge ohne die Folge zu bauen (gleiche gierige Paarung wie `play`)."""
    avail, singles_u, dual = 0, 0, 0
    for k in order:
        d = min(avail, bay.u[k])
        dual += d
        singles_u += bay.u[k] - d
        avail += bay.l[k] - d
    return singles_u + dual + avail


def duals_of(bay, order):
    avail, dual = 0, 0
    for k in order:
        d = min(avail, bay.u[k])
        dual += d
        avail += bay.l[k] - d
    return dual


# ---------------------------------------------------------------------------------------------------
# Unabhängige Prüfung einer Spielfolge
# ---------------------------------------------------------------------------------------------------
def verify(bay, seq):
    """Verletzte Bedingungen einer Spielfolge: "Entladen" (falsche Zahl je Stapel), "Beladen" (falsche Zahl je Stapel), "Reihenfolge" (in einen Stapel geladen, der noch nicht leer ist),
    "Selbst" (Doppelspiel lädt in den Stapel, aus dem es löscht). Leeres Tupel = zulässig."""
    unloaded, loaded = [0] * bay.n_stacks, [0] * bay.n_stacks
    bad = set()
    for c in seq:
        if c[0] in ("U", "D"):
            k = c[1]
            if not 0 <= k < bay.n_stacks or unloaded[k] >= bay.u[k]:
                bad.add("Entladen")
                continue
        if c[0] in ("L", "D"):
            j = c[-1]
            if not 0 <= j < bay.n_stacks:
                bad.add("Beladen")
                continue
            if c[0] == "D" and c[1] == j:
                bad.add("Selbst")
            if unloaded[j] < bay.u[j]:
                bad.add("Reihenfolge")
            if loaded[j] >= bay.l[j]:
                bad.add("Beladen")
                continue
            loaded[j] += 1
        if c[0] in ("U", "D"):
            unloaded[c[1]] += 1
    if unloaded != list(bay.u):
        bad.add("Entladen")
    if loaded != list(bay.l):
        bad.add("Beladen")
    return tuple(sorted(bad))


# ---------------------------------------------------------------------------------------------------
# Reihenfolgen
# ---------------------------------------------------------------------------------------------------
def bay_order(bay):
    return tuple(range(bay.n_stacks))


def short_first(bay):
    """Aufsteigend nach der Löschzahl (bei Gleichstand nach der Stapelnummer)."""
    return tuple(sorted(range(bay.n_stacks), key=lambda i: (bay.u[i], i)))


def largest_first(bay):
    """Absteigend nach der Löschzahl: schlechter als die Bay-Reihenfolge (nur als Vergleichszeile)."""
    return tuple(sorted(range(bay.n_stacks), key=lambda i: (-bay.u[i], i)))


def johnson(bay):
    """Johnson-Regel für den Zwei-Maschinen-Flow-Shop: erst die Stapel mit u <= l aufsteigend nach u, dann die mit u > l absteigend nach l (Gleichstand: Stapelnummer)."""
    idx = range(bay.n_stacks)
    first = sorted((i for i in idx if bay.u[i] <= bay.l[i]), key=lambda i: (bay.u[i], i))
    last = sorted((i for i in idx if bay.u[i] > bay.l[i]), key=lambda i: (-bay.l[i], i))
    return tuple(first + last)


def johnson_group(bay, i):
    """1 = erste Gruppe (u <= l), 2 = zweite Gruppe (u > l)."""
    return 1 if bay.u[i] <= bay.l[i] else 2


def brute_force(bay):
    """Kleinste Spielzahl über alle Reihenfolgen (Gegenprobe, nur für wenige Stapel)."""
    if bay.n_stacks > C.BRUTE_FORCE_MAX_STACKS:
        raise ValueError("zu viele Stapel für die Gegenprobe")
    return min(cycles_of(bay, p) for p in itertools.permutations(range(bay.n_stacks)))


def lower_bound(bay):
    """Untere Schranke der Spiele: jedes Spiel löscht höchstens einen und lädt höchstens einen Container."""
    return max(bay.unloads, bay.loads)


def time_lower10(bay, ratio10):
    """Untere Schranke der Kranzeit (Zehntel Einzelspiele): höchstens min(U, L) Doppelspiele."""
    d = min(bay.unloads, bay.loads)
    return 10 * (bay.containers - 2 * d) + ratio10 * d
