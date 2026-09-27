"""CONNAISSANCES — VIBRATIONS : causes possibles et actions.

Contenu FOURNI PAR LE CLIENT (26/09/2026), transcrit verbatim —
l'application n'invente rien. Deux listes indépendantes : les causes
n'ont PAS de correspondance imposée avec les actions (choix client).

Utilisé par vibration_rules.py quand la vitesse vibratoire atteint ou
dépasse le seuil (4,5 mm/s si P ≤ 300 kW, sinon 7,1 mm/s). Sous le
seuil → « Aucun risque » (base.py).
"""

CAUSES = [
    "Desalignement de l'arbre (moteur/pompe)",
    "Defaut d'equilibrage du rotor ou de l'accouplement",
    "Roulements uses ou piques",
    "Fixation lache ou chassis instable",
    "Probleme hydraulique (cavitation de la pompe)",
]

ACTIONS = [
    "Realiser un alignement laser des arbres",
    "Equilibrer dynamiquement le rotor",
    "Remplacer les roulements",
    "Resserrer les boulons de fixation",
    "Controler le debit et la pression de la pompe",
]
