# OCP Motor Diagnostic — Kit de diagnostic de moteurs électriques

Application web de **diagnostic ponctuel** (~60 s) de moteurs électriques industriels,
développée pour un atelier de maintenance (projet de fin d'études, inspiration de
l'identité visuelle OCP sans reproduction du site).

Deux modes de test existent, qui produisent **la même fiche de diagnostic**,
**le même historique** et **le même rapport PDF** :

| Mode | Température, courant, vibration | Isolement + R12/R23/R31 |
|---|---|---|
| **Manuel** | saisies par le technicien | saisies par le technicien |
| **Automatique** | acquises par le kit (ESP32) | saisies par le technicien |

## Architecture

```
MOTEUR
   ↓ PT100 (MAX31865) + ADXL345 + SCT-013-000
ESP32 (kit) ──MQTT──► Mosquitto ──► Backend FastAPI ──WebSocket/API──► React
                                                                        (navigateur)
```

Le navigateur ne communique **jamais** directement avec le kit : tout passe par le
backend. Plusieurs kits pourront être connectés à terme.

| Bloc | Technologie | Rôle |
|---|---|---|
| `frontend/` | React (Vite) | Interface du technicien (8 écrans) |
| `backend/` | Python + FastAPI | API, logique métier, MQTT, WebSocket, PDF |
| `backend/diagnostic_rules/` | module Python isolé | Règles d'analyse par paramètre (modifiables sans toucher au reste) |
| `infra/` (Docker) | PostgreSQL 16 | Base de données |
| | Mosquitto 2 | Broker MQTT |

> **Document de référence** : voir `docs/PLAN_DEVELOPPEMENT.md` (plan, étapes,
> hypothèses techniques, décisions).

---

## Prérequis (Windows)

1. **Git** — https://git-scm.com
2. **Python 3.11 ou plus récent** — https://www.python.org/downloads
   (cocher « Add python.exe to PATH » à l'installation)
3. **Node.js 20 ou plus récent** — https://nodejs.org
4. **Docker Desktop** — https://www.docker.com/products/docker-desktop
   (PostgreSQL et Mosquitto tourneront dans des conteneurs ; aucune installation manuelle)

---

## Installation (une seule fois)

```bash
# 1. Récupérer le projet (ou ouvrir le dossier s'il est déjà sur le disque)
git clone <adresse-du-dépôt> OCPMotorDiagnostic_Project
cd OCPMotorDiagnostic_Project

# 2. Copier les modèles de configuration (aucun secret n'est versionné)
copy .env.example .env              (PowerShell : Copy-Item .env.example .env)
cd backend
copy .env.example .env

# 3. Environnement virtuel Python + dépendances du backend
python -m venv .venv
.venv\Scripts\activate              (le prompt doit afficher (.venv))
pip install -r requirements.txt

# 4. Dépendances du frontend
cd ..\frontend
npm install
```

---

## Lancement (à chaque session de travail)

Il faut **trois choses qui tournent en parallèle** (trois fenêtres de terminal,
ou un seul terminal Docker Desktop + deux terminaux) :

### 1. Infrastructure : PostgreSQL + Mosquitto (Docker)

Démarrer **Docker Desktop**, puis :

```bash
cd OCPMotorDiagnostic_Project
docker compose up -d
```

Vérification : `docker compose ps` → les deux conteneurs doivent être `running`.

### 2. Backend FastAPI

```bash
cd OCPMotorDiagnostic_Project\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

- L'API répond sur **http://localhost:8000**
- Documentation interactive : **http://localhost:8000/docs**

### 3. Frontend React

```bash
cd OCPMotorDiagnostic_Project\frontend
npm run dev
```

- L'application s'ouvre sur **http://localhost:5173**

En développement, le serveur Vite transmet automatiquement les appels `/api` au
backend : le navigateur n'a besoin que de l'adresse du frontend.

---

## Tester l'Étape 1 (squelette)

1. Ouvrir **http://localhost:5173** : page sobre « OCP — Diagnostic Moteurs ».
2. La carte « État du système » doit afficher **« Backend connecté »**
   (sinon : le backend n'est pas lancé, voir plus haut).
3. Ouvrir **http://localhost:8000/api/v1/health** : réponse JSON
   `{"status": "ok", ...}`.
4. Ouvrir **http://localhost:8000/docs** : documentation FastAPI.

---

## Configuration (variables d'environnement)

- `.env` (racine) → valeurs de PostgreSQL/Mosquitto lues par Docker Compose.
- `backend/.env` → configuration du backend (nom, URL de base de données, broker MQTT).
- `.env.example` = modèles à copier ; les vrais `.env` ne sont jamais versionnés
  (fichier `.gitignore`).

---

## Structure du projet

```
├── docker-compose.yml      ← PostgreSQL + Mosquitto en un clic
├── infra/mosquitto/        ← configuration du broker MQTT
├── docs/                   ← plan de développement, documentation
├── backend/
│   ├── requirements.txt    ← dépendances Python
│   └── app/
│       ├── main.py         ← point d'entrée FastAPI
│       └── core/           ← configuration (variables d'environnement)
└── frontend/
    ├── package.json        ← dépendances React
    └── src/
        ├── main.jsx        ← démarrage React
        ├── App.jsx         ← page d'accueil (provisoire, Étape 1)
        └── styles.css      ← thème (palette inspirée OCP)
```

Les dossiers suivants seront ajoutés progressivement (voir `docs/PLAN_DEVELOPPEMENT.md`) :
`backend/app/api`, `backend/app/models`, `backend/app/services`, `backend/app/mqtt`,
`backend/app/ws`, `backend/app/pdf`, `backend/app/simulator`,
`backend/diagnostic_rules/`, `frontend/src/pages`, `frontend/src/components`,
`frontend/src/charts`, `frontend/src/services`, `frontend/src/websocket`,
`frontend/src/state`, puis `esp32/` et `data_legacy/` (étapes futures).

---

## Mini-glossaire (pour bien suivre le projet)

| Terme | Signification simple |
|---|---|
| **Backend** | Programme qui tourne sur le serveur : il gère les données et la logique (ici FastAPI). |
| **Frontend** | Ce qui s'affiche dans le navigateur (ici React). |
| **API / route** | « Porte d'entrée » du backend : une adresse précise qui attend des demandes et renvoie des réponses JSON. |
| **JSON** | Format texte universel pour échanger des données entre frontend et backend. |
| **MQTT / broker** | Protocole de messages léger ; le *broker* (Mosquitto) est le « facteur » qui relaie les messages du kit (ESP32) au backend. |
| **WebSocket** | Canal temps réel entre backend et navigateur (utilisé pour les mesures en direct). |
| **PostgreSQL** | Base de données : l'endroit où sont stockés moteurs, tests et mesures. |
| **Docker** | Outil qui fait tourner des logiciels (PostgreSQL, Mosquitto) dans des « conteneurs » isolés, sans installation compliquée. |
| **Migration (Alembic)** | Historique versionné des évolutions de la base de données (Étape 4). |
| **Endpoint** | Voir « API / route ». |

## Identité visuelle

L'interface reprend la charte du site OCP Group (vert & blanc) sans reproduire le site.
- Couleurs centralisées dans `frontend/src/theme/styles.css` (variables CSS `:root`).
- Emblème OCP : `frontend/public/brand/ocp-emblem.png`. L'emblème est la propriété
  d'OCP Group (usage interne au projet d'atelier). Pour utiliser le logo officiel
  complet, téléchargez-le depuis https://www.ocpgroup.ma et remplacez ce fichier
  (même nom) ; retirez-le si le dépôt doit devenir public.

## État d'avancement

- ✅ **Étape 1 — Squelette du projet** (dossiers, Docker Compose, backend et frontend minimaux) — *fusionnée via la PR #1*
- ✅ **Étape 2 — Frontend : navigation et écrans principaux** (8 écrans reliés, gabarit commun, thème)
- ✅ **Étape 3 — Backend : API de base** (routes moteurs/tests, validation Pydantic)
- ✅ **Étape 4 — PostgreSQL + modèles de données** (tables motors/tests/measurements, migrations Alembic, dépôts SQL, données persistantes)
- ✅ **Étape 5 — Formulaire de diagnostic manuel** (auto-remplissage si le moteur existe déjà, enregistrement réel via l'API, page de confirmation de la fiche)
- ✅ **Étape 6 — Historique complet** (filtres service/période/mode/décision, consultation de la fiche, archivage réel via PATCH — aucune suppression définitive)
- ✅ **Étape 7 — MQTT + simulateur ESP32** (backend abonné au broker, registre des kits, WebSocket temps réel, simulateur Python, page Connexion au kit réelle)
- ✅ **Étape 8 — Acquisition automatique ~60 s** (pilote backend, commandes MQTT start/stop au kit, table acquisition_samples, événements WebSocket, page Acquisition réelle avec START/QUIT et gestion de perte du kit)
- ✅ **Étape 9 — Page View Graph** (3 figures Recharts — température, courant, vibration — avec curseur/infobulle, min/max/moyenne/durée, rafraîchissement en direct pendant l'acquisition)
- ✅ **Étape 10 — Moteur de règles** (package modulaire `backend/diagnostic_rules/` : un module Python par paramètre ; règles fournies = courant à vide ⅓–⅔ In, isolement 1 kΩ/V, température 85 °C ; vibration et résistance d'enroulements préparées ; information manquante → « non évaluable », rien d'inventé)
- ✅ **Étape 11 — Page Analysis** (branchée sur le moteur : valeur mesurée, référence/seuil, résultat, interprétation, risque/recommandation si fournis ; synthèse factuelle ; conclusion générale automatique prévue plus tard ; décision technicien inchangée et indépendante)
- ✅ **Étape 12 — Rapport PDF** (fiche §16 à 10 rubriques, identique pour les 2 modes ; générée par le backend avec ReportLab — WeasyPrint indisponible dans le bac à sable ; `GET /api/v1/tests/{id}/report.pdf` + aperçu réel sur la page Rapport ; rien d'inventé : risques/recommandations/conclusion ne reprennent que les règles fournies)
- ✅ **12b — Analyse environnementale** (base de connaissances des 7 environnements dans `backend/diagnostic_rules/environment_*.py` : données séparées de la logique ; croisement environnement × anomalies détectées → hypothèses de causes POSSIBLES + contrôles recommandés, uniquement si une anomalie est réellement détectée ; conclusion générale automatique prudente ; champ « Service / Environnement » du moteur = liste des 7 environnements)
- ✅ **Étape 13 — Parcours auto complet** (la décision du technicien et son observation sont ENREGISTRÉES dans la fiche via `PATCH /tests/{id}` depuis la page Analyse — bouton « Enregistrer la décision », indicateur de décision déjà sauvegardée ; elles apparaissent dans le rapport et le PDF ; enchaînement complet vérifié : formulaire → acquisition → View graph → Analyse → décision → Rapport PDF)
- ✅ **Étape 14 — Tests, cas limites, finitions** (lanceur unique `backend/tools/run_tests.py` = 3 suites, 51 cas ; garde-fous : START d'acquisition refusé sur un test manuel (409), In ≤ 0 jamais divisé (non évaluable), saisies invalides refusées (422) ; rapport PDF et analyse robustes sur un test sans données ; nettoyage d'un résidu de code)
- ✅ **Étape 15 — Préparation base historique (691 relevés)** (outil `backend/tools/import_history.py` : CSV UTF-8 → base avec les MÊMES validations que l'API ; `--dry-run` pour vérifier sans écrire ; `id_origine` stockée en `tests.source_ref` (migration 0004, index unique) → réimport sans doublons ; rapport d'erreurs ligne par ligne exportable ; dates historiques, décisions et environnements conservés ; procédure complète dans `docs/IMPORT_HISTORIQUE.md` ; exemple `backend/tools/exemple_import_historique.csv`)
- ✅ **Étape 16 — Workflow en étapes + nouvelles mesures (décisions client)** (migration 0005 : continuité globale Oui/Non, 2 températures de paliers « Côté accouplement / C.O.A » avec règle **< 70 °C** comme la fiche papier, références facultatives des appareils de mesure, zone administrative Sce demandeur / AVIS / ORDRE / date de réception / réparation interne-externe ; nouvelles validations API `validate-offline` puis `validate-online` (statuts `draft → offline_validated → completed`, refus 409 sinon) ; la fin d'acquisition kit ne valide PLUS le test sous tension — validation explicite du technicien ; la série du kit redevient un graphique sans règle ; ancienne température unique conservée (seuil historique 85 °C) ; **vitesse retirée des mesures** — elle reste sur la plaque signalétique)
- ✅ **Étape 17 — Parcours en étapes côté interface (accueil = formulaire moteur)** (la page d'accueil porte directement la fiche moteur : ID, informations constructeur, service/environnement, avec auto-remplissage si le moteur est connu ; deux boutons aux extrémités : **Registre** à gauche (fonction à venir, définition client en attente) et **Test** à droite → test hors tension ; nouvelle page **Test hors tension** (résistances + continuité Oui/Non + isolement) qui crée et valide la session ; nouvelle page **Test sous tension** : **Manuel** à gauche (saisie → VALIDER LE TEST) ou **Continuer avec le kit** à droite (session passe en auto → acquisition 60 s avec sélection automatique du kit en ligne → retour pour valider) ; l'ancien formulaire unique est retiré ; le bouton Rapport n'existe toujours que depuis l'Analyse)
- ✅ **Étape 18 — Analyse à jour des nouvelles données** (le récapitulatif « Mesures enregistrées » affiche la continuité Oui/Non, les 2 températures de paliers, l'ancienne température unique étiquetée « ancien format », et les références des appareils de mesure ; la zone administrative de la fiche papier (Sce demandeur, AVIS, ORDRE, date de réception, réparation interne/externe) apparaît dès qu'elle est renseignée ; les cartes d'analyse par paramètre restent génériques : continuité et paliers s'y affichent déjà avec leur évaluation)
- ✅ **Étape 19 — Rapport PDF « FICHE D'ESSAI MOTEUR »** (le PDF reprend la structure de la fiche papier : en-tête logo + titre + n° de diagnostic + version + date d'essai ; identification complète de la plaque ; tables « Mesure | mesure | unité | Valeur Réf | Observation » pour l'isolement (Rmin = 1 kΩ/V), les résistances (+ « Continuité des enroulements : Oui/Non »), le courant à vide (limites In/3 – 2In/3), les températures de paliers (< 70 °C, valeur unique ancienne étiquetée) et la vibration ; références des appareils ; observation du technicien ; zone administrative ; « Équipement conforme : [ ] Oui [ ] Non » coché selon la décision, décision finale, date et visa ; l'interprétation (causes, risques, recommandations) reste sur la page Analyse — le PDF est la preuve du test)
- ✅ **Registre numérique des moteurs (décision client)** (migration 0007 : table `registre_entries` reprenant les 20 colonnes du fichier Excel `registre_moteurs_1.xlsx` dans le même ordre ; le bouton **Registre** de l'accueil ouvre la page `/registre` qui affiche le tableau exact — intitulés et unités conservés, rien ajouté ni renommé ; le registre réunit les données **historiques importées** et les **essais de l'application**, ajoutés automatiquement après la décision du technicien ; **une ligne par essai, jamais remplacée ni supprimée** ; champs absents laissés vides — rien d'inventé ; le retour au formulaire depuis le registre préserve la saisie en cours ; correspondance centralisée dans `backend/app/services/registre.py`, complément idempotent via `backend/tools/backfill_registre.py`)

### Structure du backend (Étapes 3 et 4)

```
backend/
├── alembic/             ← migrations de la base (versionnées)
│   ├── env.py           ← relie Alembic aux modèles + à la configuration
│   └── versions/        ← une migration par évolution du schéma
├── alembic.ini          ← configuration d'Alembic
└── app/
    ├── main.py            ← point d'entrée FastAPI (assemble tout)
    ├── core/config.py     ← configuration par variables d'environnement
    ├── api/               ← les routes HTTP (moteurs, tests)
    │   ├── router.py      ← assemble les routes sous /api/v1
    │   ├── motors.py      ← routes des moteurs
    │   ├── tests.py       ← routes des tests de diagnostic
    │   └── deps.py        ← fournit les dépôts aux routes
    ├── db/session.py      ← connexion PostgreSQL (engine + sessions)
    ├── models/            ← les tables SQLAlchemy (motors, tests, measurements)
    ├── schemas/           ← validation Pydantic (motors, tests)
    ├── repositories/      ← accès aux données
    │   ├── sql/           ←   version PostgreSQL (utilisée)
    │   └── serializers.py ←   conversion lignes SQL → dictionnaires API
    └── services/          ← logique métier (création d'un test)
```

### Commandes base de données (Étape 4)

Depuis `backend/` (après `docker compose up -d`) :

```bash
.venv\Scripts\activate
alembic upgrade head        # applique les migrations (crée les tables)
alembic current             # montre la version appliquée
alembic downgrade -1        # annule la dernière migration
```

Pour ajouter une migration après modification d'un modèle :
`alembic revision --autogenerate -m "description"` puis vérifier le fichier
généré dans `backend/alembic/versions/` avant de l'appliquer.

Chaque étape est validée avec le stagiaire avant de passer à la suivante.
