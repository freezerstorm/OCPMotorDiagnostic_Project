"""RÈGLE — CONTINUITÉ DES ENROULEMENTS (décision client É16).

La continuité est une APPRÉCIATION GLOBALE du technicien (un seul
champ Oui / Non — pas une mesure par phase) :

    Continuité = Oui → CONFORME
    Continuité = Non → PROBLÉMATIQUE
    Non renseignée   → NON ÉVALUABLE (on liste ce qui manque)

Aucun seuil ni tolérance : c'est un jugement humain enregistré, pas
un calcul. Le module ne fait que traduire cette réponse.
"""

from diagnostic_rules.base import CONFORME, PROBLEMATIQUE, make_result, not_evaluable

PARAMETER = "continuity"
LABEL = "Continuité des enroulements"


from diagnostic_rules.continuity_knowledge import ACTIONS, CAUSES


def evaluate(data: dict) -> dict:
    """Évalue la continuité globale déclarée par le technicien.

    data attendu : {"continuity_ok": True | False | None}
    """
    continuity_ok = data.get("continuity_ok")
    if continuity_ok is None:
        return not_evaluable(
            PARAMETER,
            LABEL,
            ["continuité des enroulements (appréciation globale : Oui / Non)"],
        )

    return make_result(
        PARAMETER,
        LABEL,
        evaluation=CONFORME if continuity_ok else PROBLEMATIQUE,
        risk=CAUSES if not continuity_ok else None,
        recommendation=ACTIONS if not continuity_ok else None,
        measured_text="Oui" if continuity_ok else "Non",
        # Pas de « Référence / seuil appliqué » : c'est l'appréciation
        # globale du technicien, sans seuil numérique (demande client
        # 26/09/2026 — la ligne ne s'affiche pas sur la page Analyse).
        reference_text=None,
        interpretation=(
            "Le technicien a jugé la continuité des enroulements BONNE."
            if continuity_ok
            else "Le technicien a jugé la continuité des enroulements MAUVAISE."
        ),
    )
