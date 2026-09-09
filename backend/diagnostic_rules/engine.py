"""Orchestrateur du moteur de règles (étape 10).

Ce module APPELLE chaque règle (courant, température, vibration, isolement,
résistance) et agrège leurs résultats en une conclusion globale.

Pour l'instant, les règles sont des squelettes qui renvoient UNKNOWN
(« seuils à définir »). LA SEULE RÈGLE implémentée à ce stade est le courant
à vide (1/3 In – 2/3 In), fournie dans le cahier des charges.

Dès qu'une règle est ajoutée dans un fichier, il suffit de l'importer ici
et de l'ajouter à `run_rules(...)` : pas besoin de toucher à l'API, aux
pages ou à la base de données.
"""

from __future__ import annotations

from typing import Optional

from diagnostic_rules.base import (
    DiagnosticConclusion,
    ParameterFinding,
    Severity,
)


# Import des règles par paramètre. Elles seront ajoutées une par une
# aux étapes 10 et 11. Pour l'instant, seul le courant a une règle définie.
from diagnostic_rules.current_rules import evaluate_no_load_current  # noqa: F401


def run_rules(
    *,
    rated_current_a: Optional[float],
    measured_current_a: Optional[float],
    # Les autres grandeurs (température, vibration, isolement, résistances)
    # seront ajoutées au fur et à mesure.
) -> DiagnosticConclusion:
    """Exécute toutes les règles disponibles et agrège les résultats."""

    findings: list[ParameterFinding] = []

    # --- Règle : courant à vide ---
    findings.append(evaluate_no_load_current(
        rated_current_a=rated_current_a,
        measured_current_a=measured_current_a,
    ))

    # Les autres règles (température, vibration, isolement, R) seront
    # appelées ici à l'étape 11. Chacune renvoie un ParameterFinding.

    # --- Conclusion globale ---
    severity_order = [Severity.GOOD, Severity.INFO, Severity.WARNING, Severity.CRITICAL, Severity.UNKNOWN]
    worst = Severity.GOOD
    for f in findings:
        if severity_order.index(f.severity) > severity_order.index(worst):
            worst = f.severity

    summary = _build_summary(findings, worst)

    return DiagnosticConclusion(
        overall_severity=worst,
        summary=summary,
        findings=findings,
    )


def _build_summary(findings: list[ParameterFinding], worst: Severity) -> str:
    """Génère un texte de conclusion automatique à partir des findings."""
    critical = [f for f in findings if f.severity == Severity.CRITICAL]
    warning = [f for f in findings if f.severity == Severity.WARNING]
    if worst == Severity.GOOD or worst == Severity.INFO:
        return "Tous les paramètres évalués sont dans les plages acceptables. Une inspection visuelle de routine est recommandée avant remise en service."
    if worst == Severity.UNKNOWN:
        return "Données insuffisantes pour produire une conclusion automatique complète. Compléter les mesures manquantes."
    parts = []
    if critical:
        parts.append(f"Anomalie(s) critique(s) détectée(s) : {', '.join(f.parameter for f in critical)}.")
    if warning:
        parts.append(f"Point(s) à surveiller : {', '.join(f.parameter for f in warning)}.")
    parts.append("Consulter les recommandations détaillées pour chaque paramètre avant toute remise en service.")
    return " ".join(parts)
