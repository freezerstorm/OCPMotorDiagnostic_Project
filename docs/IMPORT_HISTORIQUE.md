# Import de la base historique (Étape 15)

Cette procédure permet d'intégrer en masse les relevés historiques
(≈ 691 lignes) dans l'application, depuis un fichier **CSV**.

## Principe

```
EXPORT actuel (Excel…) → CSV UTF-8 → DRY-RUN (vérification) → IMPORT
```

- Les lignes sont validées avec **les mêmes règles que l'API**
  (unités, tension de test limitée à 500/1000/2500/5000 V, décision
  limitée aux 2 valeurs, courant nominal > 0…) : **une ligne invalide
  n'est jamais importée**.
- Chaque ligne porte une **`id_origine`** (son référence dans le
  fichier d'origine). Elle est stockée avec la fiche
  (`tests.source_ref`) → **réimporter le même fichier ne crée aucun
  doublon**.
- Les **moteurs inconnus sont créés** ; un moteur déjà connu n'est
  **pas modifié** (les données du fichier ne l'écrasent pas).
- La **date du relevé** est conservée (la fiche apparaît à sa date
  historique dans l'application).

## 1. Préparer le fichier CSV

- Encodage **UTF-8** (l'export Excel « CSV UTF-8 » convient) ;
- Séparateur **`,`** ou **`;`** (détecté automatiquement) ;
- Décimales **avec ou sans virgule** (`12,5` ou `12.5`) ;
- En-têtes attendus (1ʳᵉ ligne) — l'ordre est libre, les colonnes
  facultatives peuvent être vides ou absentes :

| En-tête | Obligatoire | Contenu |
|---|---|---|
| `id_origine`            | conseillée | référence de la ligne dans ta base d'origine (traçabilité + anti-doublon ; sinon construite `moteur:date`) |
| `id_moteur`             | **oui**    | identifiant moteur (ex. `M-1042`) |
| `matricule`, `designation`, `marque`, `modele`, `n_fabrication` | non | plaque moteur |
| `date_test`             | **oui**    | `JJ/MM/AAAA` (ou `AAAA-MM-JJ`) |
| `mode`                  | non        | `manuel` (par défaut) ou `automatique` |
| `environnement`         | non        | un des 7 environnements (ex. `Laverie / Lavage / Décantation`) |
| `puissance_kw`, `tension_v`, `courant_nominal_a`, `vitesse_tr_min`, `cos_phi` | non | plaque |
| `tension_test_isolement_v` | si isolement saisi | 500 / 1000 / 2500 / 5000 |
| `isolement_ph1_ph2_mohm` … `isolement_ph3_masse_mohm` | non | 6 mesures en MΩ |
| `r12_ohm`, `r23_ohm`, `r31_ohm` | non | résistances en Ω |
| `continuite` (ou `continuite_enroulements`) | non | Oui / Non — appréciation globale |
| `temp_palier_couplage_c`, `temp_palier_coa_c` | non | températures de paliers en °C (règle < 70 °C) |
| `temperature_c` | non | température UNIQUE — ancien format (évaluée avec l'ancien seuil 85 °C) |
| `temperature_c`, `courant_a`, `vibration_mm_s` | non | mesures de fonctionnement |
| `decision`              | non        | `Remis en service` ou `Envoyé en réparation` |
| `observation`           | non        | texte libre |

Un exemple complet figure dans
`backend/tools/exemple_import_historique.csv`.

## 2. Vérifier SANS importer (dry-run)

Depuis le dossier `backend/` :

```bash
python tools/import_history.py MON_FICHIER.csv --dry-run --report erreurs.csv
```

- Le fichier est **entièrement validé**, rien n'est écrit ;
- les lignes en erreur sont listées (numéro de ligne + raison) et
  exportées dans `erreurs.csv` — corrige le fichier et relance
  jusqu'à obtenir **0 erreur** (le code retour est 1 tant qu'il reste
  des erreurs).

## 3. Importer

```bash
python tools/import_history.py MON_FICHIER.csv
```

- Résumé : `X fiche(s) créée(s), Y déjà présente(s) (ignorée(s))` ;
- en cas d'interruption, **relancer le même fichier** : les lignes déjà
  importées sont détectées par `id_origine` et ignorées.

## 4. Vérifier dans l'application

- **Historique** : les fiches importées apparaissent à leur date
  historique, avec leur décision ;
- **Analyse** : les règles (courant, isolement, température,
  enroulements) et l'analyse environnementale s'appliquent normalement
  à ces fiches ;
- **Rapport PDF** : généré comme pour toute fiche.

## Limites et points à confirmer

- Cette procédure suppose que l'export actuel peut produire un CSV
  (Excel le fait nativement). Si la source est un **autre système**
  (base de données, logiciel), dis-le : l'outil pourra être adapté
  (le format CSV reste l'interface).
- Les **noms exacts des colonnes** de ton export réel sont à confirmer
  (la table ci-dessus est la convention proposée ; les alias se
  règlent dans `HEADER_ALIASES` de `tools/import_history.py`).
- **Ne pas importer deux fois** deux fichiers contenant des lignes
  différentes avec la même `id_origine` (la 2ᵉ serait ignorée).
- Volume : 691 lignes ne posent aucun problème (import ligne à ligne,
  quelques secondes).
