// ============================================================
// UTILITAIRES DE FORMATAGE (dates, etc.)
// ============================================================

/** Convertit une date ISO (ex. 2026-09-09T10:00:00Z) en date
 *  française courte (ex. 09/09/2026). Renvoie « — » si invalide. */
export function formatDateFr(iso) {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleDateString('fr-FR');
}
