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

## Comment tester l'étape actuelle (étapes 3-4)

1. Lancer le backend (en stockage mémoire pour tester sans PostgreSQL) :
   ```bash
   cd backend
   STORAGE_BACKEND=memory .venv/bin/uvicorn app.main:app --reload --port 8000
   ```
   (Sous Windows PowerShell : `$env:STORAGE_BACKEND="memory"; uvicorn app.main:app --reload --port 8000`)
2. Lancer le frontend dans un second terminal :
   ```bash
   cd frontend
   npm run dev
   ```
3. Ouvrir **http://localhost:5173** :
   - la sidebar doit indiquer **« Backend opérationnel »** (pastille verte) ;
   - cliquer sur **Nouveau test manuel** → remplir au moins l'ID moteur → Continuer ;
   - retour à l'accueil : la carte « Derniers tests » affiche le moteur créé ;
   - la page **Historique** affiche une ligne par diagnostic.
4. Documentation interactive de l'API : **http://localhost:8000/docs**.
5. Pour activer PostgreSQL (mode « sql »), lancer `docker compose up -d` puis
   positionner `STORAGE_BACKEND=sql` dans `backend/.env` et appliquer les
   migrations : `alembic upgrade head`.

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
│   ├── requirements.txt
│   ├── alembic.ini         ← migrations Alembic
│   ├── alembic/            ← versions de migration (0001_initial_schema…)
│   └── app/
│       ├── main.py         ← point d'entrée FastAPI
│       ├── core/           ← configuration (variables d'environnement)
│       ├── api/            ← routes HTTP (health, motors, tests)
│       ├── models/         ← modèles SQLAlchemy (motors, tests, mesures)
│       ├── schemas/        ← validation Pydantic
│       ├── services/       ← logique métier
│       └── db/             ← connexion PostgreSQL
├── diagnostic_rules/       ← ⭐ moteur de règles indépendant (par paramètre)
└── frontend/
    ├── package.json
    └── src/
        ├── main.jsx        ← démarrage React
        ├── App.jsx         ← routage + assembleur
        ├── styles.css      ← thème (palette inspirée OCP)
        ├── components/     ← blocs réutilisables (cartes, badges, tableaux)
        ├── pages/          ← 8 pages (un fichier par écran)
        ├── services/       ← appels API
        └── state/          ← utilitaires d'état (sessionStorage pour l'instant)
```

Les dossiers suivants seront ajoutés/remplis progressivement :
`backend/app/mqtt`, `backend/app/ws`, `backend/app/pdf`, `backend/app/simulator`,
`frontend/src/charts`, `frontend/src/websocket`, puis `esp32/` et `data_legacy/`
(étapes futures).

---

## État d'avancement

- ✅ **Étape 0** — Analyse initiale + plan (`docs/00_ANALYSE_INITIALE.md`)
- ✅ **Étape 1** — Squelette du projet (dossiers, Docker Compose, backend/frontend minimaux)
- ✅ **Étape 2** — Frontend navigation et 8 écrans
- ✅ **Étape 3** — Backend API de base (routes `/api/v1/motors`, `/api/v1/tests`, schémas, services, stockage mémoire)
- ✅ **Étape 4** — Modèles SQLAlchemy (motors, diagnostic_tests, manual_measurements, time_series) + migration Alembic initiale
- 🧩 Squelette du **moteur de règles** (`diagnostic_rules/`) avec la règle courant à vide implémentée ; les autres règles sont en placeholder « seuils à définir » (aucune valeur inventée)
- ⏳ Étape 5 — Formulaire de diagnostic manuel (mesures d'isolement et résistances)
- ⏳ Étape 6 — Historique complet (filtres, archivage)
- …

Chaque étape est validée avec le stagiaire avant de passer à la suivante.
