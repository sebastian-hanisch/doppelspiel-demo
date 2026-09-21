"""Regler-Grenzen, Vorgaben und feste Parameter der Doppelspiel-Demo.

Ein Bay aus Stapeln; je Stapel u Container zum Löschen und l zum Laden. Ein Kranspiel ist ein Einzelspiel (nur löschen oder nur laden) oder ein Doppelspiel (löschen und in einen schon
geleerten Stapel laden). Alles ganzzahlig; die Zeit rechnet in Zehnteln eines Einzelspiels."""

# --- Regler: Grenzen und Vorgaben ---
N_STACKS_RANGE, N_STACKS_DEFAULT = (4, 20), 10
TIERS_RANGE, TIERS_DEFAULT = (2, 10), 6
UNLOAD_PCT_RANGE, PCT_STEP, UNLOAD_PCT_DEFAULT = (10, 100), 10, 50        # Entladeanteil in %: erwarteter Anteil der Lagen, die gelöscht werden
LOAD_PCT_RANGE, LOAD_PCT_DEFAULT = (10, 100), 50
RATIO_RANGE, RATIO_DEFAULT = (1.0, 1.9), 1.4                              # Doppelspiel kostet so viele Einzelspiele (Annahme)
SEED_RANGE, SEED_DEFAULT = (0, 9999), 657

# --- feste Parameter ---
SINGLE_CYCLE_MINUTES = 2.0              # Annahme: ein Einzelspiel dauert 2 Minuten (30 Spiele je Stunde, wie in der Kran-Demo)
BRUTE_FORCE_MAX_STACKS = 7              # Gegenprobe: alle Reihenfolgen durchprobieren bis zu so vielen Stapeln (7! = 5040)

# --- Verfahren (Schlüssel -> Beschriftung, in Anzeigereihenfolge); "Ohne Doppelspiel" ist die Referenz aller Deltas ---
STRAT_NONE, STRAT_BAY, STRAT_SHORT, STRAT_JOHNSON = "none", "bay", "short", "johnson"
STRATEGY_LABELS = {
    STRAT_NONE: "🚫 Ohne Doppelspiel",
    STRAT_BAY: "🏗️ Bay-Reihenfolge",
    STRAT_SHORT: "⏱️ Kurze Entladung",
    STRAT_JOHNSON: "🧮 Johnson (exakt)",
}
STRATEGY_PLAIN = {STRAT_NONE: "Ohne Doppelspiel", STRAT_BAY: "Bay-Reihenfolge", STRAT_SHORT: "Kurze Entladung zuerst", STRAT_JOHNSON: "Johnson"}     # ohne Emoji (PDF, Diagramme)
STRATEGY_SHORT = {STRAT_NONE: "Ohne<br>Doppelspiel", STRAT_BAY: "Bay-<br>Reihenfolge", STRAT_SHORT: "Kurze<br>Entladung", STRAT_JOHNSON: "Johnson"}
STRATEGY_KEYS = tuple(STRATEGY_LABELS)
BASELINE = STRAT_NONE
UDESC_LABEL = "Größte Entladung zuerst (ohne Verfahren)"

# --- Presets: eine gemeinsame Bay-Nummer (Seed); Beladung und Größe wechseln (Werte vorläufig, AP 5 stimmt sie gegen die Abnahmekriterien ab) ---
_BASE = dict(n_stacks=N_STACKS_DEFAULT, tiers=TIERS_DEFAULT, unload_pct=UNLOAD_PCT_DEFAULT, load_pct=LOAD_PCT_DEFAULT, ratio=RATIO_DEFAULT, seed=SEED_DEFAULT)
PRESETS = {
    "Nur Löschen": dict(_BASE, load_pct=10),
    "Ausgewogen": dict(_BASE),
    "Viel Laden": dict(_BASE, load_pct=80),
    "Wenig Laden": dict(_BASE, load_pct=20),
    "Große Bays": dict(_BASE, n_stacks=20, tiers=8),
}

# --- Stichprobe und Kurve (Bays mit den Seeds 0.. , nicht der eingestellte Seed) ---
SAMPLE_BAYS = 200
CURVE_BAYS = 100
CURVE_POINTS = tuple(range(10, 101, 10))        # Beladeanteil in %
VERDICT_Z = 2.0                         # "klar" heißt gepaarte Differenz > VERDICT_Z Standardfehler

# --- Darstellung ---
CYCLE_COLORS = {"U": "#2a6fb0", "L": "#c77700", "D": "#2e7d4f"}        # Einzel-Entladen, Einzel-Beladen, Doppelspiel
CYCLE_NAMES = {"U": "Einzelspiel Entladen", "L": "Einzelspiel Beladen", "D": "Doppelspiel"}
STACK_COLORS = ("#2a6fb0", "#2e7d4f", "#c77700", "#7a3fb0", "#b0356a", "#1a8a8a", "#8a6d1a", "#5b7f2a", "#a0452a", "#4b5563")
MARKER_LINE_COLOR = "#808895"           # mittleres Grau: auf hellem und dunklem Grund sichtbar
STRATEGY_COLORS = {STRAT_NONE: "#8a94a3", STRAT_BAY: "#c77700", STRAT_SHORT: "#2a6fb0", STRAT_JOHNSON: "#2e7d4f"}
BOUND_COLOR = "#7a3fb0"
OUTCOME_COLORS = {"better": "#2e7d4f", "equal": "#b8bfc9", "worse": "#c0392b"}
CHART_HEIGHT = 420
STRATEGY_DESCRIPTIONS = {
    STRAT_NONE: "**Ohne Doppelspiel.** Erst alle Container löschen, dann alle laden: jedes Spiel ist ein Einzelspiel, zusammen so viele Spiele wie Container. Der Alltag ohne Plan und die "
                "Referenz aller Vergleiche.",
    STRAT_BAY: "**Bay-Reihenfolge.** Die Stapel von links nach rechts abarbeiten. Sobald ein Stapel leer ist, wird in ihn geladen, und zwar im Doppelspiel mit dem nächsten Löschen, so oft es geht.",
    STRAT_SHORT: "**Kurze Entladung zuerst.** Stapel mit wenigen zu löschenden Containern zuerst: sie werden früh leer und nehmen früh Ladung auf, die dann im Doppelspiel mit den späteren "
                 "Löschspielen paart. Die kluge Faustregel.",
    STRAT_JOHNSON: "**Johnson (exakt).** Erst die Stapel, aus denen weniger gelöscht als geladen wird (aufsteigend nach der Löschzahl), dann die übrigen (absteigend nach der Ladezahl). "
                   "Beweisbar die wenigsten Spiele; die Spielzahl je Reihenfolge ist die Laufzeit eines Flow-Shops mit zwei Stufen.",
}

# --- Ansicht ---
RIGHT_VIEW_KEYS = (STRAT_BAY, STRAT_SHORT, STRAT_JOHNSON)     # im Bay-Blick steht links immer "Ohne Doppelspiel"
VIEW_DEFAULT = STRAT_JOHNSON
