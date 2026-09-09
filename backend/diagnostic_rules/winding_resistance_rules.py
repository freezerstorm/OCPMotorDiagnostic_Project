"""Règles de RÉSISTANCE DES ENROULEMENTS (R12, R23, R31).

Les règles précises (déséquilibre max acceptable entre phases, typiquement
< 2-5 % selon la norme) NE SONT PAS encore confirmées. Placeholder UNKNOWN.
"""

from __future__ import annotations

from typing import Optional

from diagnostic_rules.base import ParameterFinding, Severity


def evaluate_winding_resistance(
    *,
    r12: Optional[float],
    r23: Optional[float],
    r31: Optional[float],
) -> ParameterFinding:
    values = [v for v in (r12, r23, r31) if v is not None]
    finding = ParameterFinding(
        parameter="Résistance des enroulements (équilibrage)",
        unit="Ω",
        reference_value="Déséquilibre max à définir (ex: < 2 %)",
    )
    if len(values) < 3:
        finding.severity = Severity.UNKNOWN
        finding.evaluation = "INCOMPLET"
        finding.interpretation = "R12, R23 ou R31 manquant."
        return finding
    avg = sum(values) / 3
    max_dev = max(abs(v - avg) for v in values) / avg * 100 if avg > 0 else 0
    finding.measured_value = avg
    finding.evaluation = f"R12={r12}, R23={r23}, R31={r31} (moy. {avg:.3f} Ω, déséquilibre {max_dev:.2f} %)"
    finding.severity = Severity.UNKNOWN
    finding.interpretation = "Seuil de déséquilibre acceptable à définir après validation technique."
    return finding
