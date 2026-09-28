"""LOGIQUE ENVIRONNEMENTALE — croiser environnement × résultats des règles.

Chaîne demandée par le client :

    ENVIRONNEMENT → CONTRAINTE → IMPACT POSSIBLE → ANOMALIE MESURÉE
    → CAUSE POSSIBLE / HYPOTHÈSE → ACTION RECOMMANDÉE

PRINCIPES (non négociables) :
  - l'analyse environnementale s'exécute APRÈS les règles individuelles
    et ne les remplace pas ;
  - elle n'est déclenchée que sur une ANOMALIE réellement détectée
    (évaluation « problematique » ou « critique ») sur un paramètre
    lié à l'environnement — une mesure normale n'entraîne AUCUNE
    attribution de défaut (au plus : « paramètre à surveiller ») ;
  - les causes sont toujours des HYPOTHÈSES (formulations prudentes),
    jamais des certitudes ;
  - les données viennent exclusivement de environment_knowledge.py
    (fournies par le client — rien d'inventé ici).

Ce module est PUR : il reçoit les résultats des règles (listes de
dicts normalisés) et renvoie des dicts — ni base de données, ni
interface, ni source de la mesure.
"""

from diagnostic_rules.environment_knowledge import (
    ANOMALY_EVALUATIONS,
    ENVIRONMENTS,
    PARAMETER_LABELS,
)


def find_environment(name):
    """Retrouve un environnement par son libellé ou un mot-clé (alias).

    Tolérant avec les anciennes saisies (ex. « Laverie » retrouve
    « Laverie / Lavage / Décantation »). Renvoie None si inconnu.
    """
    if not name or not str(name).strip():
        return None
    needle = str(name).strip().casefold()
    for env in ENVIRONMENTS:
        if env["label"].casefold() == needle:
            return env
    for env in ENVIRONMENTS:
        for alias in env["aliases"]:
            if alias in needle or needle in alias:
                return env
    return None


def _result_label(result: dict) -> str:
    """Texte court du constat (ex. « Isolement des enroulements PROBLÉMATIQUE »)."""
    return f"{result['label']} ({result['evaluation_label']})"


def analyse_environment(environment, results: list[dict]) -> dict:
    """Croise l'environnement du moteur avec les résultats des règles.

    - environment : valeur du champ « Service » de la fiche moteur (ou None) ;
    - results     : résultats normalisés des modules de règles.

    Renvoie la section « Analyse environnementale » :
      known               : service répertorié dans la base ?
      environment         : nom affiché (code du service si retrouvé)
      description         : désignation complète officielle du service
      constraints         : contraintes environnementales (risques fournis)
      relevant_parameters : [{parameter, label}] paramètres sensibles ici
      triggered           : hypothèses de causes pour les anomalies détectées
      watch_note          : rappel des paramètres à surveiller (SANS défaut
                            inventé) — présent seulement si aucune anomalie
                            liée n'a été détectée
      message             : explication quand l'environnement est absent/inconnu
    """
    env = find_environment(environment)
    if env is None:
        message = (
            "Service non renseigné ou non répertorié "
            "(champ « Service » de la fiche moteur) : l'analyse "
            "environnementale n'est pas disponible."
        ) if environment else (
            "Service non renseigné "
            "(champ « Service » de la fiche moteur) : "
            "l'analyse environnementale n'est pas disponible."
        )
        return {
            "known": False,
            "environment": environment,
            "description": None,
            "constraints": [],
            "relevant_parameters": [],
            "triggered": [],
            "watch_note": None,
            "message": message,
        }

    # --- Hypothèses : UNIQUEMENT pour les anomalies réellement détectées ---
    triggered = []
    for result in results:
        if result.get("evaluation") not in ANOMALY_EVALUATIONS:
            continue
        for link in env["diagnostic_links"]:
            if link["parameter"] != result["parameter"]:
                continue
            if result["evaluation"] not in link["when"]:
                continue
            triggered.append({
                "parameter": result["parameter"],
                "parameter_label": PARAMETER_LABELS[link["parameter"]],
                "result_label": _result_label(result),
                "possible_causes": list(link["possible_causes"]),
                "recommendations": list(link["recommendations"]),
                "priority": link.get("priority"),
            })

    # --- Paramètres sensibles (avec libellés prêts pour l'affichage) ---
    relevant = [
        {"parameter": p, "label": PARAMETER_LABELS.get(p, p)}
        for p in env["relevant_parameters"]
    ]

    # --- Mesure normale → au plus un rappel de surveillance, jamais un défaut ---
    watch_note = None
    if not triggered:
        labels = [r["label"] for r in relevant]
        if labels:
            watch_note = (
                f"Aucune anomalie détectée sur les paramètres liés à cet environnement. "
                f"Paramètres particulièrement sensibles à surveiller ici : {', '.join(labels)}."
            )

    return {
        "known": True,
        "environment": env["label"],
        "description": env.get("description"),
        "constraints": list(env["risks"]),
        "relevant_parameters": relevant,
        "triggered": triggered,
        "watch_note": watch_note,
        "message": None,
    }


def attach_hypotheses(results: list[dict], env_analysis: dict) -> None:
    """Ajoute à chaque résultat ses hypothèses environnementales (en place).

    result[« environment_hypotheses »] = liste des entrées déclenchées
    pour CE paramètre (vide si aucune : rien n'est inventé).
    """
    for result in results:
        result["environment_hypotheses"] = [
            entry for entry in env_analysis["triggered"]
            if entry["parameter"] == result["parameter"]
        ]


def build_general_conclusion(results: list[dict], summary: dict, env_analysis: dict) -> list[str]:
    """Conclusion générale automatique — simple ASSEMBLAGE prudent des
    éléments déjà calculés (résultats des règles + comptage factuel +
    hypothèses d'environnement).

    Renvoie une liste de paragraphes (texte français prêt à afficher).
    Cette conclusion ne vaut PAS décision : la décision finale reste
    celle du technicien.
    """
    paragraphs: list[str] = []
    environment = env_analysis.get("environment")

    evaluated = (
        summary.get("conforme", 0) + summary.get("non_critique", 0)
        + summary.get("problematique", 0) + summary.get("critique", 0)
    )
    anomalies = [r for r in results if r.get("evaluation") in ANOMALY_EVALUATIONS]
    triggered = env_analysis.get("triggered", [])

    if evaluated == 0:
        paragraphs.append(
            "Aucune règle n'a pu être évaluée sur les données enregistrées : "
            "l'analyse ne permet pas de conclure (compléter les mesures du test)."
        )
        return paragraphs

    if anomalies:
        # 1) Anomalies AVEC hypothèses environnementales (base de connaissances)
        for entry in triggered:
            causes = " ; ".join(entry["possible_causes"])
            recs = " ; ".join(entry["recommendations"])
            sentence = f"Le moteur présente une anomalie : {entry['result_label']}. "
            if env_analysis.get("known") and environment:
                sentence += (
                    f"Compte tenu de son fonctionnement en « {environment} », "
                    f"la (les) cause(s) possible(s) à investiguer sont : {causes}. "
                )
            else:
                sentence += f"Causes possibles à investiguer : {causes}. "
            sentence += f"Contrôles recommandés : {recs}."
            paragraphs.append(sentence)

        # 2) Anomalies SANS correspondance environnementale (rien d'inventé)
        with_env = {t["parameter"] for t in triggered}
        without = [r for r in anomalies if r["parameter"] not in with_env]
        if without:
            labels = ", ".join(_result_label(r) for r in without)
            if env_analysis.get("known"):
                paragraphs.append(
                    f"Le moteur présente également : {labels}. Aucune cause "
                    f"environnementale spécifique n'est répertoriée dans la base "
                    f"pour ces anomalies ; leur origine reste à investiguer."
                )
            else:
                paragraphs.append(
                    f"Le moteur présente : {labels}. Origine à investiguer "
                    "(environnement de fonctionnement non renseigné)."
                )
    else:
        # Aucune anomalie : au plus un rappel des paramètres à surveiller
        if env_analysis.get("known") and env_analysis.get("watch_note"):
            paragraphs.append(env_analysis["watch_note"])
        else:
            paragraphs.append("Aucune anomalie détectée par les règles fournies sur ce test.")

    if summary.get("non_evaluable"):
        paragraphs.append(
            f"Attention : {summary['non_evaluable']} règle(s) n'ont pas pu être évaluées "
            "(information(s) manquante(s) ou seuil(s) non encore fourni(s))."
        )
    paragraphs.append(
        "Cette conclusion ne vaut pas décision : les causes listées sont des "
        "hypothèses à investiguer, et la décision finale appartient au technicien."
    )
    return paragraphs
