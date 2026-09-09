"""Règles d'ISOLEMENT (Ph-Ph ×3, Ph-Masse ×3).

Les seuils précis (règle des 1 MΩ/kV, norme IEEE 43, seuils critiques
en dessous desquels le moteur ne doit pas être remis sous tension)
NE SONT PAS encore confirmés/arrêtés. Placeholder UNKNOWN.
"""

from __future__ import annotations

from typing import Optional

from diagnostic_rules.base import ParameterFinding, Severity


def evaluate_insulation(*, min_mohm: Optional[float]) -> ParameterFinding:
    finding = ParameterFinding(
        parameter="Isolement (minimum Ph-Masse / Ph-Ph)",
        unit="MΩ",
        measured_value=min_mohm,
        reference_value="Seuils à définir (règle 1 MΩ/kV ?)",
    )
    if min_mohm is None:
        finding.severity = Severity.UNKNOWN
        finding.evaluation = "NON MESURÉ"
        finding.interpretation = "Valeurs d'isolement non saisies."
        return finding
    finding.severity = Severity.UNKNOWN
    finding.evaluation = f"Min = {min_mohm:.1f} MΩ"
    finding.interpretation = "Les seuils d'isolement minimum (en fonction de la tension nominale) seront ajoutés après validation technique."
    return finding
