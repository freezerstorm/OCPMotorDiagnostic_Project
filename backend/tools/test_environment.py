"""TESTS SIMPLES DE L'ANALYSE ENVIRONNEMENTALE (sans base de données).

Vérifie le croisement service × résultats des règles avec les cas
demandés par le client. Usage (depuis backend/) :

    python tools/test_environment.py

Rappels vérifiés ici :
  - catalogue = les 22 désignations officielles OCP (décision client) ;
  - anomalie détectée  → hypothèses de causes POSSIBLES (jamais certaines) ;
  - mesure normale     → AUCUNE cause attribuée (au plus « à surveiller ») ;
  - service inconnu/absent → message clair, aucun plantage ;
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
check("22 services OCP répertoriés", len(ENVIRONMENTS) == 22, f"trouvés : {len(ENVIRONMENTS)}")
labels = [env["label"] for env in ENVIRONMENTS]
attendus = [
    "KMB / KMB2", "KM03", "PE/RE", "PE/SI", "PE/EI", "KTD / ZKTD", "KTB",
    "KTR", "DS", "KLB", "KLR", "KL01 / KL02 / KL03", "LM/X / LMX / L-EXT",
    "LM/E / LME", "PIPE", "PP.ST", "KPPA", "PC/SI", "PC ASA", "PC/IE",
    "PC/ZB", "C M/K",
]
check("libellés exacts (codes officiels)", labels == attendus)
check("chaque service a une description non vide",
      all(env.get("description", "").strip() for env in ENVIRONMENTS))
check("chaque service a au moins une contrainte",
      all(len(env["risks"]) >= 1 for env in ENVIRONMENTS))
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

print("=== Cas 1 : KLB + isolement PROBLÉMATIQUE (exemple du client) ===")
results = [result("insulation", "problematique"), result("temperature", "non_critique")]
env = environment_rules.analyse_environment("KLB", results)
check("service reconnu", env["known"] and env["environment"] == "KLB")
check("description officielle renvoyée",
      env["description"] == "Khouribga Laverie Béni Idir — Unité de lavage, criblage humide, hydrocyclonage et flottation.")
check("1 lien déclenché (isolement seulement)", len(env["triggered"]) == 1
      and env["triggered"][0]["parameter"] == "insulation")
causes = " ".join(env["triggered"][0]["possible_causes"]).lower()
check("cause possible : humidité / infiltration", "humidité" in causes or "infiltration" in causes)
check("recommandation : étanchéité boîte à bornes",
      any("boîte à bornes" in r.lower() for r in env["triggered"][0]["recommendations"]))
check("formulation prudente (« hypothèse »)", "hypothèse" in causes)
check("aucune cause attribuée à la température (non critique)",
      all(t["parameter"] != "temperature" for t in env["triggered"]))
environment_rules.attach_hypotheses(results, env)
check("les hypothèses sont rattachées au résultat d'isolement",
      len(results[0]["environment_hypotheses"]) == 1)
check("aucune hypothèse sur la température", results[1]["environment_hypotheses"] == [])

print("=== Cas 2 : KLB + isolement CONFORME (pas de défaut inventé) ===")
results = [result("insulation", "conforme")]
env = environment_rules.analyse_environment("KLB", results)
check("service reconnu", env["known"])
check("aucune hypothèse déclenchée", env["triggered"] == [])
check("note de surveillance présente", bool(env["watch_note"]))

print("=== Cas 3 : saisie tolérante (alias, casse, variantes de code) ===")
for saisie, attendu in [
    ("klb", "KLB"),
    (" KLB ", "KLB"),
    ("zktd", "KTD / ZKTD"),
    ("lmx", "LM/X / LMX / L-EXT"),
    ("LME", "LM/E / LME"),
    ("kl02", "KL01 / KL02 / KL03"),
]:
    env = environment_rules.analyse_environment(saisie, [])
    check(f"« {saisie} » → {attendu}", env["known"] and env["environment"] == attendu)

print("=== Cas 4 : service inconnu ou absent (aucun plantage) ===")
env = environment_rules.analyse_environment("SERVICE IMAGINAIRE X", [])
check("inconnu → known=False", env["known"] is False)
check("message explicatif présent", bool(env["message"]))
check("aucune hypothèse inventée", env["triggered"] == [])
env = environment_rules.analyse_environment(None, [])
check("absent → known=False", env["known"] is False)
check("message explicatif présent", bool(env["message"]))
env = environment_rules.analyse_environment("Mine à ciel ouvert", [])
check("ancien libellé générique → non répertorié (décision client)", env["known"] is False)

print("=== Cas 5 : conclusion générale prudente ===")
results = [result("insulation", "critique")]
env = environment_rules.analyse_environment("KLB", results)
paras = environment_rules.build_general_conclusion(results, {"conforme": 0, "non_critique": 0, "problematique": 0, "critique": 1, "non_evaluable": 0}, env)
texte = " ".join(paras).lower()
check("l'hypothèse environnementale figure dans la conclusion", "klb" in texte)
check("formulation prudente dans la conclusion", "hypothèse" in texte or "à investiguer" in texte)
check("rappel : la décision reste au technicien", "décision" in texte)

print()
if failures:
    print(f"ÉCHEC : {failures} vérification(s) en erreur.")
    sys.exit(1)
print("Toutes les vérifications environnementales sont passées.")
