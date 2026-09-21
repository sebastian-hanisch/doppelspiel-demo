"""
Doppelspiel – interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zusatz zur Hafen-Linie (Kran): Ein Containerkran löscht und lädt meist nacheinander und fährt dabei oft leer zurück. Beim Doppelspiel setzt er nach dem Löschen gleich einen Container
auf das Schiff. Gezeigt wird, wie viel Kranzeit das spart und wie stark die Reihenfolge der Stapel eines Bays den Gewinn bestimmt (Johnson-Regel: beweisbar optimal, ohne Löser).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import dsp_constants as C
import dsp_evaluation as E
import dsp_rules as R
import dsp_scenario as SC
import dsp_visualization as V
from dsp_pdf_export import generate_dsp_pdf
from dsp_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, scenario_bay, SETTING_SPECS, sync_query_params)
from dsp_ui_panel import render_johnson_panel, render_strategy_panel

st.set_page_config(page_title="Doppelspiel – Sebastian Hanisch", layout="wide")

SCENARIO_KEYS = list(SETTING_SPECS)
N_, B_, S_, J_ = C.STRAT_NONE, C.STRAT_BAY, C.STRAT_SHORT, C.STRAT_JOHNSON
LABEL = C.STRATEGY_LABELS


@st.cache_data(show_spinner=False, max_entries=64)
def _compute_bay(key):
    """Bay und alle vier Verfahren."""
    n_stacks, tiers, unload_pct, load_pct, seed, r10 = key
    bay = scenario_bay(n_stacks, tiers, unload_pct, load_pct, seed)
    return bay, E.run_methods(bay, r10)


@st.cache_data(show_spinner=False, max_entries=16)
def _compute_sample(key):
    """Stichprobe (Seeds 0-199) und Kurve über den Beladeanteil, unabhängig vom eingestellten Seed."""
    n_stacks, tiers, unload_pct, load_pct, r10 = key
    return E.sample(n_stacks, tiers, unload_pct, load_pct, r10), E.curve_over_load(n_stacks, tiers, unload_pct, r10)


st.title("🏗️ Doppelspiel: Was bringt es, beim Löschen gleich zu laden?")
st.markdown(
    """
Ein Containerkran löscht und lädt meist nacheinander und fährt dabei oft leer zurück. Beim **Doppelspiel** setzt er nach dem Löschen gleich einen Container auf das Schiff: ein
**Einzelspiel** erledigt eine Aufgabe, ein **Doppelspiel** zwei. Geladen werden darf aber nur in einen Stapel, der schon leer ist; deshalb entscheidet die **Reihenfolge der Stapel**, wie
oft sich zwei Aufgaben paaren lassen. Die Demo zeigt, wie viel Kranzeit das spart und wie viel davon an der Reihenfolge hängt. Wie das Modell funktioniert, steht im Expander
"Wie funktioniert diese Demo?" weiter unten, die formale Herleitung im Expander "📐 Mathematische Formulierung".
"""
)

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = {
    "Nur Löschen": "Fast nichts zu laden: das Doppelspiel bringt wenig, und jede Reihenfolge erreicht die untere Schranke.",
    "Ausgewogen": "Löschen und Laden halten sich die Waage: der größte Gewinn, und die Reihenfolge entscheidet über einen Teil davon.",
    "Viel Laden": "Fast alles wird geladen: die einfache Regel „kurze Entladung zuerst“ ist schon so gut wie Johnson.",
    "Wenig Laden": "Wenig Ladung: die Reihenfolge entscheidet über einen großen Teil des Gewinns, und Johnson liegt fast immer auf der unteren Schranke.",
    "Große Bays": "Zwanzig Stapel: der Gewinn wächst mit der Stapelzahl, die untere Schranke wird aber nur noch selten erreicht.",
}
# Je Zeile drei Schaltflächen: bei fünf in einer Zeile werden die Namen in schmalen Fenstern abgeschnitten.
preset_names = list(C.PRESETS.keys())
for row in (preset_names[:3], preset_names[3:]):
    cols = st.columns(3)
    for col, name in zip(cols, row):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_stacks = st.slider("Stapel im Bay", *bounds("n_stacks_slider"), key="n_stacks_slider", help="Breite des Bays; je Stapel eine Löschzahl und eine Ladezahl. Die Gegenprobe (alle Reihenfolgen) gibt es bis 7 Stapel.")
    tiers = st.slider("Höhe (Lagen)", *bounds("tiers_slider"), key="tiers_slider", help="Größte Löschzahl und Ladezahl je Stapel.")
    unload_pct = st.slider("Entladeanteil (%)", *bounds("unload_slider"), step=C.PCT_STEP, format="%d%%", key="unload_slider", help="Erwarteter Anteil der Lagen, aus denen gelöscht wird.")
    load_pct = st.slider("Beladeanteil (%)", *bounds("load_slider"), step=C.PCT_STEP, format="%d%%", key="load_slider",
                         help="Erwarteter Anteil der Lagen, in die geladen wird. Der größte Gewinn liegt bei ausgewogenem Löschen und Laden.")
    ratio = st.slider("Doppelspiel kostet (Einzelspiele)", *bounds("ratio_slider"), step=0.1, format="%.1f", key="ratio_slider",
                      help="Annahme: ein Doppelspiel dauert so viele Einzelspiele. Ändert die Minuten, nicht die beste Reihenfolge (für jeden Wert unter 2 dieselbe).")
    seed = st.number_input("Seed des Bays", *bounds("seed_input"), key="seed_input", step=1, help="Bestimmt die Löschzahl und die Ladezahl je Stapel.")
    st.button("🎲 Neuer Bay", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Seed für den Bay.")

sync_query_params({key: st.session_state[key] for key in SCENARIO_KEYS})

r10 = E.ratio10(ratio)
bay_key = (int(n_stacks), int(tiers), int(unload_pct), int(load_pct), int(seed), r10)
sample_key = bay_key[:4] + (r10,)
bay, outcomes = _compute_bay(bay_key)
sample, curve = _compute_sample(sample_key)
by_key = {o.key: o for o in outcomes}
ref, best = by_key[N_], by_key[J_]
bound = R.lower_bound(bay)

# ---------------------------------------------------------------------------------------------------
# Hauptansicht
# ---------------------------------------------------------------------------------------------------
st.markdown("## 🎯 Wie viele Kranspiele braucht dieser Bay?")
st.caption(f"{bay.n_stacks} Stapel: {bay.unloads} Container zu löschen, {bay.loads} zu laden. Ein Einzelspiel dauert {C.SINGLE_CYCLE_MINUTES:g} min, ein Doppelspiel {r10 / 10:g} Einzelspiele (Annahme).")

metric_rows = [st.columns(2), st.columns(2)]                  # 2 x 2: vier Spalten schneiden die Namen bei 800 px ab
for col, o in zip(metric_rows[0] + metric_rows[1], outcomes):
    diff = o.cycles - ref.cycles
    help_txt = "Referenz für alle Vergleiche." if o.key == N_ else "Differenz: dieses Verfahren minus Ohne Doppelspiel (weniger Spiele ist besser)."
    if not o.valid:
        help_txt += " ⚠️ Die Spielfolge verletzt eine Bedingung (" + ", ".join(o.violations) + ")."
    col.metric(o.label, f"{o.cycles}" + ("" if o.valid else " ⚠️"), delta=None if o.key == N_ else f"{diff:+d}", delta_color="off" if diff == 0 else "inverse", help=help_txt)

gap = best.cycles - bound
st.info(
    f"ℹ️ Ohne Doppelspiel braucht dieser Bay **{ref.cycles} Spiele** ({E.minutes(ref.time10):.0f} min). In Bay-Reihenfolge sind es {by_key[B_].cycles}, mit der Johnson-Reihenfolge "
    f"**{best.cycles}** ({E.minutes(best.time10):.0f} min): **{ref.cycles - best.cycles} Spiele weniger, {E.saving_pct(best, ref):.0f} % Kranzeit gespart**. "
    + (f"Die untere Schranke ({bound}) ist erreicht: mehr geht nicht." if gap == 0 else f"Die untere Schranke liegt bei {bound}; Johnson liegt {gap} darüber: bewiesen das Beste, denn nicht jeder Stapel wird früh genug leer.")
)

st.markdown("#### 🔍 Blick auf den Bay")
right_key = st.radio("Rechts vergleichen mit", list(C.RIGHT_VIEW_KEYS), format_func=LABEL.get, key="view_radio", horizontal=True, help="Oben steht immer Ohne Doppelspiel.")
right = by_key[right_key]
for o, side in ((ref, "left"), (right, "right")):
    st.markdown(f"**{o.label}**: {o.cycles} Spiele, {o.duals} Doppelspiele, {E.minutes(o.time10):.0f} min")
    st.plotly_chart(V.sequence_figure(bay, o.seq, r10), width="stretch", key=f"sequence_chart_{side}")
st.markdown("**Stapel in der Reihenfolge des rechten Verfahrens**")
st.plotly_chart(V.order_figure(bay, right.order), width="stretch", key="order_chart")
st.caption("Ein Balken je Spiel: blau = Einzelspiel Entladen, orange = Einzelspiel Beladen, grün = Doppelspiel (breiter, weil es länger dauert). Darunter steht, aus welchem Stapel gelöscht wird, "
           "darüber, in welchen Stapel geladen wird (Farbe und Zahl = Stapel). Ein Stapel darf erst beladen werden, wenn er ganz geleert ist.")

pdf_slot = st.container()

st.markdown("---")

# ---------------------------------------------------------------------------------------------------
# Kernabschnitt
# ---------------------------------------------------------------------------------------------------
st.subheader("📐 Was ist die Reihenfolge wert?")
st.markdown(
    """
Kernfrage dieser Demo: Wie viel Kranzeit spart das Doppelspiel wirklich, und wie viel davon macht die **Reihenfolge der Stapel**? Ohne Plan (Bay-Reihenfolge) wird schon viel gepaart. Die
Faustregel **kurze Entladung zuerst** macht früh Stapel ladbar; die **Johnson-Regel** ist beweisbar die beste Reihenfolge. Der Gewinn hängt am Verhältnis von Laden und Löschen. Hier
live für Ihre Einstellungen gerechnet, **mit der Verteilung dazu**:
"""
)
g1, g2, g3 = st.columns(3)
g1.metric("Zu löschen", f"{bay.unloads}", help="Container, die im Bay gelöscht werden.")
g2.metric("Zu laden", f"{bay.loads}", help="Container, die im Bay geladen werden.")
g3.metric("Untere Schranke", f"{bound} Spiele", help="Jedes Spiel löscht höchstens einen und lädt höchstens einen Container: mindestens max(zu löschen, zu laden) Spiele.")


def _show_verdict(label, key, reference):
    v = E.verdict(sample, key, reference)
    d = E.distribution(sample, key, reference)
    if v.kind == "better":
        amount = f"**{abs(v.pct):.1f} % weniger**" if v.pct is not None else f"**{abs(v.diff):.1f} weniger**"
        st.success(f"✅ **{label}**: im Mittel {amount} Spiele ({v.diff:.2f} je Bay, Standardfehler {v.se:.2f}). In **{d.worse * 100:.0f} %** der Bays ist es umgekehrt.")
    elif v.kind == "worse":
        amount = f"**{v.pct:.1f} % mehr**" if v.pct is not None else f"**{v.diff:.1f} mehr**"
        st.warning(f"⚠️ **{label}**: im Mittel {amount} Spiele ({v.diff:+.2f} je Bay, Standardfehler {v.se:.2f}). In **{d.better * 100:.0f} %** der Bays ist es besser.")
    else:
        st.info(f"ℹ️ Kein klarer Unterschied bei **{label}**: die Differenz ({v.diff:+.2f} Spiele je Bay) liegt innerhalb des Rauschens (Standardfehler {v.se:.2f}). "
                f"Weniger Spiele in {d.better * 100:.0f} %, mehr in {d.worse * 100:.0f} % der Bays.")


st.markdown("**Urteil über die Stichprobe** (gepaarte Differenz der Spiele, klar ab mehr als zwei Standardfehlern)")
_show_verdict("Johnson gegen Bay-Reihenfolge", J_, B_)
_show_verdict("Johnson gegen Kurze Entladung zuerst", J_, S_)
_show_verdict("Kurze Entladung zuerst gegen Bay-Reihenfolge", S_, B_)
dists = [E.distribution(sample, k, B_) for k in (S_, J_)]
dcol1, dcol2 = st.columns(2)
with dcol1:
    st.markdown("**Wie sich die Gewinne verteilen** (Anteil der Bays, gegen die Bay-Reihenfolge)")
    st.plotly_chart(V.distribution_figure(dists, "Bay-Reihenfolge"), width="stretch", key="distribution_chart")
with dcol2:
    st.markdown("**Typischer Bay gegen Mittelwert**")
    st.plotly_chart(V.gain_figure(dists, "Bay-Reihenfolge"), width="stretch", key="gain_chart")
st.caption(
    f"Basis: {len(sample)} Bays (Seeds 0-{len(sample) - 1}, nicht Ihr Seed) mit Ihren Einstellungen. Im Mittel {E.mean_cycles(sample, N_):.1f} Spiele ohne Doppelspiel, {E.mean_cycles(sample, B_):.1f} in "
    f"Bay-Reihenfolge, {E.mean_cycles(sample, S_):.1f} mit kurzer Entladung zuerst und {E.mean_cycles(sample, J_):.1f} mit Johnson; Kranzeit gespart {E.mean_saving_pct(sample, B_):.1f} / "
    f"{E.mean_saving_pct(sample, S_):.1f} / {E.mean_saving_pct(sample, J_):.1f} %. Johnson erreicht die untere Schranke in {E.at_bound_share(sample, J_) * 100:.0f} % der Bays. Gleich heißt: dieselbe Zahl."
)
st.markdown("**Kranzeit gespart über dem Beladeanteil**")
st.plotly_chart(V.curve_figure(curve, int(load_pct) if int(load_pct) in curve.points else None), width="stretch", key="curve_chart")
st.caption(
    f"Basis: {len(curve.points)} Beladeanteile × {curve.n_bays} Bays (Seeds 0-{curve.n_bays - 1}), Entladeanteil {unload_pct} %, {n_stacks} Stapel, {tiers} Lagen. Der Gewinn ist am größten, wenn Laden und "
    "Löschen ausgewogen sind; die Reihenfolge zählt am meisten bei wenig Beladung."
)

with pdf_slot:
    st.download_button(
        "📄 Ergebnis als PDF herunterladen",
        data=generate_dsp_pdf(bay, outcomes, dict(n_stacks=int(n_stacks), tiers=int(tiers), unload_pct=int(unload_pct), load_pct=int(load_pct), ratio10=r10, seed=int(seed)),
                              sample=sample, curve=curve),
        file_name="doppelspiel_ergebnis.pdf", mime="application/pdf", key="primary_pdf_download",
        help="Szenario, Verfahrensvergleich, Stichprobe mit Urteil und die Kurve über dem Beladeanteil.")

st.markdown("---")

# ---------------------------------------------------------------------------------------------------
# Methodenvergleich
# ---------------------------------------------------------------------------------------------------
with st.expander("🔧 Wie wir das erreichen – vollständiger Methodenvergleich"):
    tabs = st.tabs([o.label for o in outcomes] + ["📊 Vergleich", "✏️ Eigener Bay"])
    for tab, outcome in zip(tabs, outcomes):
        with tab:
            if outcome.key == J_:
                render_johnson_panel("johnson", outcome, outcomes, bay, r10)
            else:
                render_strategy_panel(f"strategy_{outcome.key}", outcome, outcomes, bay, r10)
    with tabs[4]:
        table = []
        for r in E.comparison_rows(bay, outcomes):
            table.append({"Verfahren": r.label, "Spiele": r.cycles, "Einzelspiele": r.singles, "Doppelspiele": r.duals, "Minuten": round(r.minutes), "Zeit gespart": f"{r.saving_pct:.0f} %",
                          "über der Schranke": r.gap_to_bound, "Differenz zu Ohne Doppelspiel": r.delta_cycles})
        lf_cycles, lf_duals, lf_min = E.largest_first_row(bay, r10)
        table.append({"Verfahren": C.UDESC_LABEL, "Spiele": lf_cycles, "Doppelspiele": lf_duals, "Minuten": round(lf_min), "Zeit gespart": f"{100 * (ref.time10 - lf_min * 10 / C.SINGLE_CYCLE_MINUTES) / ref.time10:.0f} %",
                      "über der Schranke": lf_cycles - bound, "Differenz zu Ohne Doppelspiel": lf_cycles - ref.cycles})
        st.dataframe(pd.DataFrame(table), width="stretch", hide_index=True)
        st.plotly_chart(V.comparison_figure(outcomes, bound), width="stretch", key="comparison_chart")
        st.caption("„Größte Entladung zuerst“ ist kein Verfahren der Demo, sondern ein Beispiel für eine Regel, die oft schlechter ist als die Bay-Reihenfolge: sie macht die Stapel spät ladbar.")
    with tabs[5]:
        st.caption("Eigenen Bay eingeben: je Stapel die Zahl der zu löschenden und der zu ladenden Container, mit Komma getrennt (gleich viele Werte in beiden Feldern).")
        u_text = st.text_input("Zu löschen je Stapel", "3, 0, 5, 2, 4, 1", key="custom_u")
        l_text = st.text_input("Zu laden je Stapel", "2, 4, 1, 5, 0, 3", key="custom_l")
        try:
            custom = SC.custom_bay(SC.parse_counts(u_text), SC.parse_counts(l_text))
        except ValueError as err:
            st.warning(f"Eingabe nicht möglich: {err}")
        else:
            custom_out = E.run_methods(custom, r10)
            rows = [{"Verfahren": r.label, "Spiele": r.cycles, "Doppelspiele": r.duals, "Minuten": round(r.minutes), "Zeit gespart": f"{r.saving_pct:.0f} %"} for r in E.comparison_rows(custom, custom_out)]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            cj = E.outcome_of(custom_out, J_)
            st.caption(f"Johnson-Reihenfolge: {' - '.join(str(k + 1) for k in cj.order)}; untere Schranke {R.lower_bound(custom)} Spiele.")
            st.plotly_chart(V.sequence_figure(custom, cj.seq, r10), width="stretch", key="custom_sequence_chart")

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        """
**Bay, Stapel, Aufgaben.** Ein Bay besteht aus Stapeln. Aus jedem Stapel sind **u** Container zu löschen (von oben nach unten), in jeden Stapel sind **l** Container zu laden (von unten nach
oben). Ein Stapel darf erst beladen werden, wenn er **vollständig geleert** ist.

**Einzelspiel und Doppelspiel.** Ein **Einzelspiel** löscht einen Container oder lädt einen. Ein **Doppelspiel** löscht einen Container aus einem Stapel und lädt gleich einen in einen
anderen, schon geleerten Stapel: zwei Aufgaben in einem Spiel. Es dauert länger als ein Einzelspiel (Annahme: das 1,4-fache), aber deutlich kürzer als zwei. Das Ziel ist, möglichst viele
Doppelspiele zu fahren.

**Vier Verfahren**, alle mit demselben Bay:

- **Ohne Doppelspiel** (Referenz): erst alles löschen, dann alles laden, nur Einzelspiele. Zusammen so viele Spiele wie Container.
- **Bay-Reihenfolge**: die Stapel von links nach rechts leeren; sobald ein Stapel leer ist, wird in ihn geladen, im Doppelspiel mit dem nächsten Löschen.
- **Kurze Entladung zuerst**: Stapel mit wenig zu löschen zuerst. Sie werden früh leer und nehmen früh Ladung auf, die dann mit den späteren Löschspielen paart.
- **Johnson (exakt)**: erst die Stapel, aus denen weniger gelöscht als geladen wird (aufsteigend nach der Löschzahl), dann die übrigen (absteigend nach der Ladezahl). Beweisbar die wenigsten
  Spiele, ohne Löser.

**Warum Johnson optimal ist.** Zu jeder Reihenfolge der Stapel gibt es eine gierige Paarung, und die Spielzahl ist genau die Laufzeit eines Flow-Shops mit zwei Stufen (Löschen, Laden), dessen
Aufträge die Stapel sind. Für diesen Fall hat Johnson 1954 die beste Reihenfolge bewiesen. Bei bis zu 7 Stapeln probiert die Demo zur **Gegenprobe alle Reihenfolgen** durch.

**Warum die Reihenfolge zählt.** Ein Stapel mit viel zu löschen bindet lange und macht spät Stapel ladbar; „größte Entladung zuerst“ ist deshalb oft schlechter als die Bay-Reihenfolge.
Bei viel Beladung ist fast jede Reihenfolge gut (die untere Schranke ist dann die Zahl der Ladespiele), bei wenig Beladung zählt die Reihenfolge am meisten.

**Untere Schranke.** Jedes Spiel löscht höchstens einen und lädt höchstens einen Container: mindestens max(zu löschen, zu laden) Spiele. Johnson erreicht sie nicht immer, weil nicht jeder
Stapel früh genug leer wird.

**Stichprobe, Verteilung und Urteil.** Die Stichprobe stellt Ihre Einstellungen auf 200 Bays (Seeds 0 bis 199, nicht Ihr Seed) nach. Ein Unterschied gilt als klar, wenn er mehr als zwei
Standardfehler der gepaarten Differenz beträgt. Die Verteilung zeigt, in wie vielen Bays ein Verfahren weniger, gleich viele oder mehr Spiele braucht als die Bay-Reihenfolge; ein Mittelwert weit
vom Median heißt, dass wenige Bays den Gewinn tragen.

**Grenzen dieses Modells** (bewusst so gewählt, damit die Aussage ehrlich bleibt):

- Vereinfachtes **Literaturmodell** (Goodchild und Daganzo 2006): Stapel als Aufträge, ein Stapel wird erst ganz geleert, dann beladen.
- **Keine Fahrzeiten** zwischen Stapeln, **keine Lukendeckel** und keine Trennung Deck/Unterdeck, **keine Stabilität** beim Laden; alle Spiele gleich lang.
- Das **Verhältnis 1,4** (Doppelspiel gegen Einzelspiel) ist eine Annahme; die Reihenfolge, die die meisten Doppelspiele findet, ist für jedes Verhältnis unter 2 dieselbe.
- Die Regel **kurze Entladung zuerst** ist meine Wahl als Faustregel; die Zahlen je Stapel sind zufällig gezogen, nicht aus einem echten Stauplan.
- Alle Zahlen sind **Größenordnungen aus einer Simulation, keine Messung an echten Kranspielen.**
        """
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Doppelspiel-Planung eines Bays** (polynomial lösbar; Zwei-Maschinen-Flow-Shop).

Gegeben sind $S$ Stapel mit $u_i$ zu löschenden und $l_i$ zu ladenden Containern, $U = \sum_i u_i$, $L = \sum_i l_i$. Eine Reihenfolge $\sigma$ der Stapel bestimmt, in welcher Folge sie
ganz geleert werden. Mit $A_0 = 0$ (verfügbare Ladungen) und für $k = 1, \dots, S$
$$
d_k = \min\big(A_{k-1},\, u_{\sigma(k)}\big), \qquad A_k = A_{k-1} + l_{\sigma(k)} - d_k
$$
ist $D(\sigma) = \sum_k d_k$ die Zahl der Doppelspiele: Jedes Löschen aus Stapel $\sigma(k)$ paart sich mit einer Ladung, die in einen schon geleerten Stapel gehört ($A_{k-1}$ zählt nur Ladungen
der Stapel $\sigma(1), \dots, \sigma(k-1)$).

**Spiele und Zeit.**
$$
Z(\sigma) = U + L - D(\sigma), \qquad T(\sigma) = U + L - (2 - r)\, D(\sigma), \qquad 1 \le r < 2 .
$$
Beide werden von derselben Reihenfolge minimiert, denn $T$ fällt mit $D$ für jedes $r < 2$.

**Johnson-Regel.** $Z(\sigma)$ ist die Laufzeit eines Flow-Shops mit zwei Stufen (Löschen, Laden) und den Aufträgen $(u_i, l_i)$. Optimal ist: zuerst die Stapel mit $u_i \le l_i$ aufsteigend
nach $u_i$, dann die mit $u_i > l_i$ absteigend nach $l_i$.

**Untere Schranke.** $D \le \min(U, L)$, also $Z \ge \max(U, L)$ und $T \ge U + L - (2 - r)\min(U, L)$.

**Vergleich über Bays.** Für Verfahren $A$ gegen die Referenz $B$ auf denselben Bays $b = 1, \dots, S$ ist $\Delta_b = Z_A^{(b)} - Z_B^{(b)}$ die Differenz der Spiele (negativ = weniger); berichtet
werden Mittel, Median und die Anteile der Bays mit $\Delta_b < 0$, $= 0$, $> 0$. Ein Unterschied gilt als klar, wenn $|\bar\Delta| > 2\,\mathrm{SE}(\Delta)$ mit dem Standardfehler der gepaarten Differenz.

Implementiert in `dsp_rules.py` (Spielfolgen und Reihenfolgen), `dsp_evaluation.py` (Vergleiche) und `dsp_scenario.py` (Bay).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
