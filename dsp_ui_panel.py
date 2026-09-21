"""Wiederverwendbare Panels: je Verfahren ein Tab im Methodenvergleich und der selbstständige Johnson-Tab (mit Gegenprobe)."""

import math

import streamlit as st

import dsp_constants as C
import dsp_evaluation as E
import dsp_rules as R
from dsp_visualization import order_figure, sequence_figure

VIOLATION_TEXT = {
    "Entladen": "Nicht jeder Container wird genau einmal gelöscht",
    "Beladen": "Nicht jeder Container wird genau einmal geladen",
    "Reihenfolge": "In einen Stapel wird geladen, bevor er leer ist",
    "Selbst": "Ein Doppelspiel lädt in den Stapel, aus dem es löscht",
}


def render_strategy_panel(prefix, outcome, outcomes, bay, ratio10):
    """Beschreibung, Kennzahlen (2 x 2), Spielfolge und Stapel eines Verfahrens. Deltas lesen sich immer als "dieses Verfahren minus Ohne Doppelspiel" (weniger Spiele ist besser).
    `prefix` macht die Widget-Schlüssel eindeutig."""
    ref = E.outcome_of(outcomes, C.BASELINE)
    st.markdown(C.STRATEGY_DESCRIPTIONS[outcome.key])
    is_ref = outcome.key == ref.key
    top, bottom = st.columns(2), st.columns(2)                      # 2 x 2: vier Spalten schneiden die Namen in schmalen Tabs ab
    m1, m2, m3, m4 = top + bottom
    diff = outcome.cycles - ref.cycles
    m1.metric("Kranspiele", f"{outcome.cycles}", delta=None if is_ref else f"{diff:+d}", delta_color="off" if diff == 0 else "inverse",
              help="Einzelspiele plus Doppelspiele. Weniger ist besser; untere Schranke: " + str(R.lower_bound(bay)) + ".")
    m2.metric("Doppelspiele", f"{outcome.duals}", help="Spiele, die löschen und laden zugleich. Höchstens min(zu löschen, zu laden).")
    m3.metric("Kranzeit", f"{E.minutes(outcome.time10):.0f} min", help=f"Einzelspiel {C.SINGLE_CYCLE_MINUTES:g} min, Doppelspiel {ratio10 / 10:g} Einzelspiele (Annahme).")
    m4.metric("Zeit gespart", f"{E.saving_pct(outcome, ref):.0f} %", help="Kranzeit gegen 'Ohne Doppelspiel'.")
    if not outcome.valid:
        st.warning("⚠️ " + "; ".join(VIOLATION_TEXT.get(v, v) for v in outcome.violations) + ".")
    st.plotly_chart(sequence_figure(bay, outcome.seq, ratio10), width="stretch", key=f"{prefix}_sequence_chart")
    st.plotly_chart(order_figure(bay, outcome.order), width="stretch", key=f"{prefix}_order_chart")


def render_johnson_panel(prefix, outcome, outcomes, bay, ratio10):
    """Johnson-Tab: Kennzahlen wie die anderen Tabs, dazu Gruppe je Stapel und die Gegenprobe (alle Reihenfolgen durchprobiert, wenn der Bay klein genug ist)."""
    render_strategy_panel(prefix, outcome, outcomes, bay, ratio10)
    rows = [{"Position": pos + 1, "Stapel": k + 1, "zu löschen": bay.u[k], "zu laden": bay.l[k], "Gruppe": R.johnson_group(bay, k)} for pos, k in enumerate(outcome.order)]
    st.markdown("**Reihenfolge nach der Johnson-Regel** (Gruppe 1: zu löschen ≤ zu laden, aufsteigend nach der Löschzahl; Gruppe 2: zu löschen > zu laden, absteigend nach der Ladezahl)")
    st.dataframe(rows, width="stretch", hide_index=True)
    if bay.n_stacks <= C.BRUTE_FORCE_MAX_STACKS:
        best = R.brute_force(bay)
        if best == outcome.cycles:
            st.success(f"✅ Gegenprobe: alle {math.factorial(bay.n_stacks)} Reihenfolgen durchprobiert, keine braucht weniger als {best} Spiele.")
        else:
            st.error(f"⛔ Gegenprobe fehlgeschlagen: eine andere Reihenfolge braucht nur {best} Spiele.")
    else:
        st.caption(f"Die Gegenprobe (alle Reihenfolgen durchprobieren) gibt es bis {C.BRUTE_FORCE_MAX_STACKS} Stapel; hier sind es {bay.n_stacks}. Die Johnson-Regel ist bewiesen optimal.")

