"""CONNAISSANCES — TEMPÉRATURE ÉLEVÉE : causes possibles et actions.

Contenu FOURNI PAR LE CLIENT (26/09/2026), transcrit verbatim —
l'application n'invente rien. Deux listes indépendantes : les causes
n'ont PAS de correspondance imposée avec les actions (choix client).

Utilisé par temperature_rules.py quand un palier atteint ou dépasse
la limite critique (70 °C). Sous la limite → « Aucun risque »
(base.py).
"""

CAUSES = [
    "Surcharge mecanique prolongee",
    "Sous-ventilation (ventilateur casse ou ouies bouchees)",
    "Tension d'alimentation instable (surtension ou sous-tension)",
    "Desequilibre important entre les phases",
    "Demarrages trop frequents ou consecutifs",
]

ACTIONS = [
    "Reduire la charge mecanique sur l'arbre",
    "Nettoyer les ailettes et verifier le ventilateur",
    "Controler et stabiliser la tension du reseau",
    "Mesurer et equilibrer le courant des trois phases",
    "Espacer les cycles de demarrage du moteur",
]
