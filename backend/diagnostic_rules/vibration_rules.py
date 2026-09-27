"""RÈGLE — VIBRATION : seuils fournis par le client (24/09/2026).

L'UNITÉ est décidée (client, 17/09/2026) : mm/s partout — le kit
publie la vitesse vibratoire directement, comme la saisie manuelle.

LES SEUILS dépendent de la PUISSANCE de la plaque moteur :

    P ≤ 300 kW  → seuil 4,5 mm/s   (300 kW inclus : choix client)
    P > 300 kW  → seuil 7,1 mm/s

    v ≥ seuil → CRITIQUE (dépassement dès l'égalité, comme la règle
               des paliers ≥ 70 °C — choix client)
    v < seuil → NON CRITIQUE (« Aucun risque »)

Informations insuffisantes (mesure de vibration OU puissance de la
plaque absente) → NON ÉVALUABLE + liste de ce qui manque.
"""

from diagnostic_rules.base import CRITIQUE, NON_CRITIQUE, fmt, make_result, not_evaluable

PARAMETER = "vibration"
LABEL = "Vibration"

# Seuils fournis par le client (vitesse vibratoire globale, mm/s).
SEUIL_PETITE_PUISSANCE_MM_S = 4.5   # P ≤ 300 kW
SEUIL_GRANDE_PUISSANCE_MM_S = 7.1   # P > 300 kW
# Borne de puissance INCLUSE dans le seuil bas (choix client :
# un moteur de 300 kW exactement prend le seuil 4,5 mm/s).
PUISSANCE_BORNE_KW = 300.0


def seuil_mm_s(puissance_kw: float | None) -> float | None:
    """Seuil applicable selon la puissance de la plaque (None : inconnue)."""
    if puissance_kw is None:
        return None
    if puissance_kw <= PUISSANCE_BORNE_KW:
        return SEUIL_PETITE_PUISSANCE_MM_S
    return SEUIL_GRANDE_PUISSANCE_MM_S


from diagnostic_rules.vibration_knowledge import ACTIONS, CAUSES


def evaluate(data: dict) -> dict:
    """Compare la vibration (mm/s) au seuil selon la puissance moteur.

    data attendu : {
        "vibration": {"mm_s": float | None,      # fiche (saisie manuelle)
                      "mm_s_last": float | None}, # dernier échantillon du kit
        "rated_power_kw": float | None,          # puissance de la plaque
    }
    """
    vibration = data.get("vibration") or {}
    value = vibration.get("mm_s")
    if value is None:
        value = vibration.get("mm_s_last")
    puissance = data.get("rated_power_kw")
    seuil = seuil_mm_s(puissance)

    missing = []
    if value is None:
        missing.append("mesure de vibration (fiche ou échantillons du kit)")
    if seuil is None:
        missing.append(
            f"puissance moteur (plaque) — choisit le seuil "
            f"{fmt(SEUIL_PETITE_PUISSANCE_MM_S, 1)} ou "
            f"{fmt(SEUIL_GRANDE_PUISSANCE_MM_S, 1)} mm/s"
        )
    if missing:
        return not_evaluable(PARAMETER, LABEL, missing)

    depassement = value >= seuil
    borne_texte = (
        f"P ≤ {fmt(PUISSANCE_BORNE_KW, 0)} kW"
        if puissance <= PUISSANCE_BORNE_KW
        else f"P > {fmt(PUISSANCE_BORNE_KW, 0)} kW"
    )
    return make_result(
        PARAMETER,
        LABEL,
        evaluation=CRITIQUE if depassement else NON_CRITIQUE,
        risk=CAUSES if depassement else None,
        recommendation=ACTIONS if depassement else None,
        measured_value=value,
        measured_text=f"{fmt(value)} mm/s",
        reference_value=seuil,
        reference_text=(
            f"Seuil : {fmt(seuil, 1)} mm/s (plaque {fmt(puissance, 1)} kW · {borne_texte})"
        ),
        display={"limit_mm_s": seuil, "unit": "mm/s"},
        interpretation=(
            f"Vitesse vibratoire {fmt(value)} mm/s "
            f"{'ATTEINT OU DÉPASSE' if depassement else 'EST SOUS'} "
            f"le seuil de {fmt(seuil, 1)} mm/s "
            f"(puissance de plaque {fmt(puissance, 1)} kW : {borne_texte})."
        ),
    )
