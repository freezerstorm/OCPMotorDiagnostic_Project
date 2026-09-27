"""RÈGLE — ISOLEMENT DES ENROULEMENTS (fournie par le client).

    Rmin = 1 kΩ par 1 V de tension de test   →   Rmin[kΩ] = Vtest[V]

    Exemples : 500 V → 500 kΩ (0,5 MΩ) ; 1000 V → 1 MΩ ;
               2500 V → 2,5 MΩ ; 5000 V → 5 MΩ.

Pour CHACUNE des six mesures (3 phase-phase + 3 phase-masse) :

    R mesurée ≥ Rmin → CONFORME
    R mesurée < Rmin → PROBLÉMATIQUE

UNITÉS (point sensible) : les mesures sont stockées en MΩ (colonnes
« *_mohm »). On convertit donc la tension en MΩ :

    Rmin[MΩ] = Vtest[V] × 1 kΩ/V ÷ 1000 = Vtest / 1000

et TOUTE la comparaison se fait dans cette unité commune (MΩ).
"""

from diagnostic_rules.base import (
    CONFORME,
    PROBLEMATIQUE,
    format_resistance,
    make_result,
    not_evaluable,
)

PARAMETER = "insulation"
LABEL = "Isolement des enroulements"

# Les six mesures, dans l'ordre d'affichage :
# clé du dictionnaire de données → libellé affiché.
MEASURES = [
    ("ph1_ph2", "Ph1–Ph2"),
    ("ph2_ph3", "Ph2–Ph3"),
    ("ph3_ph1", "Ph3–Ph1"),
    ("ph1_ground", "Ph1–Masse"),
    ("ph2_ground", "Ph2–Masse"),
    ("ph3_ground", "Ph3–Masse"),
]


from diagnostic_rules.insulation_knowledge import ACTIONS, CAUSES


def evaluate(data: dict) -> dict:
    """Applique la règle 1 kΩ/V à chaque mesure d'isolement disponible.

    data attendu : {
      "insulation_test_voltage_v": 500 | 1000 | 2500 | 5000 | None,
      "insulation_mohm": {"ph1_ph2": …, …}   (valeurs en MΩ, possiblement incomplètes)
    }
    """
    voltage = data.get("insulation_test_voltage_v")
    measures = data.get("insulation_mohm") or {}
    present = {k: v for k, v in measures.items() if v is not None}

    # --- Informations manquantes ? On le dit au lieu d'inventer. ---
    missing = []
    if voltage is None:
        missing.append("tension de test d'isolement (500 / 1000 / 2500 / 5000 V)")
    if not present:
        missing.append("mesures d'isolement (6 valeurs attendues)")
    if missing:
        return not_evaluable(PARAMETER, LABEL, missing)

    # --- Résistance minimale requise (unité commune : MΩ) ---
    rmin_mohm = voltage / 1000

    items = []
    problematic_count = 0
    for key, label in MEASURES:
        value = present.get(key)
        if value is None:
            # Mesure non saisie : sous-résultat « non applicable »,
            # sans faire échouer les autres mesures.
            items.append({
                "key": key,
                "label": label,
                "value_mohm": None,
                "value_text": "non mesurée",
                "evaluation": "non_evaluable",
                "evaluation_label": "NON MESURÉE",
            })
            continue
        ok = value >= rmin_mohm
        if not ok:
            problematic_count += 1
        items.append({
            "key": key,
            "label": label,
            "value_mohm": value,
            "value_text": format_resistance(value),
            "evaluation": CONFORME if ok else PROBLEMATIQUE,
            "evaluation_label": "CONFORME" if ok else "PROBLÉMATIQUE",
        })

    measured_count = len(present)
    if problematic_count:
        evaluation = PROBLEMATIQUE
        interpretation = (
            f"{problematic_count} mesure(s) d'isolement sur {measured_count} "
            f"sont SOUS la résistance minimale requise ({format_resistance(rmin_mohm)})."
        )
    else:
        evaluation = CONFORME
        interpretation = (
            f"Les {measured_count} mesure(s) d'isolement sont "
            f"à la résistance minimale requise ou au-dessus "
            f"({format_resistance(rmin_mohm)})."
        )

    return make_result(
        PARAMETER,
        LABEL,
        evaluation=evaluation,
        risk=CAUSES if problematic_count else None,
        recommendation=ACTIONS if problematic_count else None,
        measured_text=f"{measured_count} mesure(s) sur 6",
        reference_value=rmin_mohm,
        reference_text=(
            f"Rmin = 1 kΩ × {voltage} V = {format_resistance(rmin_mohm)} "
            f"(tension de test : {voltage} V)"
        ),
        display={
            "test_voltage_v": voltage,
            "rmin_mohm": rmin_mohm,
            "rmin_text": format_resistance(rmin_mohm),
        },
        interpretation=interpretation,
        items=items,
    )
