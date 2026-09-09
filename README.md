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

## État d'avancement

- ✅ **Étape 1 — Squelette du projet** (dossiers, Docker Compose, backend et frontend minimaux)
- ⏳ Étape 2 — Frontend : navigation et écrans principaux

Chaque étape est validée avec le stagiaire avant de passer à la suivante.
