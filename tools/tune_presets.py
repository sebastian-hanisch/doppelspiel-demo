"""Preset-Abstimmung per Sweep: traegt die Geschichte jedes Presets im MITTEL ueber viele Bays, und an dem einen Bay, den das Preset zeigt?

Aufruf (im Projektordner): ./venv/Scripts/python.exe tools/tune_presets.py <modus>
  population   Grundgesamtheit (Seeds 0-199): Mittelwert-Kriterien aller Presets
  seeds        je Seed 200..699: welche Presets tragen an diesem Bay, Abstand zum Median der Kennzahlen; nennt die besten gemeinsamen Seeds

Grundsaetze (aus den Hafen-Demos): den Seed nicht nach dem schoensten Einzelfall waehlen, sondern nahe am MEDIAN; der Preset-Seed liegt ausserhalb der Grundgesamtheit (Seeds ab 200);
alle Presets teilen sich EINE Bay-Nummer. Alles ist ganzzahlig und deterministisch, kein Loeser: die Ergebnisse haengen nicht vom Rechner ab."""
import math
import statistics
import sys

sys.path.insert(0, ".")
import dsp_constants as C
import dsp_evaluation as E
import dsp_stories as ST

NAMES = list(C.PRESETS)
SEEDS = range(C.SAMPLE_BAYS, C.SAMPLE_BAYS + 500)
R10 = E.ratio10(C.RATIO_DEFAULT)


def _run(name, seed):
    p = C.PRESETS[name]
    return E.run_bay(p["n_stacks"], p["tiers"], p["unload_pct"], p["load_pct"], E.ratio10(p["ratio"]), seed)


def cmd_population():
    for name in NAMES:
        p = C.PRESETS[name]
        res = E.sample(p["n_stacks"], p["tiers"], p["unload_pct"], p["load_pct"], E.ratio10(p["ratio"]))
        print(f"\n### {name}")
        for ok, text in ST.criteria(name, res):
            print(("  OK   " if ok else "  FAIL ") + text)
        print("  Kennzahlen:", {k: round(v, 2) for k, v in ST.key_values(name, res).items()})


def _median(table):
    return {(n, k): statistics.median(table[n][s].cycles[k] for s in table[n]) for n, k in ST.TYPICAL}


def _score(table, med, seed):
    return sum(abs(math.log(table[n][seed].cycles[k] + 0.5) - math.log(med[(n, k)] + 0.5)) for n, k in ST.TYPICAL)


def cmd_seeds():
    table = {n: {s: _run(n, s) for s in SEEDS} for n in NAMES}
    med = _median(table)
    for name in NAMES:
        print(f"{name}: traegt an {sum(ST.holds(name, table[name][s]) for s in SEEDS)} von {len(SEEDS)} Bays")
    allgood = sorted((s for s in SEEDS if all(ST.holds(n, table[n][s]) for n in NAMES)), key=lambda s: _score(table, med, s))
    print("\nalle fuenf tragen an:", allgood[:12], f"({len(allgood)} von {len(SEEDS)})")
    for s in allgood[:6]:
        print(f"  seed {s:3d} | Abstand zum Median {_score(table, med, s):.2f} | " + ", ".join(f"{n}: " + "/".join(str(table[n][s].cycles[k]) for k in C.STRATEGY_KEYS) + f" (Schranke {table[n][s].bound})" for n in NAMES))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "population"
    {"population": cmd_population, "seeds": cmd_seeds}.get(mode, lambda: sys.exit(__doc__))()
