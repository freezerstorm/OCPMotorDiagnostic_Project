"""RÈGLE — COURANT À VIDE (fournie par le client).

    In/3  ≤  I0  ≤  2·In/3

    I0 < In/3      → PROBLÉMATIQUE
    In/3 ≤ I0 ≤ 2In/3 → CONFORME
    I0 > 2In/3     → PROBLÉMATIQUE

Avec : I0 = courant mesuré à vide, In = courant nominal (plaque moteur).

Le module est PUR : il reçoit des nombres, renvoie un résultat.
Il ne lit ni la base de données, ni l'interface.
"""

from diagnostic_rules.base import (
    CONFORME,
    PROBLEMATIQUE,
    fmt,
    make_result,
    not_evaluable,
)

PARAMETER = "current_no_load"
LABEL = "Courant à vide"


from diagnostic_rules.current_knowledge import (
    ACTIONS_TROP_ELEVE,
    ACTIONS_TROP_FAIBLE,
    CAUSES_TROP_ELEVE,
    CAUSES_TROP_FAIBLE,
)


def evaluate(data: dict) -> dict:
    """Applique la règle ⅓ In – ⅔ In aux données du test.

    data attendu : {"rated_current_a": In | None, "measured_current_a": I0 | None}
    """
    rated = data.get("rated_current_a")
    measured = data.get("measured_current_a")

    # CAS LIMITE : In doit être un nombre STRICTEMENT POSITIF (c'est un
    # diviseur). L'API refuse déjà 0/négatif à la saisie ; on se protège
    # quand même contre une donnée absurde déjà en base (jamais de 500).
    if rated is not None and rated <= 0:
        return not_evaluable(
            PARAMETER, LABEL,
            ["courant nominal In invalide (0 ou négatif) — corriger la fiche moteur"],
        )

    missing = []
    if rated is None:
        missing.append("courant nominal In (caractéristique « Courant nominal » de la fiche moteur)")
    if measured is None:
        missing.append("courant mesuré I0 (fiche ou échantillons du kit)")
    if missing:
        return not_evaluable(PARAMETER, LABEL, missing)

    low = rated / 3
    high = 2 * rated / 3

    if measured < low:
        evaluation = PROBLEMATIQUE
        interpretation = (
            f"Courant à vide INFÉRIEUR à 1/3 du courant nominal "
            f"({fmt(measured)} A < {fmt(low)} A)."
        )
    elif measured > high:
        evaluation = PROBLEMATIQUE
        interpretation = (
            f"Courant à vide SUPÉRIEUR à 2/3 du courant nominal "
            f"({fmt(measured)} A > {fmt(high)} A)."
        )
    else:
        evaluation = CONFORME
        interpretation = (
            f"Courant à vide compris entre 1/3 et 2/3 du courant nominal "
            f"({fmt(low)} A ≤ {fmt(measured)} A ≤ {fmt(high)} A)."
        )

    # risk / recommendation : causes et actions FOURNIES PAR LE CLIENT
    # (current_knowledge.py), selon le sens de l'écart. Conforme →
    # « Aucun risque » (géré par base.py). Listes indépendantes.
    risques = actions = None
    if evaluation == PROBLEMATIQUE:
        if measured < low:
            risques, actions = CAUSES_TROP_FAIBLE, ACTIONS_TROP_FAIBLE
        else:
            risques, actions = CAUSES_TROP_ELEVE, ACTIONS_TROP_ELEVE

    return make_result(
        PARAMETER,
        LABEL,
        evaluation=evaluation,
        risk=risques,
        recommendation=actions,
        measured_value=measured,
        measured_text=f"{fmt(measured)} A",
        reference_value=rated,
        reference_text=f"Courant nominal In = {fmt(rated)} A — plage attendue : 1/3 In – 2/3 In",
        display={
            "rated_current_a": rated,
            "limit_min_a": round(low, 2),
            "limit_max_a": round(high, 2),
            "unit": "A",
        },
        interpretation=interpretation,
        # Causes/actions fournies par le client (current_knowledge.py) —
        # deux listes indépendantes, choisies selon le sens de l'écart.
    )
