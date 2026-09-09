# Plan de développement — Kit de diagnostic moteurs électriques (OCP)

> Document de référence du projet. Étape 0 : analyse du cahier des charges.
> Ce plan est mis à jour au fil des étapes. Aucune décision technique n'est inventée :
> tout ce qui est hypothèse est marqué (H#) et sera confirmé avant utilisation.

## Avancement

| Étape | Statut | Validation stagiaire |
|---|---|---|
| 0 — Analyse + plan | ✅ Fait | ✅ |
| 1 — Squelette du projet | ✅ Fait | ✅ (fusionné dans main) |
| 2 — Frontend navigation | ✅ Fait | ✅ (fusionné dans main) |
| 3 — Backend API de base | ✅ Fait | En attente de validation |
| 4 — PostgreSQL + modèles SQLAlchemy + Alembic | ✅ Fait | En attente de validation |
| 10a — Squelette du moteur de règles | 🧩 Fait (structure + règle courant à vide) | En attente |
| 5 — Formulaire test manuel (mesures) | | |
| 6 — Historique complet | | |
| 7 — MQTT + simulateur | | |
| 8 — Acquisition auto ~60 s | | |
| 9 — View Graph (Recharts) | | |
| 10b — Autres règles de diagnostic | | |
| 11 — Page Analysis | | |
| 12 — Rapport PDF (WeasyPrint) | | |
| 13 — Parcours auto complet | | |
| 14 — Tests et finitions | | |
| 15 — Architecture base historique | | |
| 5 — Formulaire + test manuel | | |
| 6 — Historique | | |
| 7 — MQTT + simulateur | | |
| 8 — Acquisition automatique | | |
| 9 — View Graph | | |
| 10 — Moteur de règles | | |
| 11 — Page Analysis | | |
| 12 — Rapport PDF | | |
| 13 — Parcours auto complet | | |
| 14 — Tests et finitions | | |
| 15 — Préparation base historique | | |

---

## 1. Objectif

Application web de **diagnostic ponctuel** (~60 s) de moteurs électriques en atelier,
avec deux modes (manuel / automatique via kit ESP32) qui aboutissent à **une seule
fiche de diagnostic**, un **seul historique** et un **même rapport PDF**.

## 2. Technologies (confirmées)

- Frontend : **React.js** (Vite), Recharts (graphiques), WebSocket natif
- Backend : **Python + FastAPI** (uvicorn)
- Communication kit : **MQTT** (broker **Mosquitto**, client paho-mqtt)
- Base de données : **PostgreSQL** (SQLAlchemy 2 + Alembic pour les migrations)
- Temps réel : **WebSocket** (backend → navigateur)
- PDF : **WeasyPrint** (modèle HTML/CSS reproduisant l'esprit de la fiche d'essai OCP)
- Interface : **français** ; identifiants de code en anglais ; palette sobre inspirée
  de l'identité OCP (sans reproduire le site)
- Configuration : variables d'environnement (fichiers `.env`, jamais de secret en dur)

## 3. Arborescence cible

```
OCPMotorDiagnostic_Project/
├── README.md                  ← mode d'emploi général
├── .env.example               ← modèle des variables d'environnement
├── .gitignore
├── docker-compose.yml         ← PostgreSQL + Mosquitto
├── docs/                      ← documentation du projet
├── backend/                   ← Python / FastAPI
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic/               ← migrations de la base
│   ├── app/
│   │   ├── main.py            ← point d'entrée FastAPI
│   │   ├── core/              ← configuration (variables d'environnement)
│   │   ├── api/               ← routes HTTP (moteurs, tests, historique, rapport…)
│   │   ├── models/            ← tables SQLAlchemy
│   │   ├── schemas/           ← validation Pydantic
│   │   ├── services/          ← logique métier
│   │   ├── db/                ← connexion PostgreSQL
│   │   ├── mqtt/              ← client MQTT (kits)
│   │   ├── ws/                ← WebSocket vers navigateur
│   │   ├── pdf/               ← génération du rapport PDF
│   │   └── simulator/         ← simulateur ESP32 (développement sans kit)
│   └── diagnostic_rules/      ← ⭐ moteur de règles indépendant
│       ├── engine.py
│       ├── base.py
│       ├── current_rules.py
│       ├── temperature_rules.py
│       ├── vibration_rules.py
│       ├── insulation_rules.py
│       └── winding_resistance_rules.py
├── frontend/                  ← React / Vite
│   └── src/
│       ├── main.jsx / App.jsx ← démarrage + navigation
│       ├── theme/             ← palette OCP + style commun
│       ├── layouts/           ← gabarit commun (en-tête, menu)
│       ├── pages/             ← Accueil, ConnexionKit, FormulaireMoteur,
│       │                         Acquisition, ViewGraph, Analyse, Rapport, Historique
│       ├── components/        ← blocs réutilisables
│       ├── charts/            ← 3 graphiques (TEMP / COURANT / VIBRATION)
│       ├── services/          ← appels API
│       ├── websocket/         ← temps réel
│       └── state/             ← état partagé
├── esp32/                     ← (PLUS TARD) firmware du vrai kit
└── data_legacy/               ← (PLUS TARD) import des 691 relevés papier
```

Règle de conception : chaque métier est isolé (règles / MQTT / PDF / historique…),
aucun fichier géant, un module remplaçable sans casser le reste.

## 4. Données principales (aperçu, détaillé à l'ÉTAPE 4)

- **motors** : identification + caractéristiques plaque (matricule, puissance, In, Un,
  vitesse, cos φ, couplage, service, DI/OT…). Un moteur = plusieurs tests possibles.
- **tests** : 1 par diagnostic — mode (manuel/auto), kit_id, statut, dates,
  décision technicien, observation, conclusion automatique.
- **mesures automatiques** (série temporelle, une ligne par instant) : temps,
  température, courant, vibration x/y/z + grandeur globale.
- **mesures manuelles** : isolement (Ph-Ph ×3, Ph-Masse ×3) + résistance R12/R23/R31.

Conception orientée « données temporelles » sans rendre TimescaleDB obligatoire
(ajout possible plus tard sans réécriture).

## 5. Parcours applicatif

```
ACCUEIL
  ├─ Nouveau test MANUEL → Formulaire moteur → Saisie des mesures → Analysis → Rapport
  └─ Nouveau test AUTO → Connexion kit → Formulaire moteur → START
       → Acquisition ~60 s → View Graph → Analysis → Rapport
Historique accessible depuis l'Accueil (consultation, rapport, archiver — pas de suppression)
```

## 6. Hypothèses techniques (à confirmer — aucune n'est un fait établi)

| # | Hypothèse | Domaine | Trancher à l'étape |
|---|---|---|---|
| H1 | Vibration exprimée en accélération (g) ; 3 axes + valeur globale enregistrés | Règles / graphiques | 7–8 |
| H2 | Un seul SCT-013 → courant d'une phase (moteur supposé équilibré) | Interprétation | 8 |
| H3 | Essai moteur réalisé à vide en atelier | Règles courant | 10 |
| H4 | ~1 à 10 mesures/s pendant 60 s (valeurs moyennées côté kit) | Stockage | 8 |
| H5 | PT100 œillet fixé sur carcasse/boîtier | Seuils température | 10 |
| H6 | DI = demande d'intervention, OT = ordre de travail (champ libre) | Formulaire | 5 |
| H7 | Règle courant à vide 1/3–2/3 In implémentée telle quelle ; littérature souvent ~25–40 % In → à vérifier | Règles | 10 |
| H8 | Pas d'authentification dans le MVP | — | Étape 0 |

## 7. Ordre de développement (validation requise entre chaque étape)

1. **Squelette du projet** : arborescence, README, `.env.example`, Docker Compose
   (PostgreSQL + Mosquitto), backend et frontend minimaux qui tournent.
2. **Frontend navigation** : 8 écrans reliés, habillage sobre inspiré OCP.
3. **Backend API de base** : routes moteurs/tests en JSON (mémoire), `/docs`.
4. **PostgreSQL + modèles** : tables, migrations Alembic.
5. **Formulaire moteur + test manuel** : auto-remplissage si moteur connu.
6. **Historique** : tableau type Google Sheets, recherche, filtres, consulter,
   rapport, archiver (pas de suppression).
7. **MQTT + simulateur ESP32** : broker, abonnement backend, simulateur Python,
   page Connexion kit avec états.
8. **Acquisition auto ~60 s** : START (kit connecté uniquement), QUIT, états
   IDLE→READY→ACQUIRING→COMPLETED/ERROR, perte de connexion gérée.
9. **View Graph** : 3 figures distinctes + curseur/tooltip + min/max/moyenne/durée.
10. **Moteur de règles** : `diagnostic_rules/`, règle courant à vide (1/3–2/3 In),
    autres modules prêts avec « seuils à définir » (aucune invention).
11. **Page Analysis** : analyse par paramètre + conclusion auto + décision technicien
    + observation.
12. **Rapport PDF** : WeasyPrint, structure fiche d'essai, identique pour les 2 modes.
13. **Intégration du parcours automatique complet**.
14. **Tests, cas limites, finitions d'interface**.
15. **Architecture d'intégration future de la base historique (691 relevés)**.

## 8. Principes de travail

- Explications simples à chaque étape : fichiers créés/modifiés, rôle, lancement, test.
- Commit Git par étape.
- Aucune donnée fictive présentée comme réelle.
- Les seuils/règles techniques arrivent uniquement quand le stagiaire les fournit.
