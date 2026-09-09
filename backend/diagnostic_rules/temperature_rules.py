"""Règles liées à la TEMPÉRATURE.

Les seuils précis NE SONT PAS encore définis (point 13 du CDC + H5).
Ce module expose une fonction « placeholder » qui renvoie UNKNOWN,
de sorte que l'infrastructure du moteur de règles est prête,
mais aucune règle inventée n'est introduite.
"""

from __future__ import annotations

from typing import Optional

from diagnostic_rules.base import ParameterFinding, Severity


def evaluate_temperature(*, measured_c: Optional[float]) -> ParameterFinding:
    finding = ParameterFinding(
        parameter="Température (carcasse)",
        unit="°C",
        measured_value=measured_c,
        reference_value="Seuils à définir (classe d'isolation, ΔT échauffement)",
    )
    if measured_c is None:
        finding.severity = Severity.UNKNOWN
        finding.evaluation = "NON MESURÉE"
        finding.interpretation = "Température non saisie."
        return finding
    finding.severity = Severity.UNKNOWN
    finding.evaluation = f"{measured_c:.1f} °C"
    finding.interpretation = "Les seuils précis (seuils d'alerte / critique, dépendance classe d'isolation et température ambiante) seront ajoutés après recherche technique."
    return finding
