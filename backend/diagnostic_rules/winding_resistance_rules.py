"""RÈGLE — RÉSISTANCE DES ENROULEMENTS (fournie par le client).

    Les trois résistances mesurées entre phases doivent avoir
    LA MÊME VALEUR :   R12 = R23 = R31

    les trois identiques      → CONFORME
    au moins une différente   → PROBLÉMATIQUE
    mesure(s) manquante(s)    → NON ÉVALUABLE (liste de ce qui manque)

NOTE : aucune tolérance de déséquilibre (en %) — le client a CONFIRMÉ
la comparaison STRICTE (tolérance 0 %, 24/09/2026) : des valeurs
même très légèrement différentes sont signalées PROBLÉMATIQUE.
Si une tolérance est définie un jour par le client, ce module seul
sera modifié.
"""

from diagnostic_rules.base import CONFORME, PROBLEMATIQUE, fmt, make_result, not_evaluable

PARAMETER = "winding_resistance"
LABEL = "Résistance des enroulements"

# Les trois mesures, avec leur libellé (ordre d'affichage).
MEASURES = [("r12", "R12"), ("r23", "R23"), ("r31", "R31")]


from diagnostic_rules.winding_resistance_knowledge import ACTIONS, CAUSES


def evaluate(data: dict) -> dict:
    """Vérifie que R12, R23 et R31 sont identiques.

    data attendu : {"winding_resistance_ohm": {"r12": …, "r23": …, "r31": …}}
    """
    winding = data.get("winding_resistance_ohm") or {}
    values = {key: winding.get(key) for key, _ in MEASURES}

    missing = [f"mesure {label} (saisie manuellement)"
               for key, label in MEASURES if values[key] is None]
    if missing:
        return not_evaluable(PARAMETER, LABEL, missing)

    r12, r23, r31 = values["r12"], values["r23"], values["r31"]
    measured_text = f"R12 = {fmt(r12, 3)} Ω · R23 = {fmt(r23, 3)} Ω · R31 = {fmt(r31, 3)} Ω"

    if r12 == r23 == r31:
        return make_result(
            PARAMETER, LABEL,
            evaluation=CONFORME,
            measured_text=measured_text,
            reference_text="Les trois résistances doivent avoir la même valeur (R12 = R23 = R31)",
            interpretation=(
                f"Les trois résistances mesurées sont identiques ({fmt(r12, 3)} Ω)."
            ),
        )

    low, high = min(r12, r23, r31), max(r12, r23, r31)
    return make_result(
        PARAMETER, LABEL,
        evaluation=PROBLEMATIQUE,
        risk=CAUSES,
        recommendation=ACTIONS,
        measured_text=measured_text,
        reference_text="Les trois résistances doivent avoir la même valeur (R12 = R23 = R31)",
        interpretation=(
            f"Les résistances mesurées NE SONT PAS identiques : elles varient "
            f"de {fmt(low, 3)} Ω à {fmt(high, 3)} Ω (une seule valeur attendue)."
        ),
    )
