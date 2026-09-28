// ============================================================
// OPTIONS DU RAPPORT PDF — cases de la page Analyse.
//
// Décision client (28/09/2026, révisée le même jour) : la fiche OCP
// est TOUJOURS complète dans le PDF ; les informations SUPPLÉMENTAIRES
// issues de l'analyse n'y figurent que si le technicien les coche.
// SEULE EXCEPTION : le verdict global de chaque règle est COCHÉ PAR
// DÉFAUT (il complète la colonne « Observation » des tableaux de
// mesures, qui donne le détail mesure par mesure).
// Les choix sont retenus SUR CE POSTE (localStorage) et transmis au
// backend en paramètre « opts » du GET /tests/{id}/report.pdf.
// ============================================================
const KEY = 'ocp.rapport-pdf-options';

/** Case cochée par défaut : le verdict de chaque règle. */
const PAR_DEFAUT = ['verdicts'];

/** Options cochées (liste de codes) — verdict seul par défaut. */
export function getReportOptions() {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw === null) return [...PAR_DEFAUT]; // jamais réglé sur ce poste
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((o) => typeof o === 'string') : [...PAR_DEFAUT];
  } catch {
    return [...PAR_DEFAUT];
  }
}

/** Mémorise les cases cochées sur ce poste. */
export function setReportOptions(options) {
  localStorage.setItem(KEY, JSON.stringify(options));
}

/** « ?opts=a,b » — chaîne vide si aucune case cochée. */
export function reportOptionsQuery() {
  const options = getReportOptions();
  return options.length ? `?opts=${options.join(',')}` : '';
}
