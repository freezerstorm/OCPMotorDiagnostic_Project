"""Socle commun des modules de règles — formats et petites aides.

Chaque module de règle renvoie un résultat AU MÊME FORMAT (voir
« make_result » ci-dessous) : le moteur n'a qu'à les assembler, et la
page Analyse affiche tous les paramètres de la même façon.

Ce fichier ne contient AUCUNE règle : uniquement le format des
résultats et des fonctions de mise en forme.
"""

# ============================================================
# Évaluations possibles : un CODE machine (stable, pour le
# programme) + un LIBELLÉ affiché à l'écran (français).
# Seules les catégories prévues par les règles fournies existent.
# ============================================================
CONFORME = "conforme"
PROBLEMATIQUE = "problematique"
CRITIQUE = "critique"
NON_CRITIQUE = "non_critique"
NON_EVALUABLE = "non_evaluable"

EVALUATION_LABELS = {
    CONFORME: "CONFORME",
    PROBLEMATIQUE: "PROBLÉMATIQUE",
    CRITIQUE: "CRITIQUE",
    NON_CRITIQUE: "NON CRITIQUE",
    NON_EVALUABLE: "NON ÉVALUABLE",
}


def fmt(value, digits: int = 2) -> str:
    """Formate un nombre « à la française » (virgule décimale)."""
    return f"{value:.{digits}f}".replace(".", ",")


def format_resistance(mohm: float) -> str:
    """Résistance en MΩ, affichée en kΩ quand c'est plus lisible.

    Ex. : 0,5 MΩ → « 500 kΩ » ; 2,5 MΩ → « 2,50 MΩ ».
    """
    if mohm >= 1:
        return f"{fmt(mohm)} MΩ"
    return f"{fmt(mohm * 1000, 0)} kΩ"


def make_result(
    parameter: str,
    label: str,
    *,
    evaluation: str,
    measured_value=None,
    measured_text: str = "—",
    reference_value=None,
    reference_text: str = "—",
    display: dict | None = None,
    interpretation: str | None = None,
    risk: str | list | None = None,
    recommendation: str | list | None = None,
    missing_info: list | None = None,
    items: list | None = None,
) -> dict:
    """Construit le résultat normalisé d'UNE règle.

    Champs principaux (demande du client) :
      - parameter / label   : identifiant code + nom affiché ;
      - evaluation          : code machine (CONFORME, PROBLÉMATIQUE…) ;
      - measured_value/text : valeur mesurée (nombre + texte lisible) ;
      - reference_value/text: valeur de référence utilisée (In, Rmin, 85 °C…) ;
      - interpretation      : constat FACTUEL (reformule la règle appliquée) ;
      - risk / recommendation: listes fournies par le client (causes /
        actions — fichier « knowledge » par paramètre) ; conformes →
        « Aucun risque » ; l'application n'invente rien ;
      - missing_info        : ce qui manque quand la règle n'est pas
        applicable (au lieu d'inventer une valeur) ;
      - items               : sous-résultats (les 6 mesures d'isolement).
    """
    # Demande client : quand les valeurs mesurées sont conformes
    # (CONFORME, ou NON CRITIQUE = aucune règle violée, ex. paliers
    # < 70 °C), le paragraphe « risque » porte le texte « Aucun risque »
    # et le champ « action / recommandation » le texte « Aucune action
    # recommandée » (décision client 26/09/2026). Les autres évaluations
    # portent les listes client (fichiers « knowledge ») — rien d'inventé.
    if risk is None and evaluation in (CONFORME, NON_CRITIQUE):
        risk = "Aucun risque"
    if recommendation is None and evaluation in (CONFORME, NON_CRITIQUE):
        recommendation = "Aucune action recommandée"

    return {
        "parameter": parameter,
        "label": label,
        "evaluation": evaluation,
        "evaluation_label": EVALUATION_LABELS[evaluation],
        "measured_value": measured_value,
        "measured_text": measured_text,
        "reference_value": reference_value,
        "reference_text": reference_text,
        "display": display or {},
        "interpretation": interpretation,
        "risk": risk,
        "recommendation": recommendation,
        "missing_info": list(missing_info or []),
        "items": list(items or []),
    }


def not_evaluable(parameter: str, label: str, missing_info: list) -> dict:
    """Résultat « règle non applicable » : on dit CE QUI manque."""
    return make_result(
        parameter, label,
        evaluation=NON_EVALUABLE,
        missing_info=missing_info,
        interpretation="Règle non applicable : information manquante (aucune valeur inventée).",
    )
