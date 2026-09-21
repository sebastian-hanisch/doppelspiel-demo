"""Abnahmekriterien der Presets (Plan, Abschnitt 7): Welche Geschichte erzählt jedes Beispielszenario, und woran erkennt man, dass sie trägt?

Einzige Quelle für `tools/tune_presets.py` (Abstimmung) und `tests/test_preset_stories.py` (Abnahme). Jedes Kriterium ist eine Aussage über ein Tupel von `ListResult`s (dsp_evaluation):
über viele Bays die Aussage im MITTEL (`criteria`), über den EINEN Bay des Presets die Aussage an diesem Bay (`holds`). So wird dieselbe Geschichte an der Grundgesamtheit UND am gewählten Bay
geprüft: das Preset soll typisch sein, nicht der schönste Einzelfall. Alles ist ganzzahlig und deterministisch (kein Löser, keine Zeitgrenze): die Kriterien sind CI-robust."""

import dsp_constants as C
import dsp_evaluation as E

N_, B_, S_, J_ = C.STRAT_NONE, C.STRAT_BAY, C.STRAT_SHORT, C.STRAT_JOHNSON

# Kennzahlen, an denen 'typisch' gemessen wird: (Preset, Verfahren)
TYPICAL = (("Nur Löschen", J_), ("Ausgewogen", B_), ("Ausgewogen", J_), ("Viel Laden", J_), ("Wenig Laden", B_), ("Wenig Laden", J_), ("Große Bays", B_), ("Große Bays", J_))


def cycle_saving(r, key=J_):
    """Ersparnis der Spiele in % gegen 'Ohne Doppelspiel' für einen Bay."""
    return 100.0 * (r.cycles[N_] - r.cycles[key]) / r.cycles[N_]


def time_saving(r, key=J_):
    return 100.0 * (r.time10[N_] - r.time10[key]) / r.time10[N_]


def _share(results, pred):
    return sum(1 for r in results if pred(r)) / len(results)


def criteria(name, results):
    """Mittelwert-Kriterien über viele Bays. Rückgabe: Liste (erfüllt, Text)."""
    cyc = E.mean_cycle_saving_pct(results, J_)
    tim = E.mean_saving_pct(results, J_)
    at_bound = E.at_bound_share(results, J_)
    if name == "Nur Löschen":
        return [(cyc <= 20, f"Johnson spart <= 20 % der Spiele: {cyc:.1f} %"),
                (at_bound >= 0.95, f"Johnson liegt an >= 95 % der Bays auf der unteren Schranke: {at_bound * 100:.0f} %")]
    if name == "Ausgewogen":
        beats = _share(results, lambda r: r.cycles[J_] < r.cycles[B_])
        return [(cyc >= 40, f"Johnson spart >= 40 % der Spiele: {cyc:.1f} %"),
                (tim >= 20, f"Johnson spart >= 20 % Kranzeit: {tim:.1f} %"),
                (beats >= 0.75, f"Johnson braucht an >= 75 % der Bays weniger Spiele als die Bay-Reihenfolge: {beats * 100:.0f} %")]
    if name == "Viel Laden":
        same = _share(results, lambda r: r.cycles[J_] == r.cycles[S_])
        return [(same >= 0.9, f"Johnson = Kurze Entladung an >= 90 % der Bays: {same * 100:.0f} %"),
                (tim >= 20, f"Johnson spart >= 20 % Kranzeit: {tim:.1f} %")]
    if name == "Wenig Laden":
        beats = _share(results, lambda r: r.cycles[J_] < r.cycles[B_])
        lead = tim - E.mean_saving_pct(results, B_)
        return [(beats >= 0.6, f"Johnson braucht an >= 60 % der Bays weniger Spiele als die Bay-Reihenfolge: {beats * 100:.0f} %"),
                (lead >= 1.5, f"Kranzeit-Vorsprung von Johnson gegen die Bay-Reihenfolge >= 1,5 Punkte: {lead:.2f}"),
                (at_bound >= 0.85, f"Johnson liegt an >= 85 % der Bays auf der unteren Schranke: {at_bound * 100:.0f} %")]
    if name == "Große Bays":
        return [(cyc >= 44, f"Johnson spart >= 44 % der Spiele: {cyc:.1f} %"),
                (at_bound <= 0.2, f"Johnson liegt an <= 20 % der Bays auf der unteren Schranke: {at_bound * 100:.0f} %")]
    raise KeyError(name)


def holds(name, r):
    """Gilt die Geschichte an dem EINEN Bay (`ListResult`), den das Preset zeigt?"""
    c = r.cycles
    if name == "Nur Löschen":
        return c[J_] == r.bound and cycle_saving(r) <= 25
    if name == "Ausgewogen":
        return c[J_] < c[B_] and cycle_saving(r) >= 40
    if name == "Viel Laden":
        return c[J_] == c[S_] and time_saving(r) >= 18
    if name == "Wenig Laden":
        return c[J_] < c[B_] and c[J_] == r.bound
    if name == "Große Bays":
        return cycle_saving(r) >= 42 and c[J_] > r.bound
    raise KeyError(name)


def key_values(name, results):
    """Die Kennzahlen dieses Presets aus TYPICAL als {Verfahren: Mittel der Spiele}."""
    return {k: E.mean_cycles(results, k) for n, k in TYPICAL if n == name}
