// ============================================================
// SERVICES API — les appels HTTP vers le backend.
//
// Tous les appels passent par le proxy Vite (/api → port 8000 en
// développement) : le navigateur ne connaît jamais l'adresse du
// backend directement.
//
// Chaque fonction correspond à une route du backend (voir
// backend/app/api/) : si l'API change, c'est ICI qu'on adapte
// l'appel — jamais dans les pages.
// ============================================================

const API_BASE = '/api/v1';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    // Tente de lire le détail renvoyé par l'API (ex. « Moteur X déjà enregistré »)
    let detail = `Erreur ${response.status}`;
    try {
      const data = await response.json();
      if (typeof data?.detail === 'string') {
        detail = data.detail;
      } else if (Array.isArray(data?.detail)) {
        // Erreurs de validation de l'API (liste) : on garde le premier
        // message lisible (sans le préfixe technique « Value error, »).
        const first = data.detail
          .map((e) => String(e?.msg ?? '').replace(/^Value error,\s*/, ''))
          .find(Boolean);
        if (first) detail = first;
      }
    } catch {
      /* réponse non JSON : on garde le message générique */
    }
    // Le statut HTTP voyage avec l'erreur : les pages peuvent
    // distinguer un « introuvable » (404) d'une panne réseau.
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

/** Liste des fiches de diagnostic (les plus récentes d'abord). */
export function fetchTests(limit = 50) {
  return request(`/tests?limit=${limit}`);
}

/** Détail d'une fiche de diagnostic (avec moteur + mesures). */
export function fetchTest(testId) {
  return request(`/tests/${encodeURIComponent(testId)}`);
}

/** Fiche d'un moteur (404 si inconnu) — auto-remplissage du formulaire. */
export function fetchMotor(motorId) {
  return request(`/motors/${encodeURIComponent(motorId)}`);
}

/** Liste des désignations de services (catalogue du champ « Service »). */
export function fetchServices() {
  return request('/services');
}

/**
 * Ajoute une désignation de service au catalogue (409 si déjà présente).
 * La nouvelle désignation devient disponible dans les futures listes.
 */
export function addService(name) {
  return request('/services', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
}

/**
 * Crée une fiche de diagnostic.
 * payload : { mode: 'manual'|'auto', motor: {...}, measurements: {...} }
 */
export function createTest(payload) {
  return request('/tests', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

/**
 * Met à jour partiellement une fiche (PATCH).
 * ex. archiveTest('T-0003') → { status: 'archived' }
 */
export function updateTest(testId, changes) {
  return request(`/tests/${encodeURIComponent(testId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(changes),
  });
}

/** Archive une fiche de diagnostic (traçabilité : pas de suppression). */
// É17 — VALIDER LE TEST HORS TENSION (§5.4) : draft → offline_validated
export function validateOffline(testId) {
  return request(`/tests/${encodeURIComponent(testId)}/validate-offline`, {
    method: 'POST',
  });
}

// É17 — VALIDER LE TEST SOUS TENSION (§6.1) : offline_validated → completed
export function validateOnline(testId) {
  return request(`/tests/${encodeURIComponent(testId)}/validate-online`, {
    method: 'POST',
  });
}

export function archiveTest(testId) {
  return updateTest(testId, { status: 'archived' });
}

/**
 * Démarre l'acquisition automatique d'un test (START).
 * kitId doit correspondre à un kit réellement en ligne (sinon 400).
 */
export function startAcquisition(testId, kitId) {
  return request(`/tests/${encodeURIComponent(testId)}/acquisition/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kit_id: kitId }),
  });
}

/** Arrête l'acquisition en cours (QUIT). */
export function stopAcquisition(testId) {
  return request(`/tests/${encodeURIComponent(testId)}/acquisition/stop`, {
    method: 'POST',
  });
}

/** Série temporelle d'un test (échantillons du kit). */
export function fetchSamples(testId) {
  return request(`/tests/${encodeURIComponent(testId)}/samples`);
}

/** Registre numérique des moteurs (20 colonnes du fichier Excel). */
export function fetchRegistre() {
  return request('/registre');
}

/**
 * Rapport de diagnostic d'un test : résultat des règles appliquées
 * (courant à vide, isolement, température…) calculé par le BACKEND.
 * L'interface n'applique aucune règle elle-même : elle affiche.
 */
export function fetchAnalysis(testId) {
  return request(`/tests/${encodeURIComponent(testId)}/analysis`);
}
