# Analyse initiale du cahier des charges — Étape 0

> Ce document répond au point 26 du cahier des charges : avant de coder,
> il présente l'analyse, l'arborescence, les technologies confirmées,
> les points encore ambigus et l'ordre de développement proposé.
>
> **Aucun code fonctionnel nouveau n'est produit dans ce commit.**
> Le développement des modules commencera après validation du stagiaire.

---

## 1. Analyse du cahier des charges — ce qui est certain

### Nature du projet
- Application web de **diagnostic PONCTUEL** d'un moteur électrique (~60 s).
- Ce n'est PAS une application de monitoring permanent.
- Un **kit physique** (ESP32 + PT100/MAX31865 + ADXL345 + SCT-013-000) acquiert
  automatiquement trois grandeurs : **température, courant, vibration**.
- Les autres mesures (isolement Ph-Ph et Ph-Masse, résistance des enroulements
  R12/R23/R31) sont **systématiquement saisies manuellement**.

### Deux modes, UNE seule fiche
| Mode | Temp. / Courant / Vibration | Isolement + Résistances |
|---|---|---|
| **Manuel** | saisies par le technicien | saisies par le technicien |
| **Automatique** | acquises par le kit | saisies par le technicien |

Les deux modes aboutissent au **même diagnostic**, à la **même fiche**,
au **même rapport PDF** et au **même historique**.

### Architecture de communication (impérative)
```
ESP32 ──MQTT──► Mosquitto ──► Backend FastAPI ──WebSocket/API──► React
```
Le navigateur ne parle **jamais** directement à l'ESP32. Le backend est
responsable de recevoir, valider, associer, stocker et relayer les données.

### Contraintes de conception
- Code **modulaire** : pas de fichier géant, chaque fonctionnalité dans son module.
- Règles de diagnostic dans un dossier **`diagnostic_rules/`** indépendant,
  avec un fichier par paramètre (courant, température, vibration, isolement,
  résistance d'enroulement). On doit pouvoir modifier les règles sans toucher
  à l'interface ni à la base de données.
- Aucune caractéristique technique **inventée** : toute valeur non fournie
  est marquée comme **hypothèse** (numérotée H#) et devra être confirmée.
- Configuration par variables d'environnement ; aucun secret en dur.
- Interface en **français**, sobre, inspirée de la charte OCP (sans reproduction
  du site), adaptée à un technicien en atelier.
- **Pas de suppression** depuis l'interface normale (archivage uniquement)
  pour assurer la traçabilité.
- La base historique de 691 relevés papier est **différée** : l'application
  doit fonctionner sans elle, mais son intégration future doit être possible
  sans réécriture.

---

## 2. Arborescence complète du projet (cible)

```
OCPMotorDiagnostic_Project/
│
├── README.md                     ← Mode d'emploi (installation, lancement, structure)
├── .env.example                  ← Modèle des variables d'environnement (racine)
├── .gitignore
├── docker-compose.yml            ← PostgreSQL + Mosquitto (dev local)
│
├── docs/                         ← Documentation du projet
│   ├── PLAN_DEVELOPPEMENT.md     ← Plan détaillé, étapes, hypothèses
│   └── 00_ANALYSE_INITIALE.md    ← Ce document
│
├── infra/                        ← Configuration des services d'infrastructure
│   └── mosquitto/
│       └── config/
│           └── mosquitto.conf    ← Broker MQTT (dev local)
│
├── backend/                      ← BACKEND — Python / FastAPI
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini               ← Migrations Alembic (Étape 4)
│   ├── alembic/                  ← Versions de migrations
│   │   └── versions/
│   └── app/
│       ├── __init__.py
│       ├── main.py               ← Point d'entrée FastAPI (assembly)
│       ├── core/                 ← Configuration centralisée
│       │   ├── __init__.py
│       │   └── config.py
│       ├── api/                  ← Routes HTTP (versionnées /api/v1/...)
│       │   ├── __init__.py
│       │   ├── router.py         ← Routeur principal
│       │   ├── health.py         ← Route /health (déjà présente)
│       │   ├── motors.py         ← Moteurs (création, recherche par ID)
│       │   ├── tests.py          ← Cycles de diagnostic (CRUD)
│       │   ├── measurements.py   ← Mesures manuelles + séries auto
│       │   ├── analysis.py       ← Lancement de l'analyse
│       │   ├── reports.py        ← Génération du rapport PDF
│       │   └── history.py        ← Liste, filtres, archivage
│       ├── models/               ← Modèles ORM SQLAlchemy (tables)
│       │   ├── __init__.py
│       │   ├── base.py           ← Classe de base déclarative
│       │   ├── motor.py
│       │   ├── test.py
│       │   ├── manual_measure.py
│       │   └── time_series.py    ← Mesures automatiques (temporel)
│       ├── schemas/              ← Schémas Pydantic (validation entrante/sortante)
│       │   ├── __init__.py
│       │   ├── motor.py
│       │   ├── test.py
│       │   ├── measurement.py
│       │   └── analysis.py
│       ├── services/             ← Logique métier (hors API, hors règles)
│       │   ├── __init__.py
│       │   ├── motor_service.py
│       │   ├── test_service.py
│       │   ├── acquisition_service.py  ← Orchestration d'une acquisition 60 s
│       │   ├── analysis_service.py     ← Appel du moteur de règles
│       │   └── history_service.py
│       ├── db/                   ← Connexion et sessions PostgreSQL
│       │   ├── __init__.py
│       │   └── session.py
│       ├── mqtt/                 ← Client MQTT (abonnement Mosquitto)
│       │   ├── __init__.py
│       │   ├── client.py         ← Connexion, reconnexion, LWT
│       │   ├── topics.py         ← Convention de nommage des topics
│       │   └── dispatcher.py     ← Routage des messages vers les services
│       ├── ws/                   ← WebSocket vers le navigateur
│       │   ├── __init__.py
│       │   └── manager.py        ← Gestionnaire de connexions + broadcast
│       ├── pdf/                  ← Génération du rapport PDF
│       │   ├── __init__.py
│       │   ├── generator.py      ← Rendu WeasyPrint
│       │   └── templates/
│       │       └── report.html   ← Maquette HTML/CSS de la fiche OCP
│       └── simulator/            ← Simulateur ESP32 (dev sans kit physique)
│           ├── __init__.py
│           └── fake_kit.py       ← Publie des MQTT réalistes pendant 60 s
│
├── diagnostic_rules/             ← ⭐ MOTEUR DE RÈGLES (INDÉPENDANT)
│   ├── __init__.py
│   ├── engine.py                 ← Orchestrateur (applique toutes les règles)
│   ├── base.py                   ← Classes de base (ParameterResult, Severity…)
│   ├── current_rules.py          ← Règles du courant
│   ├── temperature_rules.py      ← Règles de température
│   ├── vibration_rules.py        ← Règles de vibration
│   ├── insulation_rules.py       ← Règles d'isolement
│   └── winding_resistance_rules.py  ← Règles de résistance d'enroulement
│
├── frontend/                     ← FRONTEND — React / Vite
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx              ← Point de montage React
│       ├── App.jsx               ← Routage + assembleur
│       ├── styles.css            ← Thème global (palette OCP)
│       ├── theme/                ← Variables de design, tokens
│       │   └── tokens.js
│       ├── layouts/
│       │   └── AppLayout.jsx     ← Gabarit (sidebar + topbar + footer)
│       ├── pages/                ← 8 pages (une par écran)
│       │   ├── HomePage.jsx
│       │   ├── KitConnectionPage.jsx
│       │   ├── MotorFormPage.jsx
│       │   ├── AcquisitionPage.jsx
│       │   ├── GraphPage.jsx
│       │   ├── AnalysisPage.jsx
│       │   ├── ReportPage.jsx
│       │   └── HistoryPage.jsx
│       ├── components/           ← Composants réutilisables
│       │   ├── MotorCard.jsx
│       │   ├── StatusPill.jsx
│       │   ├── DataTable.jsx
│       │   ├── AcquisitionControls.jsx
│       │   └── ParameterAnalysisCard.jsx
│       ├── charts/               ← Graphiques (Recharts)
│       │   ├── TemperatureChart.jsx
│       │   ├── CurrentChart.jsx
│       │   ├── VibrationChart.jsx
│       │   └── ChartBase.jsx      ← Composant commun (grille, tooltip, curseur)
│       ├── services/             ← Appels à l'API REST
│       │   ├── apiClient.js       ← Client fetch avec gestion erreurs
│       │   ├── motors.js
│       │   ├── tests.js
│       │   ├── analysis.js
│       │   └── reports.js
│       ├── websocket/            ← Client WebSocket temps réel
│       │   └── wsClient.js
│       └── state/                ← État partagé (React Context)
│           ├── TestContext.jsx   ← Diagnostic en cours
│           └── KitContext.jsx    ← État de connexion du kit
│
├── esp32/                        ← (PLUS TARD) Firmware du kit physique
│   └── README.md                 ← Pour l'instant : placeholders
│
└── data_legacy/                  ← (PLUS TARD) Intégration base historique 691 relevés
    ├── README.md
    └── importer/                 ← Scripts de nettoyage/import
```

---

## 3. Rôle des dossiers principaux (en simple)

| Dossier | Rôle | Pourquoi il est séparé |
|---|---|---|
| **`backend/`** | Tout le code du serveur (API, logique, MQTT, WebSocket, PDF). | Le serveur n'a rien à voir avec l'affichage du navigateur. |
| `backend/app/api/` | Les « portes d'entrée » HTTP (les adresses URL que le frontend appelle). | On ajoute/modifie une route sans toucher à la logique. |
| `backend/app/models/` | Description des tables de la base de données. | Centralise la structure de la BDD. |
| `backend/app/schemas/` | Validation des données qui entrent et sortent de l'API. | Garantit que les données sont bien formées. |
| `backend/app/services/` | La logique métier (ex: « démarrer un diagnostic », « générer une conclusion »). | Réutilisable par l'API, par le WebSocket, par le MQTT. |
| `backend/app/mqtt/` | Connexion au broker Mosquitto, écoute des messages du kit. | Isole totalement la logique MQTT du reste. |
| `backend/app/ws/` | Gestion des connexions WebSocket vers les navigateurs. | Isole la logique temps réel. |
| `backend/app/pdf/` | Fabrication du PDF à partir d'un modèle HTML/CSS. | Le format du PDF pourra changer sans toucher à l'analyse. |
| `backend/app/simulator/` | Faux kit qui envoie des données MQTT pour tester sans matériel. | Permet de développer tout le reste sans ESP32 branché. |
| **`diagnostic_rules/`** | ⭐ Les règles de diagnostic par paramètre. | **Le stagiaire pourra modifier les seuils/causes/recommandations sans toucher au reste.** |
| **`frontend/src/pages/`** | Les 8 écrans principaux (un fichier par page). | On trouve facilement où modifier un écran. |
| `frontend/src/components/` | Blocs d'interface réutilisables (cartes, boutons, tableaux). | Évite de dupliquer du code. |
| `frontend/src/charts/` | Les trois graphiques (température, courant, vibration). | Les graphiques ont des réglages communs mais un fichier par grandeur. |
| `frontend/src/services/` | Fonctions qui appellent le backend (les « coups de fil » à l'API). | Si l'API change, on ne modifie que ces fichiers. |
| `frontend/src/websocket/` | Connexion temps réel au backend pour voir les mesures en direct. | Isole WebSocket des composants. |
| `frontend/src/state/` | Mémoire partagée de l'interface (diagnostic en cours, état du kit). | Évite de passer les données de composant en composant. |
| **`infra/`** | Configuration des services (Mosquitto). | Séparé du code applicatif. |
| **`docs/`** | Toute la documentation. | Trouvable par quelqu'un qui reprend le projet. |

---

## 4. Technologies confirmées (et pourquoi)

| Bloc | Technologie retenue | Justification simple |
|---|---|---|
| **Frontend** | React 18 + Vite | Choix validé au cahier des charges. Vite est plus simple et rapide que Create React App pour débuter. |
| **Routage frontend** | Routage par hash (`#/page`) — Étape 2 déjà faite. Plus tard on pourra passer à React Router si nécessaire. | Aucune dépendance externe, simple à comprendre pour un débutant. |
| **Graphiques** | **Recharts** | Librairie React moderne, interactive (tooltip, curseur, grille), bien documentée. Alternative : Chart.js (moins « React-native »). Recharts est recommandé pour ce projet. |
| **État global** | **React Context** (pas Redux) | Suffisant pour la taille du projet ; évite une librairie supplémentaire à apprendre. |
| **Backend** | Python 3.11+ / **FastAPI** | Choix validé. FastAPI est moderne, auto-génère la documentation `/docs`, valide les données automatiquement. |
| **Validation** | **Pydantic v2** | Intégré à FastAPI. |
| **ORM / BDD** | **SQLAlchemy 2** + **Alembic** (migrations) | Standard Python, gère bien les évolutions de schéma. |
| **Base de données** | **PostgreSQL 16** | Choix validé. TimescaleDB **non obligatoire** au MVP (extensible si nécessaire plus tard via migrations). |
| **MQTT client** | **paho-mqtt** | Client officiel Eclipse, stable. |
| **Broker MQTT** | **Eclipse Mosquitto 2** (Docker) | Choix validé. Léger, simple à configurer. |
| **Temps réel navigateur** | **WebSocket natif** (pas Socket.IO) | Navigateur et FastAPI le supportent nativement ; évite une dépendance. |
| **PDF** | **WeasyPrint** | Transforme du HTML/CSS en PDF. Permet de maquetter la fiche OCP avec des outils que le stagiaire connaît déjà (HTML/CSS), plutôt qu'une librairie de dessin bas niveau (ReportLab). |
| **Infrastructure dev** | **Docker Compose** | Lance PostgreSQL et Mosquitto en une commande, sans installation manuelle. |
| **Styles** | CSS natif avec variables (déjà commencé à l'étape 2) | Pas de framework CSS lourd (Tailwind, MUI…) pour garder la maîtrise du design sobre OCP. |

---

## 5. Points techniques ambigus / hypothèses à confirmer

Aucune valeur ci-dessous n'est considérée comme un fait. Elles sont marquées
**H#** et sont présentées au stagiaire pour confirmation **avant** d'être
utilisées dans les règles ou le matériel.

| # | Hypothèse / Question | Domaine | Quand il faut décider |
|---|---|---|---|
| **H1** | **Vibration** : l'ADXL345 fournit les 3 axes (x, y, z). Qu'est-ce qui est affiché / analysé : chaque axe ? Une valeur globale (RMS ou magnitude √(x²+y²+z²)) ? Les deux ? | Règles / graphiques | Étape 8 |
| **H2** | **Courant** : un seul SCT-013 → mesure sur **une seule phase**. Hypothèse : le moteur est équilibré (moteur asynchrone triphasé sain). Faut-il prévoir une option 3 pinces ? | Acquisition / interprétation | Étape 8 |
| **H3** | **Type d'essai** : le diagnostic se fait **moteur à vide** en atelier (ce qui valide la règle 1/3 In – 2/3 In pour le courant à vide). Est-ce bien le cas pour tous les tests ? | Règles courant | Étape 10 |
| **H4** | **Fréquence d'échantillonnage** : ~1 à 10 mesures par seconde pendant 60 s, avec moyennage côté ESP32 pour éviter le bruit. Combien exactement ? | Stockage / MQTT | Étape 8 |
| **H5** | **Température** : PT100 à œillet fixé sur **carcasse / boîtier de roulement** (mesure de surface, pas de température interne des enroulements). Les seuils d'alerte seront-ils basés sur la température ambiante + échauffement (ΔT) ou sur une valeur absolue ? | Règles température | Étape 10 |
| **H6** | **DI / OT** : je suppose qu'il s'agit de « Demande d'Intervention » et « Ordre de Travail » (champs alphanumériques de référence). Confirmer. | Formulaire | Étape 5 |
| **H7** | **Règle courant à vide 1/3 – 2/3 In** : c'est la seule règle fournie pour l'instant. La littérature indique souvent ~25-40 % In à vide selon puissance et nombre de pôles → à vérifier par rapport aux pratiques OCP. | Règles | Étape 10 |
| **H8** | **Authentification** : le MVP ne propose PAS d'authentification (session locale, atelier fermé). Si une authentification est requise, elle sera ajoutée après le MVP. | Sécurité | Point à confirmer |
| **H9** | **Numéro de série / matricule** : faut-il distinguer clairement « ID moteur » (interne à l'app) de « matricule » (plaque OCP) ? Commentaire : oui, tous les deux sont présents dans le formulaire demandé. | Modèle | Étape 4-5 |
| **H10** | **Fiche OCP de référence** : un scan/fichier de la véritable fiche d'essai OCP permettra de reproduire exactement la maquette du PDF. Pour l'instant, je m'appuie sur les sections listées au point 16. | PDF | Étape 12 |
| **H11** | **Identification du kit** : l'ESP32 publiera-t-il son `kit_id` (adresse MAC ou numéro de série) dans ses messages MQTT ? Conventions de topics MQTT précises à définir avant le firmware. | MQTT | Étape 7 |
| **H12** | **SCT-013-000, plage 0-100 A** : le modèle SCT-013-000 standard est souvent 0-100 A avec sortie 0-50 mA. La calibration (nombre de spires, charge/ burden resistor) doit être confirmée pour l'ESP32. | Électronique / firmware | étape ESP32 |

> Si un point est critique pour l'étape en cours, je le signalerai explicitement
> plutôt que d'inventer une valeur.

---

## 6. Ordre de développement (strict — une étape après l'autre)

Conformément à la demande du cahier des charges, **une étape à la fois**,
avec explication simple des fichiers créés, de leur rôle, et de la façon de
tester, **puis attente de validation** avant de passer à la suivante.

| Étape | Livrable | Sortie attendue (testable) |
|---|---|---|
| ✅ 0 | Analyse + arborescence (ce document) | — |
| ✅ 1 | Squelette (dossiers, Docker Compose, backend/frontend minimaux) | `GET /api/v1/health` répond ; page React affiche « backend opérationnel » |
| ✅ 2 | Navigation frontend + 8 écrans reliés | On peut naviguer entre les 8 pages ; placeholder sur pages non développées |
| **3** | **Backend API de base** | Routes REST en mémoire (moteurs, tests) ; `/docs` fonctionnel ; frontend appelle l'API via services/ |
| **4** | **PostgreSQL + modèles + Alembic** | Tables créées ; migrations ; les données survivent aux redémarrages |
| **5** | **Formulaire + test manuel** | Saisie moteur + mesures manuelles + sauvegarde en base ; auto-remplissage si ID connu |
| **6** | **Historique** | Tableau sur la page d'accueil + page historique ; recherche ; filtres ; consultation ; archivage |
| **7** | **MQTT + simulateur ESP32** | Backend s'abonne à Mosquitto ; simulateur Python publie des mesures ; page Connexion kit affiche états (déconnecté → connecté) |
| **8** | **Acquisition auto ~60 s** | Parcours START/QUIT ; états IDLE→READY→ACQUIRING→COMPLETED/ERROR ; gestion perte de connexion ; données en base |
| **9** | **Page View Graph** | 3 figures distinctes (T°/courant/vibration) avec grille, curseur, tooltip, min/max/moy/durée |
| **10** | **Moteur de règles modulaire** | Dossier `diagnostic_rules/` ; règle courant 1/3–2/3 In fonctionnelle ; autres règles en « à définir » |
| **11** | **Page Analysis** | Analyse par paramètre (valeur → référence → évaluation → interprétation → risque → action) ; conclusion auto ; décision technicien ; observations libres |
| **12** | **Rapport PDF** | Génération WeasyPrint ; maquette fiche OCP (sections du point 16) ; téléchargement depuis l'interface |
| **13** | **Intégration parcours auto complet** | Bout-en-bout : kit connecté → acquisition → graph → analyse → PDF → historisation |
| **14** | **Tests et finitions** | Tests des cas limites (perte kit, saisie invalide, moteur existant) ; améliorations responsive |
| **15** | **Architecture base historique** | Dossier `data_legacy/` avec schéma d'import/standardisation et documentation (sans importer les 691 lignes dans le MVP) |

---

## 7. Décisions immédiates à valider par le stagiaire

Avant de démarrer l'étape 3, pourrais-tu confirmer :

1. **H8** : Est-ce qu'on part bien **sans authentification** pour le MVP ?
2. **Routeur frontend** : Le routage par hash actuel te convient-il pour l'instant
   (simple, sans dépendance) ou préfères-tu React Router dès maintenant ?
3. **Graphiques** : Je recommande **Recharts** — confirmation ?
4. **PDF** : Je recommande **WeasyPrint** (HTML/CSS → PDF) plutôt que ReportLab
   (dessin bas niveau) — confirmation ?
5. **Type d'essai (H3)** : Les tests se font-ils tous **à vide** en atelier ? Cela
   impacte directement la règle du courant à vide.
6. Y a-t-il une **fiche OCP de référence** (scan ou PDF) que tu peux me partager
   pour que le rapport PDF reproduise au plus juste la fiche officielle ?

Dès validation de ces points (même partielle), je démarre l'**étape 3** :
Backend API de base.
