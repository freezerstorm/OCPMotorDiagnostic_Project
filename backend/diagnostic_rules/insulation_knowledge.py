"""CONNAISSANCES — ISOLEMENT FAIBLE : causes possibles et actions.

Contenu FOURNI PAR LE CLIENT (26/09/2026), transcrit verbatim —
l'application n'invente rien. Deux listes indépendantes : les causes
n'ont PAS de correspondance imposée avec les actions (choix client).

Utilisé par insulation_rules.py quand au moins une mesure des 6
isolements est SOUS la résistance minimale (1 kΩ/V). Conforme →
« Aucun risque » (base.py).
"""

CAUSES = [
    "Humidite ou infiltration d'eau",
    "Encrassement (poussiere, huile, graisse)",
    "Surchauffe thermique (vernis craquele)",
    "Vibrations (usure mecanique des fils)",
    "Pics de tension du reseau ou du variateur",
]

ACTIONS = [
    "Mesurer l'isolement au megohmetre",
    "Nettoyer le stator au solvant dielectrique",
    "Etuver ou chauffer pour secher le moteur",
    "Re-vernir le bobinage",
    "Rebobiner ou remplacer le moteur",
]
