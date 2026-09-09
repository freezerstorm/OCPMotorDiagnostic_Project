// Client HTTP minimal pour parler au backend FastAPI.
// Tous les appels API passent par ici : si l'URL ou le format change,
// on ne modifie QUE ce fichier.
const BASE = '/api/v1';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch (_) { /* réponse non-JSON */ }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get: (path) => request(path),
  post: (path, data) => request(path, { method: 'POST', body: JSON.stringify(data) }),
  patch: (path, data) => request(path, { method: 'PATCH', body: JSON.stringify(data) }),
};

// Petits helpers de statut (utilisés dans les étiquettes UI)
export const STATUS_LABELS = {
  idle: 'Créé',
  ready: 'Prêt',
  acquiring: 'Acquisition en cours',
  completed: 'Terminé — en attente d\'analyse',
  analyzed: 'Analysé',
  reported: 'Rapport généré',
  archived: 'Archivé',
  error: 'Erreur',
};

export const DECISION_LABELS = {
  pending: 'En attente',
  return_to_service: 'Remis en service',
  sent_to_repair: 'Envoyé en réparation',
};

export const MODE_LABELS = {
  manual: 'Manuel',
  auto: 'Automatique',
};
