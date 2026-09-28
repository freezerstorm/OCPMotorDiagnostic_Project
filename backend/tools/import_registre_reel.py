"""IMPORT DU REGISTRE RÉEL — fichier JSON du client (export de p1).

Lit le fichier JSON fourni par le client (liste d'objets, 14 champs :
Date, Mat, DIT/OT, Service (Sce), Un, In, U0, I0, Isolement, Nature,
Puissance (P), Société, BT/MT (Tension), Observation) et remplit :

  - le REGISTRE (une ligne par objet, valeurs BRUTES conservées) ;
  - les FICHES MOTEUR (créées ou complétées quand une valeur est
    exploitable : Un/In/Puissance à valeur unique, Service, Nature =
    désignation, DI/OT).

NETTOYAGE APPLIQUÉ (rien n'est inventé) :
  - null, « - », « ~ », « -> » → cellule VIDE (valeur non renseignée) ;
  - DÉCALAGE DE COLONNES corrigé quand il est certain : sur une partie
    du fichier, les cases « Isolement » et « Nature » sont INVERSÉES
    (ex. Isolement = « M.E » et Nature = « 4 GΩ »). La correction
    échange les deux valeurs et est JOURNALISÉE ligne par ligne ;
  - de même, « Société » et « BT/MT (Tension) » sont inversées sur une
    partie du fichier (tension « BT »/« MT » en Société, société de
    réparation « FAR »/« AB »… en BT/MT). L'échange n'est fait que
    quand il est ÉVIDENT (les deux indices convergent — décision
    client 26/09/2026) et journalisé ligne par ligne ;
  - les autres particularités du fichier (ex. « I0 = 102V »,
    « Puissance = FAZAHT ») sont conservées TELLES QUELLES.

IDEMPOTENCE : chaque ligne porte la référence « JSON:<position> » ;
ré-importer le même fichier ne crée aucun doublon.

Usage (depuis backend/) :

    python tools/import_registre_reel.py registre_reel_complet.json [--dry-run]
    python tools/import_registre_reel.py FICHIER.json
    python tools/import_registre_reel.py FICHIER.json --lot JSON-C1

FORMATS ACCEPTÉS (le fichier client a évolué) :
  - premier export : « Mat », « Un » (« 500V » en texte) ;
  - exports suivants : « Mat / N° », « Un (V) » (525.0 en nombre) —
    le nombre est mis au format du registre (« 525V », « 16,5A »),
    l'unité venant de l'intitulé de la colonne ;
  - exports n°2 et suivants (clés minuscules) : « matricule »,
    « dit_ot », « un_v », « in_a », « u0_v », « i0_a »… avec des
    VALEURS TEXTE ; un nombre seul (« "525" », « "16,5" ») reçoit
    l'unité de sa colonne (« 525V », « 16,5A »), le reste est
    conservé verbatim ;
  - FORMAT 4 (lot 4, 24-05-25 → 16-05-26) : clés « date », « mle_ns »,
    « di_ot », « couplage », « service », « un_v », « in_a », « u0_v »,
    « i0_a », « nature », « isolement_ph_ph », « isolement_ph_m »,
    « r », « puissance », « tension », « societe », « observation ».
    Trois colonnes nouvelles : Couplage, R et Isolement ph-m. Les
    décalages de fin de lot sont RÉALIGNÉS à l'import (annoncé au
    client) et JOURNALISÉS ligne par ligne :
      · bloc où « Nature » contient « …V / …A » (double de U0/I0) :
        toute la chaîne est décalée d'un cran (Nature ← Isolement
        ph-ph ← Isolement ph-m ← R ← Puissance ← Tension ← Société) ;
      · ligne où une 2ᵉ résistance s'intercale entre R et Puissance ;
      · ligne où R est logée dans la cellule d'isolement (« Poste S ») ;
      · lignes où Matricule et DI/OT sont inversés.
    La cellule « …V / …A » (doublon exact de U0/I0) n'a pas de colonne
    dans le registre : elle est abandonnée et signalée en log.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.motor import Motor  # noqa: E402
from app.models.registre import RegistreEntry  # noqa: E402
from tools.import_registre import parse_date  # noqa: E402

# Valeurs du fichier signifiant « information non renseignée ».
PLACEHOLDERS = {"-", "~", "->", "→", ""}

# Lignes EXCLUES de l'import (décision du client, 24/09/2026) :
#   - « JSON-C3:518 » : au-delà de la fin réelle du registre (le
#     client avait annoncé 517 lignes au lot 4) ;
#   - « JSON-C3:229 » : Matricule = « 11175103 » = DI/OT de la
#     ligne 153 (incohérence) — suppression préférée à la correction.
# Le fichier JSON reste la transcription VERBATIM de la source : ce
# sont les règles d'import qui ignorent ces lignes (et les journaillent).
LIGNES_EXCLUES = {
    "JSON-C3:518": "au-delà de la fin réelle du registre (client : 517 lignes)",
    "JSON-C3:229": "Matricule = DI/OT de la ligne 153 (incohérence)",
}

# Corrections ponctuelles de cellules (décisions client 26/09/2026) :
#   - « JSON-C3:181 » : la Puissance « 85 / 75 GΩ » (valeurs
#     d'isolement) est EFFACÉE — la ligne reste au registre ;
#   - « JSON-C3:96 » : l'isolement ph-m abrégé « 220 M » est complété
#     en « 220 MΩ » (unité manquante).
CORRECTIONS_CELLULES = {
    "JSON-C3:181": {"puissance": None},
    "JSON-C3:96": {"isolement_ph_m": "220 MΩ"},
}

# Valeur d'ISOLEMENT : contient une unité d'isolement (GΩ, MΩ, kΩ, Ω,
# « 3G / 6G », « 10/236 G.m »…).
_ISOLEMENT_RE = re.compile(r"Ω|G\.m|^\s*\d+([.,]\d+)?\s*G(\s*/\s*\d+\s*G)?\s*$", re.IGNORECASE)

# Format 4 — cellule « Nature » du bloc décalé : « 500V / 1,5 A »
# (doublon de U0/I0 de la même ligne).
_VA_RE = re.compile(r"^\d+V\s*/\s*[\d.,]+\s*A$")

# Format 4 — valeur de PUISSANCE (« 5,5 kW », « 315/290 kW », « 3 HP »…).
_PUISSANCE_RE = re.compile(r"(kW|W|HP|CV|kVA)$", re.IGNORECASE)

# Valeur NUMÉRIQUE unique avec unité (pour les fiches moteurs).
_SINGLE = {
    "V": re.compile(r"^(\d+(?:[.,]\d+)?)\s*k?V$", re.IGNORECASE),
    "A": re.compile(r"^(\d+(?:[.,]\d+)?)\s*A$", re.IGNORECASE),
    "W": re.compile(r"^(\d+(?:[.,]\d+)?)\s*(?:kW|W)$", re.IGNORECASE),
}


def clean(value) -> str | None:
    """null / « - » / « ~ » / « -> » / espaces → None (cellule vide)."""
    if value is None:
        return None
    text = str(value).strip()
    return None if text in PLACEHOLDERS else text


def get_first(item: dict, *keys):
    """Première clé présente (les intitulés du fichier ont varié)."""
    for key in keys:
        if key in item and item[key] is not None:
            return item[key]
    return None


def raw_with_unit(value, unit: str) -> str | None:
    """Valeur brute du registre (« 525V ») — texte conservé tel quel.

    - nombre (525.0) : mis au format du registre avec l'unité de la
      colonne (« 525V », « 16,5A ») — l'unité vient du fichier ;
    - nombre SEUL en texte (« "525" », « "16,5" ») : idem ;
    - tout autre texte (« 525V », « 380V / 800 », « 500 Y »,
      « - ») : conservé verbatim/nettoyé.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        text = f"{float(value):.4f}".rstrip("0").rstrip(".")
        return text.replace(".", ",") + unit
    text = clean(value)
    if text is not None and re.fullmatch(r"\d+(?:[.,]\d+)?", text):
        return text + unit
    return text


def looks_like_isolement(value: str | None) -> bool:
    """Vrai si la valeur ressemble à une mesure d'isolement."""
    return bool(value and _ISOLEMENT_RE.search(value))


def est_tension(value: str | None) -> bool:
    """Vrai si la valeur est une tension de réseau (« BT », « MT », « H.T »,
    « BT - », « BT / HT »… — signes de ponctuation parasites ignorés)."""
    if not value:
        return False
    return re.sub(r"[ .\-/]", "", value).upper() in {
        "BT", "MT", "HT", "BTMT", "MTBT", "BTHT", "HTBT",
    }


def deplace_btmt_vers_societe(societe: str | None, bt_mt: str | None):
    """Transposition Société VIDE ← BT/MT (décision client 26/09/2026).

    Quand la colonne BT/MT (Tension) porte une notation qui N'EST PAS
    une tension (MT/BT/HT) — c'est donc normalement une notation de
    SOCIÉTÉ —, elle est transposée (déplacée) dans la colonne Société
    SEULEMENT SI celle-ci est vide. Sinon, rien n'est changé.
    Renvoie (societe, bt_mt, transposition_effectuee).
    """
    if (bt_mt and not est_tension(bt_mt) and societe is None):
        return bt_mt, None, True
    return societe, bt_mt, False


def deplace_societe_vers_btmt(societe: str | None, bt_mt: str | None):
    """Transposition Tension VIDE ← Société (décision client 26/09/2026).

    Quand la colonne Société porte une notation de TENSION
    (« BT », « MT », « H.T »…), elle est déplacée vers la colonne
    BT/MT (Tension) SEULEMENT SI celle-ci est vide.
    Renvoie (societe, bt_mt, transposition_effectuee).
    """
    if (societe and est_tension(societe) and bt_mt is None):
        return None, societe, True
    return societe, bt_mt, False


# Valeur de MESURE seule (nombre + unité Ω/kΩ/MΩ/GΩ facultative) —
# pour reconnaître une vraie paire de valeurs dans la cellule R.
_MESURE_RE = re.compile(
    r"\A\d+([.,]\d+)?(\s*(?:k|M|G)?\s*Ω)?\Z", re.IGNORECASE)
_UNITE_FIN_RE = re.compile(r"(k|M|G)?\s*Ω\Z", re.IGNORECASE)


def separe_r_deux_valeurs(resistance: str | None, isolement_m: str | None):
    """Séparation d'une cellule R à DEUX valeurs « A / B » (26/09/2026).

    Quand la cellule R porte deux valeurs séparées par « / » et que la
    colonne Isolement ph-m est VIDE, la valeur de GAUCHE est décalée
    vers Isolement ph-m (elle y restait bloquée) et R garde la valeur
    de droite. Quand l'unité est portée une seule fois en fin de
    cellule (« 1,28 / 2,2 Ω »), elle est recopiée sur la valeur
    déplacée (« 1,28 Ω ») — elle vient de la cellule elle-même.
    Cas non traités : Isolement ph-m déjà rempli, ou parties qui ne
    sont pas des mesures (libellés « R1=C1=2 / R2=C2=2 »).
    Renvoie (r, isolement_m, separation_effectuee).
    """
    if resistance is None or isolement_m is not None or "/" not in resistance:
        return resistance, isolement_m, False
    parties = [part.strip() for part in resistance.split("/")]
    if len(parties) != 2:
        return resistance, isolement_m, False
    gauche, droite = parties
    if not (_MESURE_RE.match(gauche) and _MESURE_RE.match(droite)):
        return resistance, isolement_m, False
    if not _UNITE_FIN_RE.search(gauche):
        unite = _UNITE_FIN_RE.search(droite)
        if unite:
            gauche = f"{gauche} {unite.group(0).strip()}"
    return droite, gauche, True


# Une « partie » est une VALEUR : exactement UN nombre, sans « = »,
# taille raisonnable — les libellés (« Stator », « Rot », « Pompe »…)
# collés à la valeur sont tolérés (transcription verbatim).
_NOMBRE_RE = re.compile(r"\d+(?:[.,]\d+)?")
# Unité en FIN de valeur (partagée en fin de cellule) :
# « GΩ », « M Ω », « G.m », « 6G », « 900M »…
_UNITE_TAIL_RE = re.compile(r"(G\.m|[kMG]?\s*Ω|[kMG])\s*$")


def _est_valeur_isolement(texte: str | None) -> bool:
    """Vrai si cette partie d'isolement porte exactement UNE valeur."""
    if texte is None:
        return False
    texte = texte.strip()
    if not texte or "=" in texte or len(texte) > 30:
        return False
    return len(_NOMBRE_RE.findall(texte)) == 1


def separe_isolement_deux_valeurs(isolement: str | None, isolement_m: str | None):
    """Séparation d'une cellule Isolement à DEUX valeurs (26/09/2026).

    Quand la cellule Isolement (ph-ph) porte deux valeurs séparées par
    « / » et que la colonne Isolement ph-m est VIDE, la valeur de
    DROITE est décalée vers Isolement ph-m ; Isolement garde la valeur
    de gauche. Quand l'unité est portée une seule fois en fin de
    cellule (« 2,75 / 2,9 GΩ »), elle est recopiée sur la valeur de
    gauche (« 2,75 GΩ ») — elle vient de la cellule elle-même.
    Cas non traités : Isolement ph-m déjà rempli ; parties qui ne sont
    pas des valeurs (« MT/BT = 2,4 GΩ » : une seule mesure avec
    préfixe ; étiquettes sans nombre ; 3 valeurs et plus).
    Renvoie (isolement, isolement_m, separation_effectuee).
    """
    if isolement is None or isolement_m is not None or "/" not in isolement:
        return isolement, isolement_m, False
    parties = [part.strip() for part in isolement.split("/")]
    if len(parties) != 2:
        return isolement, isolement_m, False
    gauche, droite = parties
    if not (_est_valeur_isolement(gauche) and _est_valeur_isolement(droite)):
        return isolement, isolement_m, False
    if not _UNITE_TAIL_RE.search(gauche):
        unite = _UNITE_TAIL_RE.search(droite)
        if unite:
            gauche = f"{gauche} {unite.group(1).strip()}"
    return gauche, droite, True


def deplace_notation_nature(isolement: str | None, nature: str | None):
    """Notation de NATURE restée en Isolement → Nature vide (26/09/2026).

    Une cellule Isolement SANS AUCUN CHIFFRE n'est pas une mesure :
    c'est une notation de désignation (« M.E », « ME », « Transfo »,
    « Pompe Dragueuse Toyo »… — les mesures abrégées ont toujours un
    chiffre : « 740 M », « 900M », « 3G »). Elle est décalée vers la
    colonne Nature SEULEMENT SI celle-ci est vide.
    Renvoie (isolement, nature, deplacement_effectue).
    """
    if (isolement and nature is None and not re.search(r"\d", isolement)):
        return None, isolement, True
    return isolement, nature, False


# Isolement NÉGATIF : signe « - » au début de la valeur (devant un
# chiffre) — pas un tiret au milieu d'un libellé.
_NEGATIF_RE = re.compile(r"^\s*-\s*(?=\d)")


def absolu_isolement(value: str | None) -> str | None:
    """Isolement NÉGATIF → POSITIF (décision client 26/09/2026).

    Retire le signe « - » de tête (« -2 GΩ » → « 2 GΩ »). Un tiret à
    l'intérieur d'un libellé (« R1-52 ») n'est pas concerné, et la
    règle ne s'applique qu'aux colonnes d'isolement.
    """
    if value and _NEGATIF_RE.search(value):
        return _NEGATIF_RE.sub("", value)
    return value


def couplage_fiche(couplage: str | None) -> str | None:
    """Notation de couplage du registre → valeur de la fiche moteur.

    Le registre note « Y » (étoile) et « D » / « Δ » (triangle) —
    notations du fichier lui-même. Le formulaire attend
    « Étoile (Y) » ou « Triangle (Δ) ». Les valeurs non standard
    (« C », « S », composites « Y / D ») ne sont PAS converties.
    """
    if not couplage:
        return None
    symbole = couplage.strip().upper()
    if symbole == "Y":
        return "Étoile (Y)"
    if symbole in ("D", "Δ"):
        return "Triangle (Δ)"
    return None


def echange_societe_btmt(societe: str | None, bt_mt: str | None):
    """Décalage ÉVIDENT Société ↔ BT/MT (décision client 26/09/2026).

    Échange les deux valeurs SEULEMENT quand les deux indices
    convergent : la colonne Société contient une TENSION
    (« BT », « MT »…) ET la colonne BT/MT contient un nom (non vide,
    non tension). Les cas ambigus (une seule cellule renseignée)
    restent TELS QUELS.
    Renvoie (societe, bt_mt, echange_effectue).
    """
    if (est_tension(societe) and bt_mt and not est_tension(bt_mt)):
        return bt_mt, societe, True
    return societe, bt_mt, False


def extract_format4(item: dict) -> tuple[dict, list[str]]:
    """Format 4 (lot 4) → valeurs du registre + journaux de réalignement.

    Conventions identiques aux autres formats (cellules vides = NULL,
    unités ajoutées aux nombres seuls). Les DÉCALAGES de fin de lot
    (annoncés au client) sont corrigés ici et journalisés ; rien
    n'est inventé : chaque valeur déplacée garde sa colonne réelle.
    """
    logs: list[str] = []

    mle = clean(item.get("mle_ns"))
    di_ot = clean(item.get("di_ot"))
    # Matricule et DI/OT inversés (n° de DI dans la colonne Matricule :
    # 8 chiffres = n° DI, ≤ 6 chiffres = n° de matricule).
    if (mle and di_ot and mle.isdigit() and di_ot.isdigit()
            and len(mle) >= 8 and len(di_ot) <= 6):
        mle, di_ot = di_ot, mle
        logs.append("Matricule ↔ DI/OT échangés")

    nature = clean(item.get("nature"))
    isolement = clean(item.get("isolement_ph_ph"))
    isolement_m = clean(item.get("isolement_ph_m"))
    resistance = clean(item.get("r"))
    puissance = clean(item.get("puissance"))
    tension = clean(item.get("tension"))
    societe = clean(item.get("societe"))
    observation = clean(item.get("observation"))

    # Bloc décalé d'UN cran dès « Nature » : la cellule Nature porte la
    # paire d'essai « …V / …A » (doublon de U0/I0, sans colonne dans le
    # registre) et chaque valeur suivante est dans la colonne de gauche.
    if _VA_RE.match(nature or "") or (
            nature is None and isolement == "M.É"
            and (puissance or "").endswith("Ω")
            and looks_like_isolement(resistance)):
        surplus = nature
        (nature, isolement, isolement_m, resistance,
         puissance, tension, societe) = (
            isolement, isolement_m, resistance, puissance,
            tension, societe, observation)
        observation = None
        logs.append(
            "décalage réaligné"
            + (f" (cellule « {surplus} » = doublon U0/I0, sans colonne)"
               if surplus else ""))

    # Décalage dès « Puissance » : une 2ᵉ résistance s'intercale entre
    # R et Puissance (regroupée dans R avec le séparateur « / » du
    # fichier lui-même).
    elif ((puissance or "").endswith("Ω")
            and _PUISSANCE_RE.search(tension or "")):
        deuxieme = puissance
        resistance = f"{resistance} / {deuxieme}" if resistance else deuxieme
        puissance, tension, societe = tension, societe, observation
        observation = None
        logs.append(f"décalage réaligné (2ᵉ résistance « {deuxieme} » regroupée dans R)")

    # R logée dans la cellule d'isolement (« Poste S »).
    elif (nature == "Poste S" and (isolement or "").endswith("Ω")
            and resistance is None):
        resistance = isolement
        isolement = None
        logs.append(f"résistance « {resistance} » déplacée de Isolement ph-ph vers R")

    # Cellule R à deux valeurs « A / B » : la valeur de gauche est
    # décalée vers Isolement ph-m SI cette cellule est vide (les
    # réalignements ci-dessus peuvent avoir regroupé les 2 valeurs
    # dans R — la séparation s'applique donc en dernier).
    resistance, isolement_m, separe = separe_r_deux_valeurs(resistance, isolement_m)
    if separe:
        logs.append(f"R « {resistance} / {isolement_m} » : valeur de gauche "
                    f"« {isolement_m} » décalée vers Isolement ph-m (vide)")

    # Cellule Isolement à deux valeurs « A / B » : la valeur de droite
    # est décalée vers Isolement ph-m SI cette cellule est vide (une
    # valeur déjà reçue de R bloque la règle — aucun écrasement).
    isolement, isolement_m, separe_iso = separe_isolement_deux_valeurs(
        isolement, isolement_m)
    if separe_iso:
        logs.append(f"Isolement « {isolement} / {isolement_m} » : valeur de droite "
                    f"« {isolement_m} » décalée vers Isolement ph-m (vide)")

    # Notation de NATURE restée en Isolement → Nature (vide).
    isolement, nature, deplace_n = deplace_notation_nature(isolement, nature)
    if deplace_n:
        logs.append(f"« {nature} » décalé d'Isolement vers Nature (cellule vide)")

    # Isolement NÉGATIF → positif (décision client).
    isolement_sans_signe = absolu_isolement(isolement)
    if isolement_sans_signe != isolement:
        logs.append(f"Isolement « {isolement} » → « {isolement_sans_signe} » "
                    "(signe « - » retiré)")
        isolement = isolement_sans_signe
    isolement_m_sans_signe = absolu_isolement(isolement_m)
    if isolement_m_sans_signe != isolement_m:
        logs.append(f"Isolement ph-m « {isolement_m} » → « {isolement_m_sans_signe} » "
                    "(signe « - » retiré)")
        isolement_m = isolement_m_sans_signe

    values = {
        "entry_date": parse_date(clean(item.get("date")) or ""),
        "matricule": mle,
        "di_ot": di_ot,
        "couplage": clean(item.get("couplage")),
        "service": clean(item.get("service")),
        "un_v": raw_with_unit(item.get("un_v"), "V"),
        "in_a": raw_with_unit(item.get("in_a"), "A"),
        "uo_v": raw_with_unit(item.get("u0_v"), "V"),
        "io_a": raw_with_unit(item.get("i0_a"), "A"),
        "isolement": isolement,
        "isolement_ph_m": isolement_m,
        "r": resistance,
        "nature": nature,
        "puissance": puissance,
        "societe": societe,
        "bt_mt": tension,
        "observation": observation,
    }
    return values, logs


def single_voltage(text: str | None) -> float | None:
    """« 525V » → 525.0 ; « 5,5 kV » → 5500.0 ; composé/absent → None."""
    if not text:
        return None
    match = _SINGLE["V"].match(text)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    return value * 1000.0 if "kv" in text.lower() else value


def single_current(text: str | None) -> float | None:
    """« 260A » → 260.0 ; « 33.5A » → 33.5 ; composé/parenthèses → None."""
    if not text:
        return None
    match = _SINGLE["A"].match(text)
    return float(match.group(1).replace(",", ".")) if match else None


def single_power_kw(text: str | None) -> float | None:
    """« 45 kW » → 45.0 ; « 170 W » → 0.17 ; HP/kVA/composé → None."""
    if not text:
        return None
    match = _SINGLE["W"].match(text)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    return value / 1000.0 if text.lower().rstrip().endswith("w") and not text.lower().replace(" ", "").endswith("kw") else value


def import_file(path: Path, dry_run: bool = False, lot: str = "JSON") -> int:
    """Importe un JSON simple (une liste) ; renvoie 0 si OK, 1 sinon.

    `lot` distingue les fichiers successifs dans source_ref (« JSON »,
    « JSON-C1 »…) : chaque import est idempotent pour SON fichier, et
    un contrôle par CONTENU (date + matricule + DI/OT) empêche les
    doublons entre fichiers qui se recouvrent.
    """
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)
    return import_rows(rows, lot=lot, label=str(path), dry_run=dry_run)


def import_rows(rows: list, lot: str, label: str, dry_run: bool = False) -> int:
    """Importe des lignes DÉJÀ chargées (fichier simple ou fusionné).

    `label` sert uniquement à l'affichage.
    """
    # Format 4 (lot 4) : clés séparées « isolement_ph_ph »/« mle_ns »…
    is_format4 = bool(rows) and isinstance(rows[0], dict) and "mle_ns" in rows[0]
    print(f"Source : {label} — {len(rows)} ligne(s) (lot « {lot} »"
          + (", format 4" if is_format4 else "") + ")")

    db = SessionLocal()
    imported = skipped = swaps = no_matricule = realigns = exclues = echanges = transpositions = separations = separations_iso = deplaces_nature = negatifs = corrections = 0
    try:
        for index, item in enumerate(rows, start=1):
            source_ref = f"{lot}:{index}"
            if source_ref in LIGNES_EXCLUES:
                exclues += 1
                print(f"  [exclue] ligne {index} : décision client — "
                      f"{LIGNES_EXCLUES[source_ref]}")
                continue
            if db.scalar(select(RegistreEntry.id)
                         .where(RegistreEntry.source_ref == source_ref)) is not None:
                skipped += 1
                continue

            if is_format4:
                values, logs = extract_format4(item)
                if any(message.startswith("R «") and "décalée vers Isolement ph-m" in message
                       for message in logs):
                    separations += 1
                if any(message.startswith("Isolement «") and "décalée vers Isolement ph-m" in message
                       for message in logs):
                    separations_iso += 1
                if any(message.startswith("«") and message.endswith("(cellule vide)")
                       and "décalé d'Isolement vers Nature" in message
                       for message in logs):
                    deplaces_nature += 1
                if any("signe « - » retiré" in message for message in logs):
                    negatifs += 1
                if logs:
                    realigns += 1
                    for message in logs:
                        print(f"  [déc. corr.] ligne {index} ({values['entry_date']} / "
                              f"{values['matricule'] or '—'}) : {message}")
                matricule = values["matricule"]
            else:
                isolement = clean(get_first(item, "Isolement", "isolement"))
                nature = clean(get_first(item, "Nature", "nature"))

                # Décalage certain du fichier : Isolement et Nature inversés.
                if (nature and looks_like_isolement(nature)
                        and not looks_like_isolement(isolement)):
                    isolement, nature = nature, isolement
                    swaps += 1
                    print(f"  [déc. corr.] ligne {index} ({clean(get_first(item, 'Date', 'date'))} / "
                          f"{clean(get_first(item, 'Mat', 'Mat / N°', 'matricule')) or '—'}) : "
                          "Isolement ↔ Nature échangés")

                # Isolement à deux valeurs : la valeur de droite est
                # décalée vers Isolement ph-m (toujours vide ici).
                isolement, isolement_m_separe, separe_iso = (
                    separe_isolement_deux_valeurs(isolement, None))
                if separe_iso:
                    separations_iso += 1
                    print(f"  [déc. corr.] ligne {index} : Isolement « {isolement} / "
                          f"{isolement_m_separe} » : valeur de droite décalée vers "
                          "Isolement ph-m (vide)")

                # Notation de NATURE restée en Isolement → Nature (vide).
                isolement, nature, deplace = deplace_notation_nature(isolement, nature)
                if deplace:
                    deplaces_nature += 1
                    print(f"  [déc. corr.] ligne {index} : « {nature} » décalé "
                          "d'Isolement vers Nature (cellule vide)")

                # Isolement NÉGATIF → positif (décision client).
                isolement_sans_signe = absolu_isolement(isolement)
                if isolement_sans_signe != isolement:
                    negatifs += 1
                    print(f"  [déc. corr.] ligne {index} : Isolement « {isolement} » "
                          f"→ « {isolement_sans_signe} » (signe « - » retiré)")
                isolement = isolement_sans_signe

                matricule = clean(get_first(item, "Mat", "Mat / N°", "matricule"))

                # Décalage ÉVIDENT : Société ↔ BT/MT (décision client).
                brut_societe = clean(get_first(item, "Société", "societe"))
                brut_bt_mt = clean(get_first(item, "BT/MT (Tension)", "tension_bt_mt"))
                brut_societe, brut_bt_mt, echange = echange_societe_btmt(brut_societe, brut_bt_mt)
                if echange:
                    echanges += 1
                    print(f"  [déc. corr.] ligne {index} : Société ↔ BT/MT échangées")

                # Transposition : notation de société restée en BT/MT,
                # vers la colonne Société SEULEMENT SI elle est vide.
                brut_societe, brut_bt_mt, transpose = deplace_btmt_vers_societe(
                    brut_societe, brut_bt_mt)
                if transpose:
                    transpositions += 1
                    print(f"  [déc. corr.] ligne {index} : « {brut_societe} » "
                          "transposé de BT/MT vers Société (cellule vide)")

                # Transposition inverse : notation de TENSION restée en
                # Société, vers la colonne BT/MT SEULEMENT SI elle est vide.
                brut_societe, brut_bt_mt, transpose2 = deplace_societe_vers_btmt(
                    brut_societe, brut_bt_mt)
                if transpose2:
                    transpositions += 1
                    print(f"  [déc. corr.] ligne {index} : « {brut_bt_mt} » "
                          "transposé de Société vers BT/MT (cellule vide)")

                values = {
                    "entry_date": parse_date(clean(get_first(item, "Date", "date")) or ""),
                    "matricule": matricule,
                    "di_ot": clean(get_first(item, "DIT/OT", "dit_ot")),
                    "couplage": None,
                    "service": clean(get_first(item, "Service (Sce)", "service")),
                    "un_v": raw_with_unit(get_first(item, "Un", "Un (V)", "un_v"), "V"),
                    "in_a": raw_with_unit(get_first(item, "In", "In (A)", "in_a"), "A"),
                    "uo_v": raw_with_unit(get_first(item, "U0", "U0 (V)", "u0_v"), "V"),
                    "io_a": raw_with_unit(get_first(item, "I0", "I0 (A)", "i0_a"), "A"),
                    "isolement": isolement,
                    "isolement_ph_m": isolement_m_separe,
                    "r": None,
                    "nature": nature,
                    "puissance": clean(get_first(item, "Puissance (P)", "puissance")),
                    "societe": brut_societe,
                    "bt_mt": brut_bt_mt,
                    "observation": clean(get_first(item, "Observation", "observation")),
                }

            # Corrections ponctuelles de cellules (décisions client).
            if source_ref in CORRECTIONS_CELLULES:
                for champ, nouvelle in CORRECTIONS_CELLULES[source_ref].items():
                    if values.get(champ) != nouvelle:
                        print(f"  [déc. corr.] ligne {index} : {champ} "
                              f"« {values.get(champ)} » → « {nouvelle} »")
                        values[champ] = nouvelle
                        corrections += 1

            if not matricule:
                no_matricule += 1

            # Dédoublonnage par contenu entre fichiers qui se recouvrent
            # (au moins une des 3 valeurs d'identité renseignée).
            identity = (values["entry_date"], values["matricule"], values["di_ot"])
            if any(identity) and db.scalar(
                select(RegistreEntry.id).where(
                    RegistreEntry.entry_date == values["entry_date"],
                    RegistreEntry.matricule == values["matricule"],
                    RegistreEntry.di_ot == values["di_ot"],
                )
            ) is not None:
                skipped += 1
                print(f"  [déjà présent] ligne {index} ({identity[0]} / "
                      f"{identity[1] or '—'} / {identity[2] or '—'}) : ignorée")
                continue

            if dry_run:
                imported += 1
                continue

            # --- Fiche moteur (créée ou complétée quand exploitable) ---
            if matricule:
                motor = db.scalar(select(Motor).where(Motor.motor_id == matricule))
                if motor is None:
                    motor = Motor(motor_id=matricule)
                    db.add(motor)
                    db.flush()  # visible pour les lignes suivantes du même moteur
                motor.matricule = matricule
                if values["nature"]:
                    motor.designation = values["nature"]
                couplage = couplage_fiche(values["couplage"])
                if couplage:
                    motor.coupling = couplage
                if values["service"]:
                    motor.service = values["service"]
                if values["di_ot"]:
                    motor.di_ot = values["di_ot"]
                tension = single_voltage(values["un_v"])
                if tension is not None:
                    motor.rated_voltage_v = tension
                courant = single_current(values["in_a"])
                if courant is not None:
                    motor.rated_current_a = courant
                puissance = single_power_kw(values["puissance"])
                if puissance is not None:
                    motor.rated_power_kw = puissance

            db.add(RegistreEntry(
                source="historique", source_ref=source_ref, **values
            ))
            imported += 1

        if not dry_run:
            db.commit()

        print(f"Lignes importées : {imported}"
              + (f" (ignorées, déjà présentes : {skipped})" if skipped else ""))
        if exclues:
            print(f"Lignes exclues (décision client) : {exclues}")
        print(f"Décalages Isolement ↔ Nature corrigés : {swaps}")
        if echanges:
            print(f"Décalages Société ↔ BT/MT corrigés (évidents) : {echanges}")
        if transpositions:
            print(f"Notations de société transposées BT/MT → Société (vide) : {transpositions}")
        if separations:
            print(f"R à deux valeurs : valeurs de gauche décalées vers Isolement ph-m (vide) : {separations}")
        if separations_iso:
            print(f"Isolement à deux valeurs : valeurs de droite décalées vers Isolement ph-m (vide) : {separations_iso}")
        if deplaces_nature:
            print(f"Notations de nature décalées d'Isolement vers Nature (vide) : {deplaces_nature}")
        if negatifs:
            print(f"Isolements négatifs rendus positifs (signe « - » retiré) : {negatifs}")
        if corrections:
            print(f"Corrections ponctuelles de cellules (décisions client) : {corrections}")
        if realigns:
            print(f"Réalignements (format 4) : {realigns}")
        print(f"Lignes sans matricule (ligne de registre créée sans fiche moteur) : {no_matricule}")
        if dry_run:
            print("DRY-RUN : rien n'a été écrit.")
        return 0
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import du registre réel (JSON).")
    parser.add_argument("fichier", type=Path, help="fichier JSON du registre réel")
    parser.add_argument("--dry-run", action="store_true",
                        help="valide et compte sans rien écrire")
    parser.add_argument("--lot", default="JSON",
                        help="nom du lot pour source_ref (défaut : JSON ; "
                             "ignoré pour le fichier fusionné)")
    args = parser.parse_args()

    # FICHIER FUSIONNÉ : un objet dont les clés sont les lots, dans
    # l'ordre du projet (« JSON », « JSON-C1 », « JSON-C2 », « JSON-C3 »).
    # Une seule commande importe tout ; les source_ref sont IDENTIQUES
    # à ceux des 4 fichiers séparés (aucune référence ne change).
    with open(args.fichier, encoding="utf-8") as fh:
        data = json.load(fh)
    LOTS = ("JSON", "JSON-C1", "JSON-C2", "JSON-C3")
    if isinstance(data, dict) and data and all(k in LOTS for k in data):
        print(f"Fichier fusionné : {len(data)} lot(s) → import dans l'ordre du projet.")
        code = 0
        for lot in [l for l in LOTS if l in data]:
            if import_rows(data[lot], lot=lot,
                           label=f"{args.fichier.name} [{lot}]",
                           dry_run=args.dry_run) != 0:
                code = 1
        sys.exit(code)
    sys.exit(import_file(args.fichier, dry_run=args.dry_run, lot=args.lot))


if __name__ == "__main__":
    main()
