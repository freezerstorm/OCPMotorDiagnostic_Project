"""Règles liées aux VIBRATIONS.

Les seuils précis (norme ISO 10816-3, mm/s RMS, etc.) NE SONT PAS encore
définis (H1 : quelle grandeur, axes vs magnitude globale ?).
Fonction placeholder qui renvoie UNKNOWN en attendant.
"""

from __future__ import annotations

from typing import Optional

from diagnostic_rules.base import ParameterFinding, Severity


def evaluate_vibration(*, magnitude_g: Optional[float]) -> ParameterFinding:
    finding = ParameterFinding(
        parameter="Vibration",
        unit="g",
        measured_value=magnitude_g,
        reference_value="Seuils à définir (norme ISO 10816-3 ?)",
    )
    if magnitude_g is None:
        finding.severity = Severity.UNKNOWN
        finding.evaluation = "NON MESURÉE"
        finding.interpretation = "Vibration non saisie."
        return finding
    finding.severity = Severity.UNKNOWN
    finding.evaluation = f"{magnitude_g:.3f} g (magnitude)"
    finding.interpretation = "Les seuils et la nature exacte de la grandeur analysée (axes individuels vs magnitude RMS) seront confirmés avant l'étape 10."
    return finding
