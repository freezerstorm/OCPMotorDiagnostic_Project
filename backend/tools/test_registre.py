"""TESTS SIMPLES DU REGISTRE NUMÉRIQUE (sans base de données).

Vérifie la correspondance essai → 14 colonnes du registre RÉEL :
champs mappés, champs absents laissés VIDES (rien d'inventé), format
des valeurs (« 500V », « 78A »). L'ajout effectif en base, l'import du
fichier réel et l'idempotence sont vérifiés par les outils et l'essai
bout-en-bout (PATCH décision → GET /registre).

Usage (depuis backend/) :  python tools/test_registre.py
"""

import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.registre import (  # noqa: E402
    _fmt_num,
    _glued,
    cellules_critiques_du_test,
    entry_values_from_test,
)

failures = 0


def check(name, condition, detail=""):
    global failures
    if condition:
        print(f"  OK   {name}")
    else:
        failures += 1
        print(f"  ÉCHEC {name} {detail}")


# ------------------------------------------------------------------
# Jeux d'essai factices (mêmes attributs que les objets ORM utilisés)
# ------------------------------------------------------------------
def fake_test(*, motor=None, measurements=None, samples=None, work_order=None,
              observation=None):
    return SimpleNamespace(
        motor=motor,
        measurements=measurements,
        samples=samples or [],
        work_order=work_order,
        observation=observation,
        created_at=datetime(2026, 9, 17, 10, 30),
        source_ref=None,
        test_id="T-0100",
        id=999,
        decision=None,
    )


def full_motor():
    return SimpleNamespace(
        motor_id="M-1042", matricule="M607485", designation="Pompe eau process",
        coupling="Étoile",
        service="Laverie / Lavage / Décantation", rated_voltage_v=500.0,
        rated_current_a=78.0, rated_power_kw=45.0, di_ot="DI 1747782",
    )


def full_measurements():
    return SimpleNamespace(
        current_a=41.0,
        ph1_ground_mohm=310.0, ph2_ground_mohm=298.0, ph3_ground_mohm=305.0,
        ph1_ph2_mohm=145.0, ph2_ph3_mohm=138.0, ph3_ph1_mohm=141.0,
        r12_ohm=0.152, r23_ohm=0.152, r31_ohm=0.153,
    )


print("\n=== Format des valeurs (style du registre réel) ===")
check("310.0 → « 310 »", _fmt_num(310.0) == "310", _fmt_num(310.0))
check("0.152 → « 0,152 »", _fmt_num(0.152) == "0,152", _fmt_num(0.152))
check("None → vide", _fmt_num(None) is None)
check("500 V → « 500V »", _glued(500.0, "V") == "500V", _glued(500.0, "V"))
check("78 A → « 78A »", _glued(78.0, "A") == "78A")
check("45 kW → « 45 kW »", _glued(45.0, " kW") == "45 kW")

print("\n=== Essai complet (fiche moteur + mesures) ===")
v = entry_values_from_test(fake_test(motor=full_motor(), measurements=full_measurements(),
                                     work_order="OT 54135995", observation="Vibration"))
check("1. Date = date de l'essai", str(v["entry_date"]) == "2026-09-17", v["entry_date"])
check("2. Matricule = matricule moteur", v["matricule"] == "M607485")
check("3. DI/OT = ORDRE de la session", v["di_ot"] == "OT 54135995")
check("4. Service (Sce)", v["service"] == "Laverie / Lavage / Décantation")
check("5. Un = « 500V »", v["un_v"] == "500V", v["un_v"])
check("6. In = « 78A »", v["in_a"] == "78A", v["in_a"])
check("7. U0 vide (non capturée)", v["uo_v"] is None)
check("8. I0 = courant de la fiche « 41A »", v["io_a"] == "41A", v["io_a"])
check("9. PH_PH = isolements entre phases (Ph1-Ph2/Ph2-Ph3/Ph3-Ph1)",
      v["isolement"] == "145 / 138 / 141 MΩ", v["isolement"])
check("9b. PH_m = isolements phase-masse (Ph1-M/Ph2-M/Ph3-M)",
      v["isolement_ph_m"] == "310 / 298 / 305 MΩ", v["isolement_ph_m"])
check("9c. R = résistances des enroulements (R12/R23/R31)",
      v["r"] == "0,152 / 0,152 / 0,153 Ω", v["r"])
check("10. Nature = désignation du moteur", v["nature"] == "Pompe eau process")
check("11. Puissance = « 45 kW »", v["puissance"] == "45 kW", v["puissance"])
check("12. Société vide (non capturée)", v["societe"] is None)
check("13. BT/MT vide (non capturée)", v["bt_mt"] is None)
check("14. Observation = observation du technicien", v["observation"] == "Vibration")

print("\n=== Essai minimal (rien d'inventé) ===")
v2 = entry_values_from_test(fake_test(
    motor=SimpleNamespace(motor_id="M-X", matricule=None, designation=None,
                          coupling=None, service=None,
                          rated_voltage_v=None, rated_current_a=None,
                          rated_power_kw=None, di_ot=None),
    measurements=None,
    samples=[SimpleNamespace(current_a=10.0), SimpleNamespace(current_a=12.0)],
))
check("Matricule → ID moteur (seul identifiant disponible)", v2["matricule"] == "M-X")
check("DI/OT vide", v2["di_ot"] is None)
check("Un/In vides", v2["un_v"] is None and v2["in_a"] is None)
check("I0 = moyenne des échantillons kit", v2["io_a"] == "11A", v2["io_a"])
check("PH_PH / PH_m / R vides (pas de mesures)",
      v2["isolement"] is None and v2["isolement_ph_m"] is None and v2["r"] is None)
check("Nature vide si moteur sans désignation", v2["nature"] is None)
check("Puissance vide", v2["puissance"] is None)
check("Observation vide", v2["observation"] is None)

print("\n=== DI/OT : repli sur la fiche moteur ===")
v3 = entry_values_from_test(fake_test(motor=full_motor(), work_order=None))
check("ORDRE absent → DI/OT du moteur", v3["di_ot"] == "DI 1747782")

print("=== Société de réparation (décision client 24/09/2026) ===")
# Sans société : colonne vide (comportement inchangé)
valeurs = entry_values_from_test(fake_test(motor=full_motor()))
check("sans société de réparation → colonne Société VIDE",
      valeurs["societe"] is None, valeurs["societe"])
# Avec société (décision « Envoyé en réparation ») : colonne remplie
valeurs = entry_values_from_test(
    fake_test(motor=full_motor()), societe_reparation="FAR")
check("société « FAR » saisie → colonne Société « FAR »",
      valeurs["societe"] == "FAR", valeurs["societe"])
# Les autres colonnes restent intactes
check("les autres colonnes inchangées (Un « 500V », observation)",
      valeurs["un_v"] == "500V" and "observation" in valeurs, valeurs["un_v"])

print("\n=== Cellules en défaut (rouge du registre, décision 28/09/2026) ===")


def result_factice(parameter, evaluation):
    return {"parameter": parameter, "evaluation": evaluation}


def analyse_factice(results, iso_items=None):
    if iso_items is not None:
        results = [dict(r, items=iso_items) if r["parameter"] == "insulation" else r
                   for r in results]
    return {"results": results}


def iso_items(ph_ph_eval, ph_m_eval):
    return [
        {"key": "ph1_ph2", "evaluation": ph_ph_eval},
        {"key": "ph2_ph3", "evaluation": "conforme"},
        {"key": "ph3_ph1", "evaluation": "conforme"},
        {"key": "ph1_ground", "evaluation": ph_m_eval},
        {"key": "ph2_ground", "evaluation": "conforme"},
        {"key": "ph3_ground", "evaluation": "conforme"},
    ]


check("isolement ph-m en défaut → PH_m rouge SEULEMENT",
      cellules_critiques_du_test(analyse_factice(
          [result_factice("insulation", "problematique")],
          iso_items("conforme", "problematique"))) == ["isolement_ph_m"])
check("isolement ph-ph en défaut → PH_PH rouge SEULEMENT",
      cellules_critiques_du_test(analyse_factice(
          [result_factice("insulation", "problematique")],
          iso_items("problematique", "conforme"))) == ["isolement"])
check("isolement conforme → aucune cellule rouge",
      cellules_critiques_du_test(analyse_factice(
          [result_factice("insulation", "conforme")],
          iso_items("conforme", "conforme"))) == [])
check("courant hors tolérance → I0 rouge",
      cellules_critiques_du_test(analyse_factice(
          [result_factice("current_no_load", "problematique")])) == ["io_a"])
check("résistances différentes → R rouge",
      cellules_critiques_du_test(analyse_factice(
          [result_factice("winding_resistance", "problematique")])) == ["r"])
check("évaluation critique → cellule rouge aussi",
      cellules_critiques_du_test(analyse_factice(
          [result_factice("current_no_load", "critique")])) == ["io_a"])
check("tout en défaut → 4 cellules rouges",
      cellules_critiques_du_test(analyse_factice(
          [result_factice("current_no_load", "problematique"),
           result_factice("winding_resistance", "problematique"),
           result_factice("insulation", "problematique")],
          iso_items("problematique", "problematique")))
      == ["io_a", "r", "isolement", "isolement_ph_m"])

print()
if failures:
    print(f"ÉCHECS : {failures}")
    sys.exit(1)
print("Registre numérique : tous les contrôles sont passés.")
