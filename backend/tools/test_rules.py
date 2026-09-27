"""TESTS SIMPLES DES RÈGLES — cas numériques de base (sans base de données).

Vérifie les calculs des trois règles fournies avec quelques valeurs
évidentes. Usage (depuis backend/) :

    python tools/test_rules.py

Chaque test affiche « OK » ; le script se termine par un récapitulatif
et un code d'erreur non nul si un cas échoue.
"""

import sys
from pathlib import Path

# Permet de lancer « python tools/test_rules.py » depuis backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from diagnostic_rules import (  # noqa: E402
    continuity_rules,
    current_rules,
    insulation_rules,
    temperature_rules,
)

failures = 0


def check(name, condition, detail=""):
    global failures
    if condition:
        print(f"  OK   {name}")
    else:
        failures += 1
        print(f"  ÉCHEC {name} {detail}")


print("=== Règle COURANT À VIDE (In/3 ≤ I0 ≤ 2·In/3) ===")
# In = 30 A → bornes 10 / 20 A
r = current_rules.evaluate({"rated_current_a": 30.0, "measured_current_a": 15.0})
check("I0 = 15 A, In = 30 A → CONFORME (10 ≤ 15 ≤ 20)",
      r["evaluation"] == "conforme", r)
r = current_rules.evaluate({"rated_current_a": 30.0, "measured_current_a": 8.0})
check("I0 = 8 A (< 10) → PROBLÉMATIQUE", r["evaluation"] == "problematique", r)
r = current_rules.evaluate({"rated_current_a": 30.0, "measured_current_a": 25.0})
check("I0 = 25 A (> 20) → PROBLÉMATIQUE", r["evaluation"] == "problematique", r)
r = current_rules.evaluate({"rated_current_a": None, "measured_current_a": 15.0})
check("In manquante → NON ÉVALUABLE (rien d'inventé)", r["evaluation"] == "non_evaluable")
r = current_rules.evaluate({"rated_current_a": 30.0, "measured_current_a": 10.0})
check("I0 = 10 A exactement à la borne → CONFORME", r["evaluation"] == "conforme", r)

print("=== Règle ISOLEMENT (Rmin = 1 kΩ × Vtest) ===")
# 1000 V → Rmin = 1 MΩ
r = insulation_rules.evaluate({
    "insulation_test_voltage_v": 1000,
    "insulation_mohm": {"ph1_ph2": 2.5, "ph2_ph3": 0.7, "ph3_ph1": 1.8,
                        "ph1_ground": 3.1, "ph2_ground": 2.0, "ph3_ground": 1.2},
})
check("1000 V → Rmin = 1 MΩ", r["display"]["rmin_mohm"] == 1.0, r["display"])
items = {i["key"]: i for i in r["items"]}
check("Ph1-Ph2 = 2,5 MΩ → CONFORME", items["ph1_ph2"]["evaluation"] == "conforme")
check("Ph2-Ph3 = 0,7 MΩ → PROBLÉMATIQUE", items["ph2_ph3"]["evaluation"] == "problematique")
check("Bilan global → PROBLÉMATIQUE", r["evaluation"] == "problematique")
# 500 V → Rmin = 0,5 MΩ ; mesure exactement à la limite
r = insulation_rules.evaluate({
    "insulation_test_voltage_v": 500,
    "insulation_mohm": {"ph1_ph2": 0.5, "ph2_ph3": 0.6, "ph3_ph1": 0.6,
                        "ph1_ground": 0.6, "ph2_ground": 0.6, "ph3_ground": 0.6},
})
check("500 V → Rmin affichée « 500 kΩ »", r["display"]["rmin_text"] == "500 kΩ", r["display"])
check("0,5 MΩ exactement à la limite → CONFORME (≥ Rmin)",
      r["evaluation"] == "conforme", r)
# 2500 V et 5000 V
r = insulation_rules.evaluate({
    "insulation_test_voltage_v": 2500,
    "insulation_mohm": {"ph1_ph2": 2.5, "ph2_ph3": 2.6, "ph3_ph1": 2.6,
                        "ph1_ground": 2.6, "ph2_ground": 2.6, "ph3_ground": 2.6},
})
check("2500 V → Rmin = 2,5 MΩ ; mesure à la limite → CONFORME",
      r["display"]["rmin_mohm"] == 2.5 and r["evaluation"] == "conforme", r)
r = insulation_rules.evaluate({
    "insulation_test_voltage_v": 5000,
    "insulation_mohm": {"ph1_ph2": 95.0, "ph2_ph3": 91.0, "ph3_ph1": 89.0,
                        "ph1_ground": 1.1, "ph2_ground": 0.9, "ph3_ground": 1.0},
})
check("5000 V → Rmin = 5 MΩ ; mesures < 5 MΩ → PROBLÉMATIQUE",
      r["display"]["rmin_mohm"] == 5.0 and r["evaluation"] == "problematique", r)
# Informations manquantes
r = insulation_rules.evaluate({"insulation_test_voltage_v": None,
                               "insulation_mohm": {"ph1_ph2": 2.5}})
check("Mesures sans tension de test → NON ÉVALUABLE", r["evaluation"] == "non_evaluable")
r = insulation_rules.evaluate({"insulation_test_voltage_v": 1000,
                               "insulation_mohm": {}})
check("Tension sans mesures → NON ÉVALUABLE", r["evaluation"] == "non_evaluable")

print("=== Règle RÉSISTANCE DES ENROULEMENTS (même valeur attendue) ===")
from diagnostic_rules import winding_resistance_rules  # noqa: E402
r = winding_resistance_rules.evaluate({"winding_resistance_ohm": {"r12": 0.42, "r23": 0.42, "r31": 0.42}})
check("R12 = R23 = R31 = 0,42 Ω → CONFORME", r["evaluation"] == "conforme", r)
r = winding_resistance_rules.evaluate({"winding_resistance_ohm": {"r12": 0.42, "r23": 0.43, "r31": 0.42}})
check("R23 différente (0,43) → PROBLÉMATIQUE", r["evaluation"] == "problematique", r)
r = winding_resistance_rules.evaluate({"winding_resistance_ohm": {"r12": 0.42, "r23": 0.43, "r31": None}})
check("R31 manquante → NON ÉVALUABLE (R31 listée)",
      r["evaluation"] == "non_evaluable" and any("R31" in m for m in r["missing_info"]))
r = winding_resistance_rules.evaluate({"winding_resistance_ohm": {"r12": None, "r23": None, "r31": None}})
check("aucune mesure → NON ÉVALUABLE", r["evaluation"] == "non_evaluable")

print("=== Règle TEMPÉRATURE PALIERS (limite critique 70 °C, É16) ===")
r = temperature_rules.evaluate({"temp_bearing_de_c": 48.5, "temp_bearing_nde_c": 51.2})
check("paliers 48,5 / 51,2 °C → NON CRITIQUE", r["evaluation"] == "non_critique", r)
r = temperature_rules.evaluate({"temp_bearing_de_c": 69.9, "temp_bearing_nde_c": 40.0})
check("palier DE 69,9 °C → NON CRITIQUE (strictement sous 70)", r["evaluation"] == "non_critique", r)
r = temperature_rules.evaluate({"temp_bearing_de_c": 84.0, "temp_bearing_nde_c": 71.5})
check("paliers 84,0 / 71,5 °C → CRITIQUE (2 paliers ≥ 70)", r["evaluation"] == "critique", r)
r = temperature_rules.evaluate({"temp_bearing_de_c": 70.0, "temp_bearing_nde_c": 50.0})
check("palier DE 70,0 exactement → CRITIQUE (≥)", r["evaluation"] == "critique", r)
labels = {i["key"]: i["evaluation_label"] for i in r["items"]}
check("détail par palier présent (items DE/NDE)", set(labels) == {"de", "nde"}, r)
r = temperature_rules.evaluate({"temp_bearing_de_c": 50.0, "temp_bearing_nde_c": None})
check("un seul palier → NON ÉVALUABLE (palier manquant listé)",
      r["evaluation"] == "non_evaluable" and any("C.O.A" in m for m in r["missing_info"]))
r = temperature_rules.evaluate({"temp_bearing_de_c": None, "temp_bearing_nde_c": None,
                                "legacy_temperature_c": 82.0})
check("ancienne fiche 82 °C unique → NON CRITIQUE (ancien seuil 85)",
      r["evaluation"] == "non_critique", r)
r = temperature_rules.evaluate({"legacy_temperature_c": 88.0})
check("ancienne fiche 88 °C unique → CRITIQUE (ancien seuil 85)",
      r["evaluation"] == "critique", r)
r = temperature_rules.evaluate({})
check("aucune température → NON ÉVALUABLE (2 paliers listés)",
      r["evaluation"] == "non_evaluable" and len(r["missing_info"]) == 2)

print("=== Règle CONTINUITÉ des enroulements (É16 — Oui/Non global) ===")
r = continuity_rules.evaluate({"continuity_ok": True})
check("continuité Oui → CONFORME", r["evaluation"] == "conforme", r)
r = continuity_rules.evaluate({"continuity_ok": False})
check("continuité Non → PROBLÉMATIQUE", r["evaluation"] == "problematique", r)
r = continuity_rules.evaluate({"continuity_ok": None})
check("continuité non renseignée → NON ÉVALUABLE (listée)",
      r["evaluation"] == "non_evaluable" and any("ontinuité" in m for m in r["missing_info"]))

print("=== Règle VIBRATION (seuils 4,5 / 7,1 mm/s selon la puissance) ===")
from diagnostic_rules import vibration_rules  # noqa: E402
# Petit moteur (P ≤ 300 kW) → seuil 4,5 mm/s
r = vibration_rules.evaluate({"vibration": {"mm_s": 2.8, "mm_s_last": None},
                              "rated_power_kw": 45.0})
check("2,8 mm/s, P = 45 kW → NON CRITIQUE (seuil 4,5)",
      r["evaluation"] == "non_critique" and r["reference_value"] == 4.5, r)
r = vibration_rules.evaluate({"vibration": {"mm_s": 4.5, "mm_s_last": None},
                              "rated_power_kw": 45.0})
check("4,5 mm/s exactement, P = 45 kW → CRITIQUE (≥ seuil, choix client)",
      r["evaluation"] == "critique", r)
r = vibration_rules.evaluate({"vibration": {"mm_s": 5.0, "mm_s_last": None},
                              "rated_power_kw": 300.0})
check("5,0 mm/s, P = 300 kW exactement → CRITIQUE (300 inclus au seuil 4,5)",
      r["evaluation"] == "critique" and r["reference_value"] == 4.5, r)
# Gros moteur (P > 300 kW) → seuil 7,1 mm/s
r = vibration_rules.evaluate({"vibration": {"mm_s": 6.9, "mm_s_last": None},
                              "rated_power_kw": 315.0})
check("6,9 mm/s, P = 315 kW → NON CRITIQUE (seuil 7,1)",
      r["evaluation"] == "non_critique" and r["reference_value"] == 7.1, r)
r = vibration_rules.evaluate({"vibration": {"mm_s": 7.1, "mm_s_last": None},
                              "rated_power_kw": 500.0})
check("7,1 mm/s exactement, P = 500 kW → CRITIQUE (≥ seuil)",
      r["evaluation"] == "critique", r)
# Source du kit (mm_s_last) utilisée si la fiche est vide
r = vibration_rules.evaluate({"vibration": {"mm_s": None, "mm_s_last": 8.2},
                              "rated_power_kw": 400.0})
check("8,2 mm/s (kit), P = 400 kW → CRITIQUE (seuil 7,1)",
      r["evaluation"] == "critique", r)
# Informations manquantes
r = vibration_rules.evaluate({"vibration": {"mm_s": 3.0, "mm_s_last": None},
                              "rated_power_kw": None})
check("mesure sans puissance plaque → NON ÉVALUABLE (puissance listée)",
      r["evaluation"] == "non_evaluable" and any("puissance" in m for m in r["missing_info"]), r)
r = vibration_rules.evaluate({"vibration": {"mm_s": None, "mm_s_last": None},
                              "rated_power_kw": 45.0})
check("puissance sans mesure → NON ÉVALUABLE (mesure listée)",
      r["evaluation"] == "non_evaluable" and any("vibration" in m for m in r["missing_info"]), r)

print()
if failures:
    print(f"ÉCHEC : {failures} test(s) en erreur.")
    sys.exit(1)
print("Tous les cas simples sont OK.")
