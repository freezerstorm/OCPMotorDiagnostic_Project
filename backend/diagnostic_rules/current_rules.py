"""Règles liées au COURANT.

Règle implémentée à ce jour (fournie par le cahier des charges) :
    - Courant à vide : doit être compris entre 1/3 In et 2/3 In.

Hypothèse (H3 du document d'analyse) : l'essai est réalisé à VIDE.
Si le moteur n'est pas à vide, cette règle n'est pas valide : elle devra
être confirmée/adaptée.

Autres règles à venir (après recherche technique) :
    - Déséquilibre entre phases
    - Surtension / sous-tension (quand la tension sera mesurée)
    - Surcharge
"""

from __future__ import annotations

from typing import Optional

from diagnostic_rules.base import ParameterFinding, Severity


def evaluate_no_load_current(
    *,
    rated_current_a: Optional[float],
    measured_current_a: Optional[float],
) -> ParameterFinding:
    """Évalue le courant à vide par rapport au courant nominal In."""

    finding = ParameterFinding(
        parameter="Courant à vide",
        unit="A",
        measured_value=measured_current_a,
        reference_value=(
            f"Entre 1/3 In et 2/3 In ({round(rated_current_a/3, 1) if rated_current_a else '?'} – "
            f"{round(2*rated_current_a/3, 1) if rated_current_a else '?'} A)" if rated_current_a
            else "Entre 1/3 In et 2/3 In (In inconnu)"
        ),
    )

    if rated_current_a is None or rated_current_a <= 0:
        finding.severity = Severity.UNKNOWN
        finding.evaluation = "INCONNU"
        finding.interpretation = "Courant nominal In non renseigné : impossible d'évaluer le courant à vide."
        return finding

    if measured_current_a is None:
        finding.severity = Severity.UNKNOWN
        finding.evaluation = "NON MESURÉ"
        finding.interpretation = "Courant à vide non saisi."
        return finding

    ratio = measured_current_a / rated_current_a
    finding.evaluation = f"{measured_current_a:.1f} A → {ratio*100:.1f} % de In"

    lower = rated_current_a / 3
    upper = (2 * rated_current_a) / 3

    if lower <= measured_current_a <= upper:
        finding.severity = Severity.GOOD
        finding.interpretation = "Courant à vide dans la plage acceptable (1/3 In – 2/3 In)."
    elif measured_current_a < lower:
        finding.severity = Severity.WARNING
        finding.interpretation = "Courant à vide anormalement bas."
        finding.risks.append("Alimentation défectueuse ou circuit ouvert sur une phase.")
        finding.recommendations.append("Vérifier l'alimentation et les connexions des trois phases.")
    else:  # > upper
        finding.severity = Severity.CRITICAL
        finding.interpretation = "Courant à vide anormalement élevé."
        finding.risks.append("Problème de roulement ou frottement mécanique.")
        finding.risks.append("Défaut d'entrefer ou bobinage endommagé.")
        finding.risks.append("Erreur de couplage (étoile/triangle).")
        finding.risks.append("Surcharge ou défaut d'alignement.")
        finding.recommendations.append("Contrôler les roulements et la rotation libre de l'arbre.")
        finding.recommendations.append("Vérifier le couplage et la tension d'alimentation.")
        finding.recommendations.append("Inspecter visuellement les enroulements.")

    return finding
