"""TESTS SIMPLES DES CAS LIMITES (sans base de données) — Étape 14.

Complète test_rules.py et test_environment.py avec les valeurs aux
bords (0, négatif, extrêmes) : la règle ne doit JAMAIS planter, et
répondre « non évaluable » quand la donnée est absurde.

Usage (depuis backend/) :  python tools/test_edge_cases.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from diagnostic_rules import current_rules, insulation_rules, temperature_rules  # noqa: E402

failures = 0


def check(name, condition, detail=""):
    global failures
    if condition:
        print(f"  OK   {name}")
    else:
        failures += 1
        print(f"  ÉCHEC {name} {detail}")


print("=== CAS LIMITE — courant (In = 0 ou négatif : jamais de plantage) ===")
r = current_rules.evaluate({"rated_current_a": 0, "measured_current_a": 15.0})
check("In = 0 → NON ÉVALUABLE (pas de division par zéro)",
      r["evaluation"] == "non_evaluable" and "invalide" in r["missing_info"][0])
r = current_rules.evaluate({"rated_current_a": -12.0, "measured_current_a": 15.0})
check("In négatif → NON ÉVALUABLE", r["evaluation"] == "non_evaluable")
r = current_rules.evaluate({"rated_current_a": 30.0, "measured_current_a": 1000.0})
check("I0 énorme (1000 A) → PROBLÉMATIQUE sans crash", r["evaluation"] == "problematique")

print("=== CAS LIMITE — isolement (mesure à 0, mesures partielles) ===")
r = insulation_rules.evaluate({
    "insulation_test_voltage_v": 1000,
    "insulation_mohm": {"ph1_ph2": 0, "ph2_ph3": 2.0, "ph3_ph1": 2.0,
                        "ph1_ground": 2.0, "ph2_ground": 2.0, "ph3_ground": 2.0},
})
check("mesure 0 MΩ (< Rmin) → PROBLÉMATIQUE (pas de confusion avec « absent »)",
      r["evaluation"] == "problematique")
r = insulation_rules.evaluate({
    "insulation_test_voltage_v": 500,
    "insulation_mohm": {"ph1_ph2": 2.0, "ph1_ground": 0.4},
})
labels = {i["key"]: i["evaluation_label"] for i in r["items"]}
check("mesures partielles : saisies évaluées + autres « NON MESURÉE »",
      labels["ph1_ph2"] == "CONFORME" and labels["ph2_ph3"] == "NON MESURÉE"
      and r["evaluation"] == "problematique")  # 0,4 < 0,5 → problématique

print("=== CAS LIMITE — température paliers (valeurs extrêmes) ===")
r = temperature_rules.evaluate({"temp_bearing_de_c": -10.0, "temp_bearing_nde_c": 20.0})
check("palier DE -10 °C → NON CRITIQUE", r["evaluation"] == "non_critique")
r = temperature_rules.evaluate({"temp_bearing_de_c": 250.0, "temp_bearing_nde_c": 250.0})
check("paliers 250 °C → CRITIQUE", r["evaluation"] == "critique")
r = temperature_rules.evaluate({"temp_bearing_de_c": 0.0, "temp_bearing_nde_c": 0.0})
check("paliers 0,0 °C → NON CRITIQUE (≥70 seulement)", r["evaluation"] == "non_critique")

print()
if failures:
    print(f"ÉCHEC : {failures} test(s) en erreur.")
    sys.exit(1)
print("Tous les cas limites sont OK.")
