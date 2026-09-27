"""CONNAISSANCES — COURANT À VIDE : causes possibles et actions.

Contenu FOURNI PAR LE CLIENT (26/09/2026), transcrit verbatim —
l'application n'invente rien. Deux listes indépendantes : les causes
n'ont PAS de correspondance imposée avec les actions (choix client).

Utilisé par current_rules.py quand I0 sort de la plage attendue
(In/3 ≤ I0 ≤ 2·In/3). Conforme → « Aucun risque » (base.py).
"""

# --- I0 TROP ÉLEVÉ (> 2/3 In) -------------------------------------------
CAUSES_TROP_ELEVE = [
    "Mauvais couplage (moteur câble en Triangle au lieu d'Etoile)",
    "Surtension d'alimentation (tension reseau superieure a la plaque signaletique)",
    "Frottement mecanique interne (roulements grippes ou rotor qui frotte)",
    "Court-circuit entre spires (degradation locale de l'isolant du bobinage)",
    "Erreur de rebobinage (nombre de spires insuffisant ou entrefer modifie)",
]

ACTIONS_TROP_ELEVE = [
    "Corriger le couplage (passer en Etoile)",
    "Controler et reduire la tension reseau",
    "Remplacer les roulements grippes",
    "Tester l'isolement (recherche de court-circuit)",
    "Ajuster le rapport Tension/Frequence du variateur",
]

# --- I0 TROP FAIBLE (< 1/3 In) ------------------------------------------
CAUSES_TROP_FAIBLE = [
    "Mauvais couplage (moteur câble en Etoile au lieu de Triangle)",
    "Sous-tension d'alimentation (tension reseau trop basse)",
    "Coupure d'une phase (fusible grille ou fil desserre, provoquant une marche en monophase)",
    "Mauvais contact electrique (bornes oxydees ou mal serrees qui limitent le courant)",
    "Frequence trop elevee (variateur de vitesse mal configure)",
]

ACTIONS_TROP_FAIBLE = [
    "Corriger le couplage (passer en Triangle)",
    "Controler et augmenter la tension reseau",
    "Remplacer le fusible ou le cable coupe",
    "Nettoyer et resserrer les bornes electriques",
    "Ajuster la frequence maximale du variateur",
]
