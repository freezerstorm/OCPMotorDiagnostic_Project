"""CONNAISSANCES — RÉSISTANCE DES ENROULEMENTS INCORRECTE : causes et actions.

Contenu FOURNI PAR LE CLIENT (26/09/2026), transcrit verbatim —
l'application n'invente rien. Deux listes indépendantes : les causes
n'ont PAS de correspondance imposée avec les actions (choix client).

Utilisé par winding_resistance_rules.py quand R12 ≠ R23 ≠ R31
(égalité stricte, tolérance 0 % — décision client 24/09/2026).
Conforme → « Aucun risque » (base.py).
"""

CAUSES = [
    "Court-circuit partiel entre spires",
    "Mauvais raccordement interne (erreur de rebobinage)",
    "Mauvais serrage ou oxydation des bornes",
    "Rupture partielle d'un brin de cuivre",
    "Echauffement inegal des bobinages",
]

ACTIONS = [
    "Mesurer avec un micro-ohmmetre (pont de Thomson)",
    "Nettoyer et resserrer les connexions du bornier",
    "Verifier l'equilibre des resistances entre phases (ecart < 2%)",
    "Controle visuel des soudures et connexions internes",
    "Rebobiner le stator si un court-circuit est avere",
]
