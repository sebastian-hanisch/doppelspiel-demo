"""Bay aus den Reglern: je Stapel die Zahl der zu löschenden und der zu ladenden Container. Ganzzahlig, deterministisch aus dem Seed."""

import random
from dataclasses import dataclass

import dsp_constants as C


@dataclass(frozen=True)
class Bay:
    u: tuple                # zu löschende Container je Stapel
    l: tuple                # zu ladende Container je Stapel

    @property
    def n_stacks(self):
        return len(self.u)

    @property
    def unloads(self):
        return sum(self.u)

    @property
    def loads(self):
        return sum(self.l)

    @property
    def containers(self):
        return self.unloads + self.loads


def make_bay(n_stacks, tiers, unload_pct, load_pct, seed):
    """Je Stapel und Lage wird mit der Wahrscheinlichkeit unload_pct % ein Container gelöscht und mit load_pct % einer geladen (ganzzahlige Ziehung 0..99). Ein Bay ohne jeden Container
    bekommt einen Container zum Löschen im ersten Stapel (sonst gäbe es nichts zu vergleichen)."""
    if n_stacks < 1 or tiers < 1:
        raise ValueError("Stapel und Lagen müssen mindestens 1 sein")
    if not 0 <= unload_pct <= 100 or not 0 <= load_pct <= 100:
        raise ValueError("Anteile in 0 bis 100")
    rng = random.Random(seed)
    u = [sum(1 for _ in range(tiers) if rng.randrange(100) < unload_pct) for _ in range(n_stacks)]
    l = [sum(1 for _ in range(tiers) if rng.randrange(100) < load_pct) for _ in range(n_stacks)]
    if sum(u) + sum(l) == 0:
        u[0] = 1
    return Bay(tuple(u), tuple(l))


def custom_bay(u, l):
    """Eigenen Bay prüfen: gleich lange Listen, ganze Zahlen >= 0, mindestens ein Container."""
    u, l = tuple(u), tuple(l)
    if not u or len(u) != len(l):
        raise ValueError("Löschzahlen und Ladezahlen brauchen gleich viele Stapel (mindestens einen)")
    if any(not isinstance(x, int) or isinstance(x, bool) or x < 0 for x in u + l):
        raise ValueError("Zahlen müssen ganz und nicht negativ sein")
    if sum(u) + sum(l) == 0:
        raise ValueError("mindestens ein Container")
    return Bay(u, l)


def parse_counts(text):
    """'3, 0, 5' -> (3, 0, 5); Komma, Semikolon oder Leerzeichen als Trenner. Nicht ganze Zahlen lösen ValueError aus."""
    parts = [p for p in text.replace(";", ",").replace(" ", ",").split(",") if p != ""]
    out = []
    for p in parts:
        if not p.lstrip("-").isdigit():
            raise ValueError(f"'{p}' ist keine ganze Zahl")
        out.append(int(p))
    return tuple(out)
