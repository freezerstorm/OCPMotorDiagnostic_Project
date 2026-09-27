"""RÈGLES DE DIAGNOSTIC — package des modules de règles.

Chaque fichier de ce package contient UNIQUEMENT les règles d'UN
paramètre (demande du client : architecture modulaire) :

    current_rules.py             → courant à vide (fournie)
    insulation_rules.py          → isolement 1 kΩ/V (fournie)
    temperature_rules.py         → température 85 °C (fournie)
    winding_resistance_rules.py  → préparé (seuil non fourni)
    vibration_rules.py           → seuils 4,5 / 7,1 mm/s (fournie)

Ces modules sont PURS : ils reçoivent un dictionnaire de données,
renvoient un résultat normalisé (voir base.py). Ils ne dépendent NI de
la base de données, NI de l'interface, NI de la source de la mesure
(manuel ou kit) — c'est le moteur (backend/app/services/) qui fournit
les données.

AJOUTER / SUPPRIMER / MODIFIER une règle = toucher uniquement au
module concerné ici. Le reste de l'application ne change pas.
"""

from diagnostic_rules import (  # noqa: F401
    continuity_rules,
    current_rules,
    environment_knowledge,
    environment_rules,
    insulation_rules,
    temperature_rules,
    vibration_rules,
    winding_resistance_rules,
)

# Ordre d'affichage dans la page Analyse.
# Le moteur appelle « evaluate(data) » sur chaque module de cette liste.
RULE_MODULES = [
    current_rules,
    insulation_rules,
    temperature_rules,
    winding_resistance_rules,
    continuity_rules,
    vibration_rules,
]
