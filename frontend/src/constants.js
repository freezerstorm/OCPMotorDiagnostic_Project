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

// Environnements de fonctionnement (ateliers) — la liste reste
// modifiable ici. Ces libellés correspondent à la base de connaissances
// environnementales du backend
// (backend/diagnostic_rules/environment_knowledge.py) : l'analyse
// environnementale de la page Analyse s'appuie dessus.
export const SERVICE_OPTIONS = [
  'Mine à ciel ouvert',
  'Concassage / Criblage',
  'Laverie / Lavage / Décantation',
  'Flottation',
  'Sécherie / Fours rotatifs',
  'Station de tête du Slurry Pipeline',
  'Parc de stockage et reprise',
];
