"""Moteur de diagnostic — assemble les données puis applique les règles.

SÉPARATION DES RESPONSABILITÉS (demande du client) :
  - diagnostic_rules/            : les règles (modules purs) ;
  - CE FICHIER (le moteur)       : récupère les données du test
    (fiche en base + échantillons du kit), les met en forme et appelle
    chaque module de règles ;
  - page Analyse (frontend)      : AFFICHE les résultats, ne calcule rien.

Le moteur ne dépend pas de la SOURCE d'une mesure (§10 du cahier) :
il prend la valeur de la fiche si elle existe, sinon celle des
échantillons du kit — les règles reçoivent juste des nombres.

Le moteur NE DÉCIDE RIEN : pas de « remis en service / à réparer »
automatique. La décision finale appartient au technicien.
"""

from diagnostic_rules import RULE_MODULES, environment_rules
from diagnostic_rules.base import CRITIQUE, NON_EVALUABLE, NON_CRITIQUE, PROBLEMATIQUE


def _collect(test, samples: list[dict]) -> tuple[dict, dict]:
    """Réunit les données d'un test + la source de chaque valeur.

    Renvoie (données, sources) — « sources » contient, pour certains
    paramètres, un texte expliquant d'où vient la valeur mesurée
    (fiche saisie ou échantillons du kit).
    """
    measurements = test.measurements
    motor = test.motor

    data = {
        "mode": test.mode,
        # Plaque moteur
        "rated_current_a": motor.rated_current_a if motor is not None else None,
        "rated_power_kw": motor.rated_power_kw if motor is not None else None,
        # Mesures (fiche = saisie manuelle ; échantillons = kit)
        "measured_current_a": None,
        "insulation_test_voltage_v": (
            measurements.insulation_test_voltage_v if measurements is not None else None
        ),
        "insulation_mohm": {
            "ph1_ph2": measurements.ph1_ph2_mohm if measurements is not None else None,
            "ph2_ph3": measurements.ph2_ph3_mohm if measurements is not None else None,
            "ph3_ph1": measurements.ph3_ph1_mohm if measurements is not None else None,
            "ph1_ground": measurements.ph1_ground_mohm if measurements is not None else None,
            "ph2_ground": measurements.ph2_ground_mohm if measurements is not None else None,
            "ph3_ground": measurements.ph3_ground_mohm if measurements is not None else None,
        },
        "winding_resistance_ohm": {
            "r12": measurements.r12_ohm if measurements is not None else None,
            "r23": measurements.r23_ohm if measurements is not None else None,
            "r31": measurements.r31_ohm if measurements is not None else None,
        },
        # É16 — continuité globale (appréciation Oui/Non du technicien)
        "continuity_ok": (
            measurements.continuity_ok if measurements is not None else None
        ),
        # É16 — température : PALIERS (règle < 70 °C). La série du kit
        # reste un GRAPHIQUE : elle n'alimente plus la règle (décision
        # client : seuls les 2 paliers comptent).
        "temp_bearing_de_c": (
            measurements.temp_bearing_de_c if measurements is not None else None
        ),
        "temp_bearing_nde_c": (
            measurements.temp_bearing_nde_c if measurements is not None else None
        ),
        "legacy_temperature_c": (
            measurements.temperature_c if measurements is not None else None
        ),
        # Vibration : kit ET fiche en mm/s (décision client). Seuils
        # fournis par le client (24/09/2026) : 4,5 mm/s (P ≤ 300 kW),
        # 7,1 mm/s (P > 300 kW) — voir diagnostic_rules/vibration_rules.
        "vibration": {
            "mm_s": measurements.vibration_mm_s if measurements is not None else None,
            "mm_s_last": next(
                (s.get("vibration", {}).get("global_mm_s") for s in reversed(samples)
                 if s.get("vibration", {}).get("global_mm_s") is not None),
                None,
            ),
        },
    }
    sources: dict[str, str] = {}

    # --- Courant : fiche d'abord, sinon moyenne des échantillons du kit ---
    if measurements is not None and measurements.current_a is not None:
        data["measured_current_a"] = measurements.current_a
        sources["current_no_load"] = "mesure unique de la fiche"
    else:
        currents = [s["current_a"] for s in samples if s.get("current_a") is not None]
        if currents:
            data["measured_current_a"] = sum(currents) / len(currents)
            sources["current_no_load"] = f"moyenne des {len(currents)} échantillons du kit"

    # --- Température : source = fiche (paliers) — la série du kit est
    # un graphique SANS règle (décision client É16) ---
    if measurements is not None and (
        measurements.temp_bearing_de_c is not None
        or measurements.temp_bearing_nde_c is not None
    ):
        sources["temperature"] = "mesures des paliers (fiche)"
    elif measurements is not None and measurements.temperature_c is not None:
        sources["temperature"] = "valeur unique de la fiche (ancien format)"

    # --- Vibration : fiche d'abord, sinon dernier échantillon du kit ---
    if measurements is not None and measurements.vibration_mm_s is not None:
        sources["vibration"] = "mesure de vibration de la fiche"
    elif data["vibration"]["mm_s_last"] is not None:
        sources["vibration"] = "dernier échantillon du kit"

    return data, sources


def evaluate_test(test, samples: list[dict]) -> dict:
    """Applique toutes les règles au test et renvoie le rapport complet."""
    data, sources = _collect(test, samples)

    results = [module.evaluate(data) for module in RULE_MODULES]
    for result in results:
        result["measured_source"] = sources.get(result["parameter"])

    # --- Synthèse : simple COMPTAGE des évaluations (aucune décision) ---
    counts = {"conforme": 0, "non_critique": 0, "problematique": 0, "critique": 0}
    not_evaluable = 0
    for result in results:
        code = result["evaluation"]
        if code == NON_EVALUABLE:
            not_evaluable += 1
        elif code in counts:
            counts[code] += 1

    issues = counts[PROBLEMATIQUE] + counts[CRITIQUE]
    if issues:
        overall = "issues"            # au moins une règle non respectée
    elif counts["conforme"] or counts[NON_CRITIQUE]:
        overall = "ok"                # règles évaluées, rien à signaler
    else:
        overall = "indeterminate"     # rien n'a pu être évalué

    return {
        "test_id": test.test_id,
        "mode": test.mode,
        "status": test.status,
        "motor": (
            {"motor_id": test.motor.motor_id, "rated_current_a": test.motor.rated_current_a}
            if test.motor is not None else None
        ),
        "results": results,
        "summary": {
            **counts,
            "non_evaluable": not_evaluable,
            "overall": overall,
        },
    }


def evaluate_test_full(test, samples: list[dict]) -> dict:
    """Rapport complet : règles individuelles PUIS analyse environnementale.

    L'analyse environnementale (base de connaissances séparée,
    diagnostic_rules/environment_*.py) est appelée APRÈS les règles
    individuelles et ne les remplace pas : elle ne fait qu'ajouter,
    pour les anomalies détectées, des hypothèses de causes possibles
    liées à l'environnement de fonctionnement du moteur.
    """
    report = evaluate_test(test, samples)

    environment = test.motor.service if test.motor is not None else None
    env_analysis = environment_rules.analyse_environment(environment, report["results"])
    environment_rules.attach_hypotheses(report["results"], env_analysis)
    report["environment_analysis"] = env_analysis
    report["general_conclusion"] = environment_rules.build_general_conclusion(
        report["results"], report["summary"], env_analysis
    )
    return report
