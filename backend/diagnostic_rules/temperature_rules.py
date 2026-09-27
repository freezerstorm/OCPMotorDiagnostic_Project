"""RÈGLE — TEMPÉRATURE PALIERS (décision client É16, comme la fiche papier).

Deux mesures de palier, après mise en service :

    Côté accouplement  (DE — drive end)
    C.O.A              (NDE — côté opposé à l'accouplement)

    T ≥ 70 °C → CRITIQUE (pour chaque palier)
    T < 70 °C → NON CRITIQUE

CAS DES ANCIENNES FICHES (démo, imports historiques) : elles portent
une température UNIQUE (« temperature_c »). Cette valeur est évaluée
avec l'ancien seuil 85 °C et le résultat est étiqueté « valeur unique
(ancien format) » — aucune donnée n'est inventée ni écrasée.

Informations insuffisantes → NON ÉVALUABLE + liste de ce qui manque.
"""

from diagnostic_rules.base import CRITIQUE, NON_CRITIQUE, fmt, make_result, not_evaluable

PARAMETER = "temperature"
LABEL = "Température paliers"

# Seuil fourni par le client (fiche papier : repère < 70).
LIMIT_C = 70.0

# Ancien seuil (une seule température) — uniquement pour les anciennes fiches.
LEGACY_LIMIT_C = 85.0

_BEARINGS = (
    ("de", "Palier côté accouplement"),
    ("nde", "Palier C.O.A (côté opposé)"),
)


from diagnostic_rules.temperature_knowledge import ACTIONS, CAUSES


def evaluate(data: dict) -> dict:
    """Compare les températures de paliers au seuil critique de 70 °C.

    data attendu : {
        "temp_bearing_de_c":  float | None,
        "temp_bearing_nde_c": float | None,
        "legacy_temperature_c": float | None,   # anciennes fiches
    }
    """
    de = data.get("temp_bearing_de_c")
    nde = data.get("temp_bearing_nde_c")
    legacy = data.get("legacy_temperature_c")

    # --- 1. Les deux paliers sont là → évaluation normale (70 °C) ---
    if de is not None and nde is not None:
        items = []
        critical_count = 0
        for key, label in _BEARINGS:
            value = de if key == "de" else nde
            critical = value >= LIMIT_C
            if critical:
                critical_count += 1
            items.append({
                "key": key,
                "label": label,
                "value_text": f"{fmt(value, 1)} °C",
                "evaluation": CRITIQUE if critical else NON_CRITIQUE,
                "evaluation_label": "CRITIQUE" if critical else "NON CRITIQUE",
            })

        if critical_count:
            evaluation = CRITIQUE
            interpretation = (
                f"{critical_count} palier(s) sur 2 atteignent ou dépassent "
                f"la limite critique de {fmt(LIMIT_C, 0)} °C."
            )
        else:
            evaluation = NON_CRITIQUE
            interpretation = (
                f"Les 2 paliers sont SOUS la limite critique de "
                f"{fmt(LIMIT_C, 0)} °C."
            )
        return make_result(
            PARAMETER,
            LABEL,
            evaluation=evaluation,
            measured_text=(
                f"DE {fmt(de, 1)} °C · NDE {fmt(nde, 1)} °C"
            ),
            reference_text=f"Limite critique par palier : {fmt(LIMIT_C, 0)} °C",
            display={"limit_c": LIMIT_C, "unit": "°C"},
            risk=CAUSES if critical_count else None,
            recommendation=ACTIONS if critical_count else None,
            interpretation=interpretation,
            items=items,
        )

    # --- 2. Un seul palier saisi → information insuffisante ---
    if de is not None or nde is not None:
        missing = "palier C.O.A (côté opposé)" if nde is None else "palier côté accouplement"
        return not_evaluable(
            PARAMETER,
            LABEL,
            [missing + " — les 2 paliers sont nécessaires pour évaluer"],
        )

    # --- 3. Ancienne fiche : température unique → ancien seuil 85 °C ---
    if legacy is not None:
        critical = legacy >= LEGACY_LIMIT_C
        return make_result(
            PARAMETER,
            LABEL,
            evaluation=CRITIQUE if critical else NON_CRITIQUE,
            measured_value=legacy,
            measured_text=f"{fmt(legacy, 1)} °C",
            reference_value=LEGACY_LIMIT_C,
            reference_text=(
                f"Ancienne règle (valeur unique) : limite {fmt(LEGACY_LIMIT_C, 0)} °C"
            ),
            display={"limit_c": LEGACY_LIMIT_C, "unit": "°C", "legacy": True},
            risk=CAUSES if critical else None,
            recommendation=ACTIONS if critical else None,
            interpretation=(
                "Valeur UNIQUE (ancien format de fiche) "
                + (
                    f"SUPÉRIEURE OU ÉGALE à {fmt(LEGACY_LIMIT_C, 0)} °C."
                    if critical
                    else f"INFÉRIEURE à {fmt(LEGACY_LIMIT_C, 0)} °C."
                )
                + " Les prochaines fiches mesurent les 2 paliers (limite 70 °C)."
            ),
        )

    # --- 4. Rien du tout → on dit ce qui manque ---
    return not_evaluable(
        PARAMETER,
        LABEL,
        [
            "température palier côté accouplement",
            "température palier C.O.A (côté opposé)",
        ],
    )
