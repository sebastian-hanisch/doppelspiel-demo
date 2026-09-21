"""Plotly-Diagramme: Spielfolge, Bay, Kurve über den Beladeanteil, Verteilung der Gewinne, Vergleich.

Konventionen des Portfolios: Achsen `fixedrange` (Touch-Scrollen), Vorlage plotly_white, Markerlinien in mittlerem Grau, neutrale Flächen halbtransparent (nichts Weißes im dunklen
Schema), Überschriften stehen als Markdown ÜBER dem Diagramm. Alle Funktionen sind reine Rechnung auf den Ergebnisobjekten; Streamlit kommt hier nicht vor."""

import dsp_constants as C
import dsp_evaluation as E

LEGEND_TOP = dict(orientation="h", yanchor="bottom", y=1.02, x=0)
LEGEND_BOTTOM = dict(orientation="h", yanchor="top", y=-0.22, x=0)
GAP = 0.04                          # Abstand zwischen zwei Spielen (in Einzelspielen)


def _lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def stack_color(k):
    return C.STACK_COLORS[k % len(C.STACK_COLORS)]


def cycle_widths(seq, ratio10):
    """Breite jedes Spiels in Einzelspielen: Einzelspiel 1, Doppelspiel ratio10 / 10."""
    return [ratio10 / 10 if c[0] == "D" else 1.0 for c in seq]


def cycle_text(c):
    if c[0] == "U":
        return f"Einzelspiel: aus Stapel {c[1] + 1} löschen"
    if c[0] == "L":
        return f"Einzelspiel: in Stapel {c[1] + 1} laden"
    return f"Doppelspiel: aus Stapel {c[1] + 1} löschen und in Stapel {c[2] + 1} laden"


def sequence_figure(bay, seq, ratio10):
    """Die Spielfolge als Zeitachse: mittlere Reihe ein Balken je Spiel (blau = Einzelspiel Entladen, orange = Einzelspiel Beladen, grün = Doppelspiel; ein Doppelspiel ist breiter), darunter
    aus welchem Stapel gelöscht wird, darüber in welchen Stapel geladen wird (Farbe = Stapel). Hover über das ganze Spiel."""
    import plotly.graph_objects as go

    fig = go.Figure()
    widths = cycle_widths(seq, ratio10)
    x = 0.0
    hx, hy, htext = [], [], []
    src, dst = [], []                                                # (x0, x1, Stapel) je Spiel mit Löschquelle beziehungsweise Ladeziel
    for n, (c, w) in enumerate(zip(seq, widths)):
        fig.add_shape(type="rect", x0=x + GAP / 2, x1=x + w - GAP / 2, y0=0, y1=1, fillcolor=C.CYCLE_COLORS[c[0]], line=dict(width=0), layer="below")
        for a in range(3):
            hx.append(x + w * (a + 0.5) / 3)
            hy.append(0.5)
            htext.append(f"<b>Spiel {n + 1}</b><br>{cycle_text(c)}")
        if c[0] in ("U", "D"):
            src.append((x, x + w, c[1]))
        if c[0] in ("L", "D"):
            dst.append((x, x + w, c[-1]))
        x += w
    for spans, y0, y1 in ((src, -0.55, -0.1), (dst, 1.1, 1.55)):
        merged = []
        for a, b, k in spans:
            if merged and merged[-1][2] == k and abs(merged[-1][1] - a) < 1e-9:
                merged[-1][1] = b
            else:
                merged.append([a, b, k])
        for a, b, k in merged:
            fig.add_shape(type="rect", x0=a + GAP / 2, x1=b - GAP / 2, y0=y0, y1=y1, fillcolor=stack_color(k), line=dict(width=0), layer="below")
            if b - a >= 1.5:
                fig.add_annotation(x=(a + b) / 2, y=(y0 + y1) / 2, text=str(k + 1), showarrow=False, font=dict(size=10, color="white"))
    fig.add_trace(go.Scatter(x=hx, y=hy, mode="markers", marker=dict(size=10, opacity=0), showlegend=False, text=htext, hovertemplate="%{text}<extra></extra>", name="Spiele"))
    for key in ("U", "L", "D"):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=C.CYCLE_NAMES[key], marker=dict(size=12, symbol="square", color=C.CYCLE_COLORS[key])))
    fig.update_layout(template="plotly_white", height=230, legend=LEGEND_TOP, margin=dict(t=50, b=30, l=10, r=10), hovermode="closest", xaxis_title="Kranzeit (in Einzelspielen)")
    fig.update_xaxes(range=[-0.2, max(x, 1) + 0.2])
    fig.update_yaxes(range=[-0.75, 1.75], visible=False)
    fig.add_annotation(xref="paper", yref="y", x=0, y=1.78, text="lädt in Stapel", showarrow=False, xanchor="left", font=dict(size=10, color=C.MARKER_LINE_COLOR))
    fig.add_annotation(xref="paper", yref="y", x=0, y=-0.7, text="löscht aus Stapel", showarrow=False, xanchor="left", font=dict(size=10, color=C.MARKER_LINE_COLOR))
    return _lock_axes(fig)


def order_figure(bay, order):
    """Die Stapel in der Reihenfolge des Verfahrens: je Stapel ein Balken für die Löschzahl und einer für die Ladezahl."""
    import plotly.graph_objects as go

    labels = [str(k + 1) for k in order]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[bay.u[k] for k in order], name="zu löschen", marker_color=C.CYCLE_COLORS["U"], hovertemplate="Stapel %{x}: %{y} zu löschen<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=[bay.l[k] for k in order], name="zu laden", marker_color=C.CYCLE_COLORS["L"], hovertemplate="Stapel %{x}: %{y} zu laden<extra></extra>"))
    fig.update_layout(template="plotly_white", height=220, barmode="group", legend=LEGEND_TOP, margin=dict(t=40, b=40, l=10, r=10), xaxis_title="Stapel in der Reihenfolge des Verfahrens",
                      yaxis_title="Container")
    fig.update_xaxes(type="category")
    return _lock_axes(fig)


def curve_figure(cv, load_current=None):
    """Kranzeit-Ersparnis in % über dem Beladeanteil (Mittel über die Bays). Gepunktete graue Linie = eingestellter Beladeanteil."""
    import plotly.graph_objects as go

    fig = go.Figure()
    for key in (C.STRAT_BAY, C.STRAT_SHORT, C.STRAT_JOHNSON):
        y = E.curve_saving(cv, key)
        label = C.STRATEGY_LABELS[key]
        fig.add_trace(go.Scatter(x=list(cv.points), y=list(y), mode="lines+markers", name=label, line=dict(color=C.STRATEGY_COLORS[key], width=2.5), marker=dict(size=7, color=C.STRATEGY_COLORS[key]),
                                 text=[f"<b>{label}</b><br>Beladeanteil {p} %<br>{v:.1f} % Kranzeit gespart" for p, v in zip(cv.points, y)], hovertemplate="%{text}<extra></extra>"))
    if load_current is not None:
        fig.add_vline(x=load_current, line=dict(color=C.MARKER_LINE_COLOR, width=2, dash="dot"), annotation_text="eingestellt", annotation_position="top", annotation_font=dict(size=11))
    fig.update_layout(template="plotly_white", height=C.CHART_HEIGHT, legend=LEGEND_BOTTOM, margin=dict(t=30, b=110), hovermode="closest", xaxis_title="Beladeanteil (%)",
                      yaxis_title="Kranzeit gespart (%)")
    fig.update_xaxes(range=[min(cv.points) - 4, max(cv.points) + 4], tickmode="array", tickvals=list(cv.points))
    fig.update_yaxes(rangemode="tozero")
    return _lock_axes(fig)


def distribution_figure(dists, reference_label):
    """Je Verfahren ein gestapelter Balken: Anteil der Bays mit weniger / gleich vielen / mehr Spielen als die Referenz."""
    import plotly.graph_objects as go

    labels = [C.STRATEGY_PLAIN[d.key] for d in dists]
    fig = go.Figure()
    for attr, name in (("better", f"weniger Spiele als {reference_label}"), ("equal", "gleich viele"), ("worse", f"mehr Spiele als {reference_label}")):
        shares = [getattr(d, attr) * 100 for d in dists]
        fig.add_trace(go.Bar(y=labels, x=shares, orientation="h", name=name, marker_color=C.OUTCOME_COLORS[attr], text=[f"{v:.0f} %" if v >= 6 else "" for v in shares],
                             textposition="inside", insidetextanchor="middle", hovertemplate=f"<b>%{{y}}</b><br>{name}: %{{x:.0f}} % der Bays<extra></extra>"))
    fig.update_layout(barmode="stack", template="plotly_white", height=150 + 70 * len(dists), legend=dict(LEGEND_BOTTOM, y=-0.45, traceorder="normal"), margin=dict(t=20, b=110, l=10),
                      xaxis_title="Anteil der Bays (%)")
    fig.update_xaxes(range=[0, 100])
    fig.update_yaxes(autorange="reversed")
    return _lock_axes(fig)


def gain_figure(dists, reference_label):
    """Median-Gewinn neben Mittel-Gewinn je Verfahren (eingesparte Spiele je Bay gegen die Referenz)."""
    import plotly.graph_objects as go

    labels = [C.STRATEGY_SHORT[d.key] for d in dists]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[d.median_gain for d in dists], name="Median (typischer Bay)", marker_color="#2a6fb0", hovertemplate="<b>%{x}</b><br>Median-Gewinn %{y:.1f} Spiele<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=[d.mean_gain for d in dists], name="Mittelwert", marker_color="#c77700", hovertemplate="<b>%{x}</b><br>Mittel-Gewinn %{y:.1f} Spiele<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=C.MARKER_LINE_COLOR, width=1))
    fig.update_layout(barmode="group", template="plotly_white", height=C.CHART_HEIGHT - 60, legend=LEGEND_BOTTOM, margin=dict(t=20, b=100), yaxis_title=f"eingesparte Spiele gegen {reference_label}")
    return _lock_axes(fig)


def comparison_figure(outcomes, bound):
    """Spiele je Verfahren für denselben Bay. Gestrichelte Linie = untere Schranke max(zu löschen, zu laden)."""
    import plotly.graph_objects as go

    fig = go.Figure()
    labels = [C.STRATEGY_SHORT[o.key] for o in outcomes]
    for label, o in zip(labels, outcomes):
        fig.add_trace(go.Bar(x=[label], y=[o.cycles], marker=dict(color=C.STRATEGY_COLORS[o.key], line=dict(color=C.MARKER_LINE_COLOR, width=1)), showlegend=False, text=[str(o.cycles)],
                             textposition="outside", hovertemplate=f"<b>{o.label}</b><br>%{{y}} Spiele ({o.duals} Doppelspiele)<extra></extra>"))
    fig.add_hline(y=bound, line=dict(color=C.BOUND_COLOR, width=1.5, dash="dash"), annotation_text=f"untere Schranke {bound}", annotation_position="top right", annotation_font=dict(size=11, color=C.BOUND_COLOR))
    fig.update_layout(template="plotly_white", height=C.CHART_HEIGHT - 60, margin=dict(t=30, b=50), yaxis_title="Kranspiele", barmode="overlay")
    fig.update_xaxes(tickangle=0, tickfont=dict(size=10), categoryorder="array", categoryarray=labels)
    fig.update_yaxes(range=[0, max(o.cycles for o in outcomes) * 1.15])
    return _lock_axes(fig)
