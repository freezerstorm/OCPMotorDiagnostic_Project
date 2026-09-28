// ============================================================
// CONSTANTES COMMUNES — codes machine + libellés français.
//
// PRINCIPE : le frontend et le backend échangent des CODES
// stables en anglais (ex. 'manual', 'repair') ; les libellés
// affichés (ex. « Test manuel ») sont définis ici, à côté des
// codes, via les tableaux « *_LABELS ». Pour changer un texte
// affiché, on ne modifie que ce fichier.
// ============================================================

// --- Décision finale du technicien (§14) ---
export const DECISIONS = {
  SERVICED: 'serviced', // Remis en service
  REPAIR: 'repair',     // Envoyé en réparation
};

export const DECISION_LABELS = {
  [DECISIONS.SERVICED]: 'Remis en service',
  [DECISIONS.REPAIR]: 'Envoyé en réparation',
};

// --- Mode de test (§3) ---
export const TEST_MODES = {
  MANUAL: 'manual',
  AUTO: 'auto',
};

export const TEST_MODE_LABELS = {
  [TEST_MODES.MANUAL]: 'Test manuel',
  [TEST_MODES.AUTO]: 'Test automatique',
};

// --- Statuts d'un test de diagnostic ---
export const TEST_STATUSES = {
  DRAFT: 'draft',
  OFFLINE_VALIDATED: 'offline_validated',
  ACQUIRING: 'acquiring',
  COMPLETED: 'completed',
  ERROR: 'error',
  ARCHIVED: 'archived',
};

export const TEST_STATUS_LABELS = {
  [TEST_STATUSES.DRAFT]: 'Brouillon',
  [TEST_STATUSES.OFFLINE_VALIDATED]: 'Hors tension validé',
  [TEST_STATUSES.ACQUIRING]: 'En acquisition',
  [TEST_STATUSES.COMPLETED]: 'Terminé',
  [TEST_STATUSES.ERROR]: 'Erreur',
  [TEST_STATUSES.ARCHIVED]: 'Archivé',
};

// --- Tension de test d'isolement (règle « 1 kΩ par volt ») ---
// Seules ces quatre valeurs sont admises (formulaire + validation API).
export const INSULATION_TEST_VOLTAGES = [500, 1000, 2500, 5000];

// NB — la liste des SERVICES n'est plus définie ici : elle vient du
// catalogue en base (GET /api/v1/services, migration 0011 : 22
// désignations OCP officielles + désignations ajoutées par les
// techniciens). Le contexte environnemental utilisé par l'analyse vit
// dans backend/diagnostic_rules/environment_knowledge.py.

// --- Rapport PDF : informations supplémentaires sélectionnables ---
// La fiche OCP est toujours complète dans le PDF ; ces éléments
// (issus de l'ANALYSE) ne s'y ajoutent que si le technicien les coche
// sur la page Analyse. Tous décochés par défaut SAUF « verdicts »
// (verdict de chaque règle, coché par défaut — décision 28/09/2026).
export const REPORT_PDF_OPTIONS = [
  { key: 'verdicts', label: 'Verdict de chaque règle (CONFORME / NON CRITIQUE / PROBLÉMATIQUE / NON ÉVALUABLE)' },
  { key: 'interpretations', label: 'Interprétation de chaque règle' },
  { key: 'risques', label: 'Risques / causes possibles (règles en défaut)' },
  { key: 'recommandations', label: 'Actions recommandées (règles en défaut)' },
  { key: 'sources', label: 'Source de chaque mesure (fiche ou kit)' },
  { key: 'synthese', label: 'Synthèse du diagnostic (comptage par évaluation)' },
  { key: 'conclusion', label: 'Conclusion générale automatique' },
  { key: 'env_hypotheses', label: 'Environnement — hypothèses de causes et contrôles recommandés' },
  { key: 'env_service', label: 'Environnement — fiche du service (description, contraintes, paramètres sensibles)' },
];
