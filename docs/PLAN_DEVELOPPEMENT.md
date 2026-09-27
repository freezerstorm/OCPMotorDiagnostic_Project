# Plan de développement — Kit de diagnostic moteurs électriques (OCP)

> Document de référence du projet. Étape 0 : analyse du cahier des charges.
> Ce plan est mis à jour au fil des étapes. Aucune décision technique n'est inventée :
> tout ce qui est hypothèse est marqué (H#) et sera confirmé avant utilisation.

## Avancement

| Étape | Statut | Validation stagiaire |
|---|---|---|
| 0 — Analyse + plan | ✅ Fait | ✅ Validé (plan GO, Windows, Docker, simulateur d'abord) |
| 1 — Squelette du projet | ✅ Fait | ✅ Validé (fusionné via la PR #1) |
| 2 — Frontend navigation | ✅ Fait | ⏳ À valider (commits locaux prêts à pousser) |
| 3 — Backend API de base | ✅ Fait | ⏳ À valider (commits locaux prêts à pousser) |
| 4 — PostgreSQL + modèles | ✅ Fait | ⏳ À valider (testé sur PostgreSQL 16 réel) |
| 5 — Formulaire + test manuel | ✅ Fait | ⏳ À valider (auto-remplissage + enregistrement réels) |
| 3 — Backend API de base | | |
| 4 — PostgreSQL + modèles | | |
| 5 — Formulaire + test manuel | | |
| 6 — Historique | ✅ Fait | ⏳ À valider (archivage réel, pas de suppression) |
| 7 — MQTT + simulateur | ✅ Fait | ⏳ À valider (broker, simulateur, page connexion kit temps réel) |
| 8 — Acquisition automatique | ✅ Fait (validée) (états IDLE→READY→ACQUIRING→COMPLETED/ERROR, stockage série temporelle) |
| 9 — View Graph | ✅ Fait (validée) | 3 figures Recharts, min/max/moyenne/durée, live 2 s |
| 10 — Moteur de règles | ✅ Fait (validée) | Modules Python diagnostic_rules/ : courant ⅓–⅔ In, isolement 1 kΩ/V, température 85 °C, enroulements R12=R23=R31 ; non évaluable si info manquante |
| 11 — Page Analysis | ✅ Fait (validée) | Branchée au moteur ; décision technicien inchangée ; conclusion générale plus tard |
| 12 — Rapport PDF | ✅ Fait | ReportLab — WeasyPrint indisponible dans le bac à sable ; fiche §16 identique 2 modes ; GET /tests/{id}/report.pdf |
| 12b — Analyse environnementale | ✅ Fait (validée) | Base de connaissances 7 environnements ; hypothèses de causes uniquement sur anomalie détectée ; conclusion générale prudente |
| 13 — Parcours auto complet | ✅ Fait (validée) | Décision technicien + observation enregistrées via PATCH ; enchaînement complet vérifié |
| 14 — Tests et finitions | ✅ Fait (validée) | 3 suites = 55 cas via tools/run_tests.py ; garde-fous START manuel + In ≤ 0 ; PDF et analyse robustes sans données |
| 15 — Préparation base historique | ✅ Fait | ⏳ À valider (tools/import_history.py : CSV → base, validations API réutilisées, id_origine anti-doublons, dry-run, rapport d erreurs ; docs/IMPORT_HISTORIQUE.md) |
| 16 — Workflow en étapes + nouvelles mesures (continuité, paliers 70 °C, appareils, admin) | ✅ Fait | ⏳ À valider (migration 0005 ; validations API validate-offline/validate-online ; règle continuité ; règle paliers < 70 °C ; vitesse retirée des mesures ; front des étapes à venir) |
| 17 — Parcours en étapes côté interface | ✅ Fait | ⏳ À valider (accueil = formulaire moteur + Registre/Test aux extrémités ; Test hors tension ; Test sous tension Manuel/Kit ; ANALYSIS et PDF inchangés) |
| 18 — Analyse à jour (continuité, paliers, appareils, admin) | ✅ Fait | ⏳ À valider (récapitulatif des mesures enrichi + zone administrative affichée si renseignée) |
| 19 — Rapport PDF « FICHE D'ESSAI MOTEUR » | ✅ Fait | ⏳ À valider (structure de la fiche papier : tables mesure/unité/référence/observation, conforme Oui/Non, décision, visa) |

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

## 4. Données principales (détaillé à l'ÉTAPE 4 — réalisé)

- **motors** : identification + caractéristiques plaque (matricule, puissance, In, Un,
  vitesse, cos φ, couplage, service, DI/OT…). Un moteur = plusieurs tests possibles.
  Clé primaire = motor_id (clé de l'auto-remplissage).
- **tests** : 1 par diagnostic — mode (manuel/auto), statut, décision technicien,
  observation ; identifiant lisible test_id « T-0001 » (séquence SQL test_id_seq) ;
  clé interne id auto-incrémentée.
- **measurements** : 1 ligne par test — isolement (Ph-Ph ×3, Ph-Masse ×3),
  résistance R12/R23/R31, valeurs instantanées température/courant/vibration.
- Évolution : schéma initial versionné par Alembic (migration 0001). Les séries
  temporelles du kit (acquisition ~60 s) seront stockées dans une table dédiée
  (Étape 8) — conception orientée « données temporelles » sans TimescaleDB
  obligatoire (ajout possible plus tard sans réécriture).

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
| H1 | ~~Vibration exprimée en accélération (g)~~ **TRANCHÉ (client, 17/09/2026) : la vibration est en mm/s partout** — le kit publie la vitesse vibratoire directement (3 axes + valeur globale, mm/s) | Règles / graphiques | 7–8 |
| H2 | Un seul SCT-013 → courant d'une phase (moteur supposé équilibré) | Interprétation | 8 |
| H3 | Essai moteur réalisé à vide en atelier | Règles courant | 10 |
| H4 | ~1 à 10 mesures/s pendant 60 s (valeurs moyennées côté kit) | Stockage | 8 |
| H5 | PT100 œillet fixé sur carcasse/boîtier | Seuils température | 10 |
| H6 | DI = demande d'intervention, OT = ordre de travail (champ libre) | Formulaire | 5 |
| H7 | Règle courant à vide 1/3–2/3 In implémentée telle quelle ; littérature souvent ~25–40 % In → à vérifier | Règles | 10 |
| H8 | Pas d'authentification dans le MVP | — | Étape 0 |
| H9 | Vibration saisie manuellement exprimée en mm/s (appareil du technicien) ; **TRANCHÉ (17/09/2026) : le kit publie aussi en mm/s** (voir H1) | Schémas API | 3 |

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
