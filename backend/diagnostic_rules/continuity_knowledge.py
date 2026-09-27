"""CONNAISSANCES — DÉFAUT DE CONTINUITÉ : causes possibles et actions.

Contenu FOURNI PAR LE CLIENT (26/09/2026), transcrit verbatim —
l'application n'invente rien. Deux listes indépendantes : les causes
n'ont PAS de correspondance imposée avec les actions (choix client).

Utilisé par continuity_rules.py quand la continuité est NON assurée.
Conforme → « Aucun risque » (base.py).
"""

CAUSES = [
    "Rupture d'un fil de bobinage suite a une surchauffe",
    "Cable d'alimentation coupe ou sectionne",
    "Fusible grille ou disjoncteur declenche sur une phase",
    "Connexion desserree ou arrachee dans la boite a bornes",
    "Soudure interne cassee entre deux bobines",
]

ACTIONS = [
    "Tester la continuite au multimetre (mode bip/ohmmetre)",
    "Controler l'etat des fusibles et de l'appareillage en amont",
    "Resserrer et verifier les connexions du bornier",
    "Inspecter visuellement les chignons de bobinage",
    "Rebobiner ou remplacer le moteur si la coupure est interne",
]
