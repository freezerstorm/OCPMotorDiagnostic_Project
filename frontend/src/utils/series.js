// ============================================================
// UTILITAIRE — mise en forme de la série temporelle d'un test.
//
// L'API renvoie les échantillons du kit sous la forme :
//   [{ t_s, temperature_c, current_a,
//      vibration: { x_mm_s, y_mm_s, z_mm_s, global_mm_s } }, …]
//
// La page View Graph a besoin de :
//   1. lignes « à plat » pour Recharts (une colonne par figure) ;
//   2. les valeurs clés : minimum / maximum / moyenne / durée.
//
// AUCUNE logique de diagnostic ici : on ne fait que DES COMPTAGES
// (min/max/moyenne). Les seuils et conclusions vivent dans le
// moteur de règles côté backend (Étape 10) et la page Analyse.
// ============================================================

/**
 * Transforme les échantillons de l'API en lignes à plat pour
 * Recharts, triées par instant croissant.
 * @param {Array} samples échantillons renvoyés par GET /tests/{id}/samples
 * @returns {Array<{t:number, temperature_c:number|null, current_a:number|null, vibration_mm_s:number|null}>}
 */
export function buildSeriesPoints(samples) {
  return (samples ?? [])
    .map((s) => ({
      t: s.t_s,
      temperature_c: s.temperature_c ?? null,
      current_a: s.current_a ?? null,
      // Vibration retenue : la NORME des 3 axes (mm/s — le kit publie
      // la vitesse vibratoire directement).
      vibration_mm_s: s.vibration?.global_mm_s ?? null,
    }))
    .sort((a, b) => a.t - b.t);
}

/**
 * Valeurs clés d'une grandeur sur la série.
 * Les échantillons incomplets (valeur null) sont simplement ignorés.
 * @returns {{min:number|null, max:number|null, avg:number|null, duration:number|null}}
 *   duration = dernier instant − premier instant (secondes).
 */
export function computeFigureStats(points, key) {
  const values = points.map((p) => p[key]).filter((v) => v !== null && v !== undefined);
  const stats = { min: null, max: null, avg: null, duration: null };

  if (values.length > 0) {
    stats.min = Math.min(...values);
    stats.max = Math.max(...values);
    stats.avg = values.reduce((sum, v) => sum + v, 0) / values.length;
  }
  if (points.length >= 2) {
    stats.duration = points[points.length - 1].t - points[0].t;
  }
  return stats;
}

/** Nombre formaté « à la française » (ex. 27,91) ou « — » si absent.
 * Sans précision imposée : 2 décimales au-dessus de 1, 4 en dessous. */
export function formatValue(value, maxDigits) {
  if (value === null || value === undefined) return '—';
  const digits = maxDigits ?? (Math.abs(value) < 1 ? 4 : 2);
  return value.toLocaleString('fr-FR', { maximumFractionDigits: digits });
}

/** Durée en secondes, formatée (ex. « 11,5 s ») ou « — » si absente. */
export function formatDuration(seconds) {
  if (seconds === null || seconds === undefined) return '—';
  return `${seconds.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} s`;
}
