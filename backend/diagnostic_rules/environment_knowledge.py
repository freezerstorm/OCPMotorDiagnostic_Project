"""BASE DE CONNAISSANCES ENVIRONNEMENTALES — services OCP (désignations réelles).

Ce fichier contient UNIQUEMENT DES DONNÉES (aucune logique) : c'est ici
qu'on ajoute / modifie / supprime un service, une contrainte, une cause
possible ou une recommandation — sans toucher au reste de l'application.

Décision client (28/09/2026) : la liste du formulaire est désormais la
liste officielle des services OCP (22 désignations). Les 7 anciens
libellés génériques (« Mine à ciel ouvert », « Laverie / Lavage /
Décantation »…) sont SUPPRIMÉS : un ancien moteur portant un ancien
libellé affichera « environnement non répertorié » — ses données
historiques restent intactes (décision client).

Structure de chaque service :
    label                : code affiché dans la liste déroulante (ex. « KLB »)
    description          : désignation complète officielle du service
    aliases              : mots-clés retrouvant ce service (tolérance de
                           saisie : chaque variante de code y figure)
    risks                : contraintes environnementales du service
    relevant_parameters  : paramètres particulièrement sensibles ici
                           (codes : current_no_load, insulation, temperature,
                           vibration, winding_resistance)
    diagnostic_links     : ANOMALIE → CAUSES POSSIBLES + RECOMMANDATIONS
                           (déclenché uniquement si le résultat de la règle
                           est dans « when » : problematique / critique)
    priority             : (réservé) niveaux de priorité à définir plus tard

IMPORTANT (formulations prudentes imposées) : les causes sont des
HYPOTHÈSES (« peut être associé à », « peut favoriser », « risque
potentiel », « à vérifier », « hypothèse à confirmer ») — JAMAIS des
certitudes. L'environnement n'est jamais la cause certaine d'une
anomalie. Aucun seuil numérique n'est défini ici : les relations
environnementales sont séparées des seuils de mesure (règles de
diagnostic inchangées).
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
    # 1. KMB / KMB2 — Khouribga Mine B
    # ============================================================
    {
        "label": "KMB / KMB2",
        "description": (
            "Khouribga Mine B — Secteurs d'extraction de phosphate à ciel ouvert "
            "(décapage, déroctage, concassage primaire et transport)."
        ),
        "aliases": ["kmb", "kmb2", "khouribga mine b", "mine b"],
        "risks": [
            "Poussières abrasives (décapage, déroctage, concassage primaire) pouvant colmater la ventilation du moteur",
            "Infiltration de poussières abrasives dans les roulements",
            "Chocs et vibrations liés au déroctage et au concassage primaire",
            "Matériel en plein air : variations de température et humidité pouvant affecter les joints d'étanchéité",
        ],
        "relevant_parameters": ["temperature", "vibration", "current_no_load", "insulation"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Colmatage possible des systèmes de ventilation par les poussières (risque de surchauffe)",
                    "Variations de température en plein air pouvant affecter les joints d'étanchéité (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier les systèmes de ventilation (recherche de colmatage) et nettoyer les ouïes",
                    "Rechercher un encrassement important du moteur",
                    "Contrôler les joints d'étanchéité",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Chocs mécaniques liés au déroctage et au concassage primaire",
                    "Infiltration de poussières abrasives dans les roulements (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Contrôler les roulements",
                    "Vérifier la fixation, l'alignement et l'équilibrage",
                    "Inspecter la carcasse (traces de chocs mécaniques)",
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
                    "Vérifier la charge entraînée (concassage primaire, transport)",
                ],
                "priority": None,
            },
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Dépôts de poussières conductrices ou abrasives pouvant être associés à la dégradation de l'isolement (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Vérifier l'indice de protection (IP) du moteur par rapport aux conditions d'installation",
                    "Contrôler l'étanchéité de la boîte à bornes et nettoyer si nécessaire",
                    "Rechercher des dépôts de poussière dans le moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 2. KM03 — Unité / Zone Extraction 03
    # ============================================================
    {
        "label": "KM03",
        "description": (
            "Unité / Zone Extraction 03 — Extraction à ciel ouvert et alimentation "
            "des installations de concassage."
        ),
        "aliases": ["km03", "km 03", "extraction 03"],
        "risks": [
            "Poussières d'extraction à ciel ouvert pouvant colmater la ventilation",
            "Chocs et vibrations liés à l'extraction et à l'alimentation du concassage",
            "Matériel en plein air : intempéries et variations de température",
        ],
        "relevant_parameters": ["temperature", "vibration"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Colmatage possible de la ventilation par les poussières (risque de surchauffe)",
                ],
                "recommendations": [
                    "Vérifier la ventilation (recherche de colmatage)",
                    "Nettoyer les ouïes et rechercher un encrassement important",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Chocs et vibrations liés à l'extraction et à l'alimentation des installations de concassage",
                ],
                "recommendations": [
                    "Contrôler les roulements",
                    "Vérifier la fixation et l'alignement",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 3. PE/RE — Pôle Extraction, Réseau Électrique
    # ============================================================
    {
        "label": "PE/RE",
        "description": (
            "Pôle Extraction — Réseau Électrique (Alimentation MT/BT des engins "
            "d'extraction et stations de concassage)."
        ),
        "aliases": ["pe/re", "reseau electrique extraction"],
        "risks": [
            "Postes et réseaux MT/BT exposés aux poussières et aux intempéries",
            "Échauffement possible des connexions et des jeux de barres",
            "Vibrations transmises par les équipements alimentés (concassage)",
        ],
        "relevant_parameters": ["insulation", "temperature"],
        "diagnostic_links": [
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Encrassement des surfaces isolantes par les poussières pouvant favoriser des courants de fuite (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Vérifier la propreté et le serrage des connexions",
                    "Contrôler l'étanchéité de la boîte à bornes",
                    "Vérifier l'indice de protection (IP) du matériel",
                ],
                "priority": None,
            },
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Échauffement possible des connexions ou du circuit magnétique (à vérifier)",
                ],
                "recommendations": [
                    "Contrôler le serrage des connexions",
                    "Vérifier la ventilation et la propreté du moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 4. PE/SI — Pôle Extraction, Services Industriels
    # ============================================================
    {
        "label": "PE/SI",
        "description": "Pôle Extraction — Services Industriels.",
        "aliases": ["pe/si", "services industriels extraction"],
        "risks": [
            "Utilités et ateliers : contraintes généralement modérées",
            "Encrassement ordinaire possible des systèmes de ventilation",
        ],
        "relevant_parameters": ["temperature"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Encrassement possible de la ventilation (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier la ventilation et la propreté du moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 5. PE/EI — Pôle Extraction, Électronique & Instrumentation
    # ============================================================
    {
        "label": "PE/EI",
        "description": "Pôle Extraction — Électronique & Instrumentation.",
        "aliases": ["pe/ei", "electronique instrumentation extraction"],
        "risks": [
            "Locaux techniques : environnement généralement peu contraignant pour les moteurs",
            "Encrassement possible si les locaux ne sont pas climatisés",
        ],
        "relevant_parameters": ["temperature"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Ventilation ou refroidissement insuffisant possible (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier la ventilation et la propreté du moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 6. KTD / ZKTD — Khouribga Traitement Daoui
    # ============================================================
    {
        "label": "KTD / ZKTD",
        "description": (
            "Khouribga Traitement Daoui — Installations de criblage, séchage "
            "thermique et traitement du phosphate."
        ),
        "aliases": ["ktd", "zktd", "traitement daoui"],
        "risks": [
            "Poussières de phosphate (criblage, traitement) pouvant encrasser la ventilation et se déposer dans les bobinages",
            "Contraintes thermiques liées au séchage du phosphate",
            "Vibrations mécaniques liées aux équipements de criblage",
        ],
        "relevant_parameters": ["temperature", "vibration", "insulation"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Encrassement de la ventilation par les poussières pouvant affecter le refroidissement (hypothèse à confirmer)",
                    "Contraintes thermiques de l'installation de séchage",
                ],
                "recommendations": [
                    "Vérifier la ventilation / le refroidissement du moteur",
                    "Vérifier l'encrassement éventuel (ouïes, ailettes)",
                    "Une attention particulière doit être portée à la propreté du moteur dans cet environnement poussiéreux",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Vibrations mécaniques liées aux équipements de criblage",
                    "Dégradation possible des roulements",
                ],
                "recommendations": [
                    "Vérifier les roulements",
                    "Contrôler la fixation, l'alignement et les éléments mécaniques associés",
                ],
                "priority": None,
            },
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Dépôts de poussières pouvant être associés à la dégradation de l'isolement (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Vérifier l'indice de protection (IP) adapté aux conditions d'installation",
                    "Contrôler et nettoyer la boîte à bornes",
                    "Rechercher des dépôts de poussière dans le moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 7. KTB — Khouribga Traitement B
    # ============================================================
    {
        "label": "KTB",
        "description": "Khouribga Traitement B — Unité de séchage et dépoussiérage.",
        "aliases": ["ktb", "traitement b"],
        "risks": [
            "Contraintes thermiques liées au séchage",
            "Poussières fines malgré le dépoussiérage, pouvant encrasser la ventilation",
        ],
        "relevant_parameters": ["temperature", "insulation"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Contraintes thermiques du séchage et encrassement possible de la ventilation (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier la ventilation / le refroidissement",
                    "Vérifier l'encrassement éventuel du moteur",
                ],
                "priority": None,
            },
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Dépôts de poussières fines pouvant être associés à la dégradation de l'isolement (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Contrôler la boîte à bornes et l'indice de protection (IP)",
                    "Rechercher des dépôts de poussière dans le moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 8. KTR — Khouribga Traitement, Réseau Électrique
    # ============================================================
    {
        "label": "KTR",
        "description": "Khouribga Traitement — Réseau Électrique.",
        "aliases": ["ktr", "reseau electrique traitement"],
        "risks": [
            "Postes électriques en zone de traitement : poussières possibles",
            "Échauffement possible des connexions",
        ],
        "relevant_parameters": ["insulation", "temperature"],
        "diagnostic_links": [
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Encrassement des surfaces isolantes pouvant favoriser des courants de fuite (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Vérifier la propreté et le serrage des connexions",
                    "Contrôler la boîte à bornes",
                ],
                "priority": None,
            },
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Échauffement possible des connexions (à vérifier)",
                ],
                "recommendations": [
                    "Contrôler le serrage des connexions",
                    "Vérifier la ventilation du moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 9. DS — Division Séchage (fours, tubes sécheurs rotatifs)
    # ============================================================
    {
        "label": "DS",
        "description": "Division Séchage — Fours et tubes sécheurs rotatifs.",
        "aliases": ["ds", "division sechage", "sechage"],
        "risks": [
            "Ambiance fortement thermique (fours, tubes sécheurs rotatifs)",
            "Vieillissement thermique potentiel de l'isolation des bobinages",
            "Rayonnement thermique sur la carcasse et les connexions",
            "Vibrations liées à la rotation continue des tubes sécheurs",
        ],
        "relevant_parameters": ["temperature", "insulation", "vibration"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Conditions thermiques sévères de l'installation (fours, sécheurs) pouvant affecter le refroidissement",
                    "Ventilation ou refroidissement insuffisant possible (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier le refroidissement et les conditions de ventilation de l'installation",
                    "Vérifier l'état et la propreté du circuit de ventilation du moteur",
                    "Une attention particulière doit être portée à la protection du moteur vis-à-vis des sources de chaleur",
                ],
                "priority": None,
            },
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Vieillissement thermique de l'isolation : risque potentiel à vérifier dans un environnement de fours",
                    "Rayonnement thermique sur les connexions et la boîte à bornes",
                ],
                "recommendations": [
                    "Assurer un suivi rapproché des valeurs d'isolement (évolution dans le temps)",
                    "Vérifier l'état des connexions et de la boîte à bornes (proximité de sources chaudes)",
                    "Vérifier l'adéquation de la classe thermique du moteur aux conditions réelles",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Vibrations liées à la rotation continue des tubes sécheurs (transmises au groupe)",
                ],
                "recommendations": [
                    "Contrôler les roulements",
                    "Vérifier l'alignement moteur / sécheur et le supportage",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 10. KLB — Khouribga Laverie Béni Idir
    # ============================================================
    {
        "label": "KLB",
        "description": (
            "Khouribga Laverie Béni Idir — Unité de lavage, criblage humide, "
            "hydrocyclonage et flottation."
        ),
        "aliases": ["klb", "laverie beni idir"],
        "risks": [
            "Présence d'eau et humidité élevée (environnement de lavage)",
            "Risque potentiel d'infiltration d'eau dans le moteur et la boîte à bornes",
            "Projections d'eau et de pulpe sur les moteurs (criblage humide, hydrocyclonage)",
        ],
        "relevant_parameters": ["insulation", "vibration"],
        "diagnostic_links": [
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "La présence d'humidité ou une infiltration d'eau constitue une hypothèse à vérifier pouvant être associée à la dégradation de l'isolement",
                ],
                "recommendations": [
                    "Vérifier l'étanchéité de la boîte à bornes",
                    "Contrôler les presse-étoupes et les entrées de câbles",
                    "Vérifier l'état des joints",
                    "Vérifier l'indice de protection (IP) adapté aux conditions d'installation",
                    "Rechercher d'éventuelles traces d'humidité ou d'infiltration",
                    "Effectuer les contrôles nécessaires avant toute remise en service",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Vibrations mécaniques liées au criblage humide et aux équipements de lavage",
                    "Dégradation possible des roulements",
                ],
                "recommendations": [
                    "Vérifier les roulements",
                    "Contrôler la fixation, l'alignement et les éléments mécaniques associés",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 11. KLR — Khouribga Laverie, Réseau Électrique
    # ============================================================
    {
        "label": "KLR",
        "description": "Khouribga Laverie — Réseau Électrique.",
        "aliases": ["klr", "reseau electrique laverie"],
        "risks": [
            "Postes électriques en ambiance humide (laverie) : risque potentiel d'infiltration",
            "Échauffement possible des connexions",
        ],
        "relevant_parameters": ["insulation", "temperature"],
        "diagnostic_links": [
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Humidité pouvant être associée à la dégradation de l'isolement (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Vérifier l'étanchéité de la boîte à bornes",
                    "Contrôler les presse-étoupes et l'état des joints",
                ],
                "priority": None,
            },
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Échauffement possible des connexions (à vérifier)",
                ],
                "recommendations": [
                    "Contrôler le serrage des connexions",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 12. KL01 / KL02 / KL03 — Lignes de Laverie
    # ============================================================
    {
        "label": "KL01 / KL02 / KL03",
        "description": (
            "Lignes de Laverie 01, 02 et 03 — Modules de débourbage, déchiquetage "
            "et criblage."
        ),
        "aliases": ["kl01", "kl02", "kl03", "lignes de laverie"],
        "risks": [
            "Présence d'eau et humidité élevée (débourbage, criblage humide)",
            "Risque potentiel d'infiltration d'eau dans le moteur",
            "Vibrations et chocs liés au criblage et au déchiquetage",
        ],
        "relevant_parameters": ["insulation", "vibration"],
        "diagnostic_links": [
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "La présence d'humidité ou une infiltration d'eau constitue une hypothèse à vérifier pouvant être associée à la dégradation de l'isolement",
                ],
                "recommendations": [
                    "Vérifier l'étanchéité de la boîte à bornes",
                    "Contrôler les presse-étoupes, les entrées de câbles et l'état des joints",
                    "Vérifier l'indice de protection (IP) adapté",
                    "Rechercher des traces d'humidité ou d'infiltration",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Vibrations et chocs liés au criblage et au déchiquetage",
                    "Dégradation possible des roulements ou désalignement",
                ],
                "recommendations": [
                    "Vérifier les roulements",
                    "Contrôler la fixation, l'alignement et les éléments mécaniques associés",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 13. LM/X / LMX / L-EXT — Laverie Maintenance Externe
    # ============================================================
    {
        "label": "LM/X / LMX / L-EXT",
        "description": (
            "Laverie Maintenance Externe — Interventions hors site sur équipements "
            "lourds."
        ),
        "aliases": ["lm/x", "lmx", "l-ext", "maintenance externe"],
        "risks": [
            "Transport et manutention d'équipements lourds : chocs possibles",
            "Conditions d'environnement variables sur sites extérieurs (poussières, humidité, température)",
        ],
        "relevant_parameters": ["vibration", "insulation"],
        "diagnostic_links": [
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Chocs possibles pendant le transport ou la manutention",
                    "Désalignement ou desserrage possible après transport (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier la fixation, l'alignement et les roulements après transport",
                    "Inspecter la carcasse (traces de chocs)",
                ],
                "priority": None,
            },
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Stockage ou intervention en extérieur : humidité pouvant être associée à la dégradation de l'isolement (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Vérifier l'étanchéité de la boîte à bornes",
                    "Rechercher des traces d'humidité avant remise en service",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 14. LM/E / LME — Laverie Maintenance Électrique
    # ============================================================
    {
        "label": "LM/E / LME",
        "description": (
            "Laverie Maintenance Électrique — Ateliers centralisés de révision, "
            "bobinage et essais électriques."
        ),
        "aliases": ["lm/e", "lme", "maintenance electrique"],
        "risks": [
            "Atelier fermé : environnement globalement maîtrisé",
            "Moteurs révisés ou rebobinés : l'état de l'isolement dépend de la qualité des travaux effectués",
        ],
        "relevant_parameters": ["insulation", "temperature"],
        "diagnostic_links": [
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Si le moteur a été rebobiné ou revisé, l'anomalie peut être associée aux travaux effectués (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Vérifier les relevés d'essais de l'atelier (isolement, continuité)",
                    "Contrôler la boîte à bornes et le remontage",
                    "Refaire la mesure pour confirmer",
                ],
                "priority": None,
            },
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Encrassement ou ventilation insuffisante possible après remontage (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier la ventilation et la propreté du moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 15. PIPE — Phosphate Slurry Pipeline
    # ============================================================
    {
        "label": "PIPE",
        "description": (
            "Phosphate Slurry Pipeline — Minéroduc et transport par pompage de la "
            "pulpe de phosphate."
        ),
        "aliases": ["pipe", "mineroduc", "slurry", "pipeline"],
        "risks": [
            "Fonctionnement continu en pompage : charge mécanique permanente",
            "Vibrations liées aux pompes et à la circulation de pulpe",
            "Efforts hydrauliques pouvant se transmettre à l'accouplement et aux paliers",
        ],
        "relevant_parameters": ["vibration", "current_no_load"],
        "diagnostic_links": [
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Conditions de pompage (charge mécanique entraînée, circulation de pulpe)",
                    "Désalignement ou dégradation possible des roulements / paliers",
                ],
                "recommendations": [
                    "Vérifier les roulements et l'alignement moteur / pompe",
                    "Contrôler l'accouplement et la fixation",
                    "Vérifier les conditions de pompage (cavitation possible, appuis de tuyauterie)",
                ],
                "priority": None,
            },
            {
                "parameter": "current_no_load",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Charge mécanique entraînée ou conditions de pompage inhabituelles (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier les conditions de fonctionnement de la pompe (débit, pression)",
                    "Contrôler l'alignement et la rotation libre de la ligne d'arbres",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 16. PP.ST — Poste / Station de Pompage
    # ============================================================
    {
        "label": "PP.ST",
        "description": (
            "Poste / Station de Pompage — Pompage haute pression et "
            "épuisement/puisard."
        ),
        "aliases": ["pp.st", "pp st", "station de pompage", "puisard"],
        "risks": [
            "Présence d'eau et humidité (épuisement, puisard) : risque potentiel d'infiltration",
            "Pompage haute pression : vibrations et charge mécanique permanente",
        ],
        "relevant_parameters": ["insulation", "vibration"],
        "diagnostic_links": [
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "La présence d'humidité ou une infiltration d'eau constitue une hypothèse à vérifier pouvant être associée à la dégradation de l'isolement",
                ],
                "recommendations": [
                    "Vérifier l'étanchéité de la boîte à bornes",
                    "Contrôler les presse-étoupes et l'état des joints",
                    "Rechercher des traces d'humidité ou d'infiltration",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Conditions de pompage (haute pression, charge permanente)",
                    "Désalignement ou dégradation possible des roulements",
                ],
                "recommendations": [
                    "Vérifier les roulements et l'alignement moteur / pompe",
                    "Contrôler la fixation et les supports de tuyauterie",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 17. KPPA — Khouribga Projet / Pompage A
    # ============================================================
    {
        "label": "KPPA",
        "description": (
            "Khouribga Projet / Pompage A — Stations d'alimentation en eau et "
            "transfert de pulpe."
        ),
        "aliases": ["kppa", "pompage a"],
        "risks": [
            "Stations d'eau / pulpe : humidité et risque potentiel d'infiltration",
            "Pompage continu : vibrations et charge mécanique",
        ],
        "relevant_parameters": ["insulation", "vibration"],
        "diagnostic_links": [
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Humidité pouvant être associée à la dégradation de l'isolement (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Vérifier l'étanchéité de la boîte à bornes et l'état des joints",
                    "Rechercher des traces d'humidité",
                ],
                "priority": None,
            },
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Conditions de pompage (transfert d'eau / pulpe)",
                ],
                "recommendations": [
                    "Vérifier les roulements et l'alignement moteur / pompe",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 18. PC/SI — Pôle Chimie, Services Industriels
    # ============================================================
    {
        "label": "PC/SI",
        "description": "Pôle Chimie — Services Industriels.",
        "aliases": ["pc/si", "services industriels chimie"],
        "risks": [
            "Utilités et ateliers : contraintes généralement modérées",
            "Encrassement ordinaire possible des systèmes de ventilation",
        ],
        "relevant_parameters": ["temperature"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Encrassement possible de la ventilation (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier la ventilation et la propreté du moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 19. PC ASA — Pôle Chimie, Ateliers Séchage Alimentation
    # ============================================================
    {
        "label": "PC ASA",
        "description": "Pôle Chimie — Ateliers Séchage Alimentation.",
        "aliases": ["pc asa", "pc/asa", "asa"],
        "risks": [
            "Contraintes thermiques liées au séchage",
            "Encrassement possible de la ventilation",
        ],
        "relevant_parameters": ["temperature"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Contraintes thermiques du séchage et encrassement possible de la ventilation (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier la ventilation / le refroidissement",
                    "Vérifier l'encrassement éventuel du moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 20. PC/IE — Pôle Chimie, Instrumentation & Électronique
    # ============================================================
    {
        "label": "PC/IE",
        "description": "Pôle Chimie — Instrumentation & Électronique.",
        "aliases": ["pc/ie", "instrumentation electronique chimie"],
        "risks": [
            "Locaux techniques : environnement généralement peu contraignant pour les moteurs",
        ],
        "relevant_parameters": ["temperature"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Ventilation ou refroidissement insuffisant possible (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier la ventilation et la propreté du moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 21. PC/ZB — Pôle Chimie, Zone B
    # ============================================================
    {
        "label": "PC/ZB",
        "description": "Pôle Chimie — Zone B.",
        "aliases": ["pc/zb", "pc zb", "zone b"],
        "risks": [
            "Zone industrielle : contraintes supposées modérées (détail à préciser)",
            "Encrassement ordinaire possible des systèmes de ventilation",
        ],
        "relevant_parameters": ["temperature"],
        "diagnostic_links": [
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Encrassement possible de la ventilation (à vérifier)",
                ],
                "recommendations": [
                    "Vérifier la ventilation et la propreté du moteur",
                ],
                "priority": None,
            },
        ],
    },

    # ============================================================
    # 22. C M/K — Centrales / Ateliers Mécaniques de Khouribga
    # ============================================================
    {
        "label": "C M/K",
        "description": (
            "Centrales / Ateliers Mécaniques de Khouribga — Usinage, fabrication "
            "et maintenance mécanique, litière/convoyeurs."
        ),
        "aliases": ["c m/k", "cm/k", "centrales ateliers mecaniques", "atelier mecanique"],
        "risks": [
            "Ateliers d'usinage : copeaux et brouillards d'huile pouvant encrasser la ventilation",
            "Convoyeurs et litière : poussières et vibrations mécaniques",
            "Manutentions : chocs possibles sur la carcasse",
        ],
        "relevant_parameters": ["vibration", "temperature", "insulation"],
        "diagnostic_links": [
            {
                "parameter": "vibration",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Vibrations mécaniques liées aux convoyeurs et à la litière",
                    "Dégradation possible des roulements",
                ],
                "recommendations": [
                    "Vérifier les roulements",
                    "Contrôler la fixation et l'alignement",
                ],
                "priority": None,
            },
            {
                "parameter": "temperature",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Encrassement de la ventilation (copeaux, poussières) pouvant affecter le refroidissement (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Vérifier la ventilation et la propreté du moteur",
                ],
                "priority": None,
            },
            {
                "parameter": "insulation",
                "when": ["problematique", "critique"],
                "possible_causes": [
                    "Dépôts d'huile ou de poussières pouvant être associés à la dégradation de l'isolement (hypothèse à confirmer)",
                ],
                "recommendations": [
                    "Nettoyer et contrôler la boîte à bornes",
                    "Rechercher des dépôts d'huile / de poussières dans le moteur",
                ],
                "priority": None,
            },
        ],
    },
]
