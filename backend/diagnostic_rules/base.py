"""Classes de base du moteur de règles (étape 10).

Ce fichier définit les structures de données communes à TOUTES les règles.
Il est volontairement petit : il est importé par chaque fichier de règle.

Les règles PROPRES à chaque paramètre seront implémentées dans les fichiers
current_rules.py, temperature_rules.py, etc. (étapes 10 et 11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Severity(str, Enum):
    """Niveau de gravité d'un constat de diagnostic."""

    GOOD = "good"          # dans les clous
    INFO = "info"          # pour information (pas d'anomalie)
    WARNING = "warning"    # à surveiller
    CRITICAL = "critical"  # critique — action immédiate
    UNKNOWN = "unknown"    # données insuffisantes pour évaluer


@dataclass
class ParameterFinding:
    """Résultat d'analyse pour UN paramètre (ex: le courant à vide)."""

    parameter: str                                    # nom du paramètre (ex: "Courant à vide")
    severity: Severity = Severity.UNKNOWN
    measured_value: Optional[float] = None            # valeur mesurée
    reference_value: Optional[str] = None             # valeur de référence (texte, ex: "1/3 In – 2/3 In")
    unit: Optional[str] = None                        # unité (A, °C, MΩ…)
    evaluation: str = ""                              # évaluation courte (ex: "BON")
    interpretation: str = ""                          # interprétation
    risks: List[str] = field(default_factory=list)    # risques potentiels
    recommendations: List[str] = field(default_factory=list)  # mesures recommandées


@dataclass
class DiagnosticConclusion:
    """Conclusion globale d'un diagnostic, agrégée à partir des findings."""

    overall_severity: Severity = Severity.UNKNOWN
    summary: str = ""
    findings: List[ParameterFinding] = field(default_factory=list)
