"""BASE DE CONNAISSANCES ENVIRONNEMENTALES — données fournies par le client.

Ce fichier contient UNIQUEMENT DES DONNÉES (aucune logique) : c'est ici
qu'on ajoute / modifie / supprime un environnement, un risque, une cause
possible ou une recommandation — sans toucher au reste de l'application.

Structure de chaque environnement :
    label                : nom affiché (doit correspondre au champ
                           « Service / Environnement » de la fiche moteur)
    aliases              : mots-clés retrouvant cet environnement
                           (tolérance avec les anciennes saisies)
    risks                : contraintes environnementales (fournies)
    relevant_parameters  : paramètres particulièrement sensibles ici
                           (codes : current_no_load, insulation, temperature,
                           vibration, winding_resistance)
    diagnostic_links     : ANOMALIE → CAUSES POSSIBLES + RECOMMANDATIONS
                           (déclenché uniquement si le résultat de la règle
                           est dans « when » : problematique / critique)
    priority             : (réservé) niveaux de priorité à définir plus tard

IMPORTANT (formulations prudentes imposées) : les causes sont des
HYPOTHÈSES (« possible », « à investiguer ») — jamais des certitudes.
Tout le contenu provient des informations fournies par le client ;
aucune recommandation supplémentaire n'a été inventée.
"""

# Libellés français des paramètres (codes identiques aux modules de règles)
PARAMETER_LABELS = {
    "current_no_load": "Courant à vide",
    "insulation": "Isolement des enroulements",
    "temperature": "Température",
    "vibration": "Vibration",
    "winding_resistance": "Résistance des enroulements",
}

# Évaluations considérées comme ANOMALIE (déclenchent la recherche de causes)
ANOMALY_EVALUATIONS = ("problematique", "critique")

ENVIRONMENTS = [
    # ============================================================
    # 1. MINE À CIEL OUVERT
    # ============================================================
    {
        "label": "Mine à ciel ouvert",
        "aliases": ["mine"],
        "risks": [
            "Colmatage des systèmes de ventilation pouvant provoquer une surchauffe",
            "Infiltration de poussières abrasives dans les roulements",
            "Chocs mécaniques sur la carcasse",
            "Variations importantes de température pouvant affecter les joints d'étanchéité",
        ],
        "relevant_parameters": ["temperature", "vibration", "current_no_load"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["critique"],
                "possible_causes": [
                    "Colmatage possible des systèmes de ventilation (risque de surchauffe)",
                    "Variations importantes de température ambiante pouvant affecter les joints d'étanchéité",
                ],
                "recommendations": [
                    "Vérifier les systèmes de ventilation (recherche de colmatage)",
                    "Contrôler les joints d'étanchéité",
                ],
                "priority": None,  # niveaux de priorité : à définir plus tard
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Chocs mécaniques sur la carcasse",
                    "Infiltration de poussières abrasives dans les roulements",
                ],
                "recommendations": [
                    "Inspecter la carcasse (traces de chocs mécaniques)",
                    "Contrôler les roulements (infiltration de poussières abrasives)",
                ],
                "priority": None,
            },
            {
                "parameter": "current_no_load",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Surchauffe possible liée au colmatage de la ventilation (à investiguer)",
                ],
                "recommendations": [
                    "Vérifier la ventilation et le refroidissement du moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 2. CONCASSAGE / CRIBLAGE
    # ============================================================
    {
        "label": "Concassage / Criblage",
        "aliases": ["concassage", "criblage", "broyage"],
        "risks": [
            "Vibrations mécaniques intenses et continues",
            "Fatigue mécanique",
            "Dégradation des roulements",
            "Dégradation potentielle des bobinages",
            "Infiltration de poussières fines pouvant affecter l'isolement",
        ],
        "relevant_parameters": ["vibration", "temperature", "insulation", "current_no_load"],
        "diagnostic_links": [
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Vibrations mécaniques intenses et continues de l'environnement",
                    "Fatigue mécanique / dégradation possible des roulements",
                ],
                "recommendations": [
                    "Vérifier les roulements",
                    "Contrôler l'alignement, l'équilibrage et la fixation",
                ],
                "priority": None,
            },
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Infiltration de poussières fines pouvant affecter l'isolement",
                    "Dégradation potentielle des bobinages",
                ],
                "recommendations": [
                    "Vérifier la protection contre les poussières fines",
                    "Surveiller particulièrement l'isolement dans cet environnement",
                ],
                "priority": None,
            },
            {
                "parameter": "temperature",
                "when": ["critique"],
                "possible_causes": [
                    "Dégradation possible des roulements (échauffement, à investiguer)",
                ],
                "recommendations": [
                    "Contrôler les roulements",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 3. LAVERIE / LAVAGE / DÉCANTATION
    # ============================================================
    {
        "label": "Laverie / Lavage / Décantation",
        "aliases": ["laverie", "lavage", "décantation", "decanation"],
        "risks": [
            "Projections d'eau",
            "Humidité élevée",
            "Défaut d'isolement",
            "Défaut de masse",
            "Corrosion",
            "Pénétration d'eau chargée de boue dans les parties mécaniques",
        ],
        "relevant_parameters": ["insulation", "temperature", "vibration"],
        "diagnostic_links": [
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Présence possible d'humidité (humidité élevée, projections d'eau)",
                    "Étanchéité insuffisante / pénétration d'eau chargée de boue",
                ],
                "recommendations": [
                    "Contrôler l'étanchéité du moteur",
                    "Vérifier les joints d'étanchéité",
                    "Vérifier les points d'entrée possibles de l'eau",
                    "Envisager l'ajout ou le remplacement de joints adaptés",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Pénétration possible d'eau chargée de boue dans les parties mécaniques",
                ],
                "recommendations": [
                    "Vérifier les parties mécaniques après exposition à l'eau chargée de boue",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 4. FLOTTATION
    # ============================================================
    {
        "label": "Flottation",
        "aliases": ["flottation"],
        "risks": [
            "Vapeurs corrosives",
            "Dégradation des isolants",
            "Dégradation des joints d'étanchéité",
            "Oxydation des connexions électriques",
        ],
        "relevant_parameters": ["insulation", "temperature", "vibration"],
        "diagnostic_links": [
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Dégradation possible des isolants liée aux vapeurs corrosives",
                    "Oxydation possible des connexions électriques",
                ],
                "recommendations": [
                    "Vérifier la protection contre les vapeurs corrosives",
                    "Contrôler les isolants et les connexions (oxydation)",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 5. SÉCHERIE / FOURS ROTATIFS
    # ============================================================
    {
        "label": "Sécherie / Fours rotatifs",
        "aliases": ["secherie", "sécherie", "fours", "four rotatif"],
        "risks": [
            "Vieillissement thermique prématuré de l'isolant",
            "Surchauffe interne",
            "Refroidissement insuffisant",
            "Problèmes potentiels au niveau des roulements sous forte température",
        ],
        "relevant_parameters": ["temperature", "current_no_load", "vibration", "insulation"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["critique"],
                "possible_causes": [
                    "Refroidissement insuffisant / surchauffe interne (environnement chaud)",
                    "Problèmes potentiels au niveau des roulements sous forte température",
                ],
                "recommendations": [
                    "Vérifier le système de refroidissement",
                    "Contrôler les roulements",
                ],
                "priority": None,
            },
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Vieillissement thermique prématuré de l'isolant (environnement chaud)",
                ],
                "recommendations": [
                    "Surveiller l'isolement plus fréquemment (vieillissement thermique)",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Problèmes potentiels au niveau des roulements sous forte température",
                ],
                "recommendations": [
                    "Contrôler les roulements",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 6. STATION DE TÊTE DU SLURRY PIPELINE
    # ============================================================
    {
        "label": "Station de tête du Slurry Pipeline",
        "aliases": ["slurry", "pipeline", "pompage"],
        "risks": [
            "Surcharge mécanique liée aux variations de viscosité de la pulpe",
            "Vibrations / torsions répétées de l'arbre",
            "Sollicitations mécaniques importantes des pompes",
        ],
        "relevant_parameters": ["current_no_load", "vibration", "temperature"],
        "diagnostic_links": [
            {
                "parameter": "current_no_load",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Surcharge mécanique possible liée aux variations de viscosité de la pulpe",
                ],
                "recommendations": [
                    "Surveiller les conditions de fonctionnement de la pompe (viscosité / charge)",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Vibrations / torsions répétées de l'arbre",
                    "Sollicitations mécaniques importantes des pompes",
                ],
                "recommendations": [
                    "Contrôler l'alignement et l'état de l'arbre",
                    "Vérifier les sollicitations mécaniques de la pompe",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 7. PARC DE STOCKAGE ET REPRISE
    # ============================================================
    {
        "label": "Parc de stockage et reprise",
        "aliases": ["parc", "stockage", "reprise"],
        "risks": [
            "Accumulation de poussière de phosphate sur la carcasse",
            "Mauvaise dissipation thermique",
            "Surchauffe",
            "Infiltration d'eau lors des lavages ou intempéries",
            "Dégradation possible de l'indice de protection",
        ],
        "relevant_parameters": ["temperature", "insulation", "vibration", "current_no_load"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["critique"],
                "possible_causes": [
                    "Accumulation de poussière de phosphate sur la carcasse (mauvaise dissipation thermique)",
                    "Surchauffe",
                ],
                "recommendations": [
                    "Nettoyer la carcasse (poussière de phosphate)",
                    "Vérifier les conditions de refroidissement",
                ],
                "priority": None,
            },
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Infiltration d'eau possible lors des lavages ou intempéries",
                    "Dégradation possible de l'indice de protection",
                ],
                "recommendations": [
                    "Vérifier l'étanchéité et l'indice de protection du moteur",
                    "Vérifier les points d'entrée possibles de l'eau",
                ],
                "priority": None,
            },
        ],
    },
]
