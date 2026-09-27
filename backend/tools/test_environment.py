"""TESTS SIMPLES DE L'ANALYSE ENVIRONNEMENTALE (sans base de données).

Vérifie le croisement environnement × résultats des règles avec les
cas demandés par le client. Usage (depuis backend/) :

    python tools/test_environment.py

Rappels vérifiés ici :
  - anomalie détectée  → hypothèses de causes POSSIBLES (jamais certaines) ;
  - mesure normale     → AUCUNE cause attribuée (au plus « à surveiller ») ;
  - environnement inconnu/absent → message clair, aucun plantage ;
  - rien d'inventé : les causes/recommandations viennent de la base.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from diagnostic_rules import environment_rules  # noqa: E402
from diagnostic_rules.environment_knowledge import (  # noqa: E402
    ANOMALY_EVALUATIONS,
    ENVIRONMENTS,
    PARAMETER_LABELS,
)

failures = 0


def check(name, condition, detail=""):
    global failures
    if condition:
        print(f"  OK   {name}")
    else:
        failures += 1
        print(f"  ÉCHEC {name} {detail}")


def result(parameter, evaluation):
    """Fabrique un résultat de règle minimal (même format que le moteur)."""
    return {
        "parameter": parameter,
        "label": PARAMETER_LABELS[parameter],
        "evaluation": evaluation,
        "evaluation_label": evaluation.upper(),
    }


print("=== Base de connaissances : cohérence ===")
check("7 environnements répertoriés", len(ENVIRONMENTS) == 7)
codes_ok = all(
    link["parameter"] in PARAMETER_LABELS
    for env in ENVIRONMENTS for link in env["diagnostic_links"]
)
check("tous les liens pointent vers des paramètres connus", codes_ok)
when_ok = all(
    set(link["when"]) <= set(ANOMALY_EVALUATIONS)
    for env in ENVIRONMENTS for link in env["diagnostic_links"]
)
check("les conditions de déclenchement sont des anomalies", when_ok)

print("=== Cas 1 : Laverie + isolement PROBLÉMATIQUE (exemple du client) ===")
results = [result("insulation", "problematique"), result("temperature", "non_critique")]
env = environment_rules.analyse_environment("Laverie / Lavage / Décantation", results)
check("environnement reconnu", env["known"] and env["environment"] == "Laverie / Lavage / Décantation")
check("1 lien déclenché (isolement seulement)", len(env["triggered"]) == 1
      and env["triggered"][0]["parameter"] == "insulation")
causes = " ".join(env["triggered"][0]["possible_causes"]).lower()
check("cause possible : humidité", "humidité" in causes)
check("recommandation : étanchéité / joints",
      any("étanchéité" in r.lower() for r in env["triggered"][0]["recommendations"]))
check("formulation prudente (« possible »)", "possible" in causes)
check("aucune cause attribuée à la température (non critique)",
      all(t["parameter"] != "temperature" for t in env["triggered"]))
environment_rules.attach_hypotheses(results, env)
check("les hypothèses sont rattachées au résultat d'isolement",
      len(results[0]["environment_hypotheses"]) == 1)
check("aucune hypothèse sur la température", results[1]["environment_hypotheses"] == [])

print("=== Cas 2 : Laverie + isolement CONFORME (pas de défaut inventé) ===")
env = environment_rules.analyse_environment(
    "Laverie / Lavage / Décantation", [result("insulation", "conforme")])
check("aucune hypothèse déclenchée", env["triggered"] == [])
check("note de surveillance (sans défaut attribué)",
      env["watch_note"] and "Isolement" in env["watch_note"])

print("=== Cas 3 : Concassage + vibration PROBLÉMATIQUE ===")
env = environment_rules.analyse_environment(
    "Concassage / Criblage", [result("vibration", "problematique")])
recs = " ".join(env["triggered"][0]["recommendations"]).lower()
check("recommandations : roulements / alignement / équilibrage / fixation",
      "roulements" in recs and "alignement" in recs
      and "équilibrage" in recs and "fixation" in recs)

print("=== Cas 4 : Sécherie + température CRITIQUE ===")
env = environment_rules.analyse_environment(
    "Sécherie / Fours rotatifs", [result("temperature", "critique")])
causes = " ".join(env["triggered"][0]["possible_causes"]).lower()
check("causes : refroidissement / surchauffe",
      "refroidissement" in causes and "surchauffe" in causes)

print("=== Cas 5 : environnement inconnu ou absent ===")
env = environment_rules.analyse_environment("Atelier 3", [result("insulation", "problematique")])
check("inconnu → known=False + message clair",
      not env["known"] and "non répertorié" in env["message"])
env = environment_rules.analyse_environment(None, [result("insulation", "problematique")])
check("absent → known=False + message clair",
      not env["known"] and "non renseigné" in env["message"])

print("=== Cas 6 : conclusion générale (assemblage prudent) ===")
res6 = [result("insulation", "problematique"), result("temperature", "non_critique")]
env = environment_rules.analyse_environment("Laverie / Lavage / Décantation", res6)
summary = {"conforme": 1, "non_critique": 1, "problematique": 1,
           "critique": 0, "non_evaluable": 2}
paragraphs = environment_rules.build_general_conclusion(res6, summary, env)
text = " ".join(paragraphs)
check("la conclusion mentionne l'anomalie d'isolement", "isolement" in text.lower())
check("la conclusion cite l'environnement (Laverie)", "Laverie" in text)
check("les causes restent des hypothèses (« possible »)", "possible" in text.lower())
check("la décision finale reste celle du technicien", "technicien" in text.lower())
check("aucune certitude affirmée", "est causé par" not in text.lower())

print("=== Cas 7 : anomalie SANS correspondance environnementale ===")
# Sécherie : la base ne fournit aucune cause « courant » → rien d'inventé
res7 = [result("current_no_load", "problematique")]
env7 = environment_rules.analyse_environment("Sécherie / Fours rotatifs", res7)
check("aucune hypothèse inventée pour le courant", env7["triggered"] == [])
paras = environment_rules.build_general_conclusion(
    res7, {"conforme": 0, "non_critique": 0, "problematique": 1, "critique": 0,
           "non_evaluable": 4}, env7)
t7 = " ".join(paras)
check("l'anomalie est mentionnée (pas cachée)", "Courant à vide" in t7)
check("l'origine reste « à investiguer »", "investiguer" in t7)

print("=== Cas 8 : aucune règle évaluable (fiche vide) ===")
paras = environment_rules.build_general_conclusion(
    [], {"conforme": 0, "non_critique": 0, "problematique": 0, "critique": 0,
         "non_evaluable": 5}, environment_rules.analyse_environment("Laverie", []))
check("message « ne permet pas de conclure »",
      "ne permet pas de conclure" in paras[0])

print()
if failures:
    print(f"ÉCHEC : {failures} test(s) en erreur.")
    sys.exit(1)
print("Tous les cas environnementaux sont OK.")
