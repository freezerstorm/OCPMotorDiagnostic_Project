// ============================================================
// COMPOSANT « FIGURE DE MESURE » — un graphique Recharts + les
// valeurs clés (minimum / maximum / moyenne / durée) dessous.
//
// Utilisé TROIS FOIS par la page View Graph : température,
// courant, vibration. Composant purement VISUALISATION :
// aucun seuil, aucun diagnostic (voir Étape 10).
//
// Interactions (§12) : grille, curseur vertical au survol,
// infobulle « temps + valeur », points lisibles.
// ============================================================
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { computeFigureStats, formatDuration, formatValue } from '../utils/series';

// Couleurs du thème (voir :root dans styles.css — SVG n'accepte pas
// les variables CSS en attribut, on maintient les valeurs en phase).
const THEME = {
  axisText: '#5b6b60',   // texte secondaire
  grid: '#d8e3da',       // --c-border
  surface: '#ffffff',
};

/**
 * @param {number}  number  numéro de la figure (1, 2, 3)
 * @param {string}  title   grandeur affichée (ex. « Température »)
 * @param {string}  unit    unité (ex. « °C »)
 * @param {string}  yLabel  légende de l'axe vertical
 * @param {string}  dataKey colonne des points à tracer
 * @param {Array}   data    points {t, temperature_c, current_a, vibration_mm_s}
 * @param {string}  color   couleur de la courbe (charte OCP)
 * @param {string}  note    note optionnelle sous le titre (ex. hypothèse)
 */
export default function SampleFigure({ number, title, unit, yLabel, dataKey, data, color, note }) {
  const stats = computeFigureStats(data, dataKey);

  return (
    <section className="card figure-card">
      <div className="card-head">
        <h2>
          Figure {number} — {title}
          {note ? <span className="muted small"> · {note}</span> : null}
        </h2>
        <span className="badge badge-neutral">unité : {unit}</span>
      </div>

      <div className="chart-box" role="img" aria-label={`Graphique : ${title} en fonction du temps`}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 14, right: 26, bottom: 14, left: 4 }}>
            <CartesianGrid stroke={THEME.grid} strokeDasharray="3 3" />
            <XAxis
              dataKey="t"
              type="number"
              domain={['dataMin', 'dataMax']}
              tick={{ fill: THEME.axisText, fontSize: 12 }}
              stroke={THEME.grid}
              label={{ value: 'Temps (s)', position: 'insideBottom', offset: -8, fill: THEME.axisText, fontSize: 12 }}
            />
            <YAxis
              tick={{ fill: THEME.axisText, fontSize: 12 }}
              stroke={THEME.grid}
              width={58}
              label={{
                value: yLabel,
                angle: -90,
                position: 'insideLeft',
                offset: 12,
                style: { textAnchor: 'middle', fill: THEME.axisText, fontSize: 12 },
              }}
            />
            <Tooltip
              isAnimationActive={false}
              formatter={(value) => [`${formatValue(value, 3)} ${unit}`, title]}
              labelFormatter={(t) => `Temps : ${formatValue(t, 1)} s`}
            />
            {/* Pas d'animation inutile : la courbe s'affiche directement.
                dot={false} : la série peut compter ~120 points. */}
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Valeurs clés sous la figure (§12) */}
      <div className="stats-grid">
        <div className="stat-box"><span className="muted small">Minimum</span><strong>{formatValue(stats.min)}</strong></div>
        <div className="stat-box"><span className="muted small">Maximum</span><strong>{formatValue(stats.max)}</strong></div>
        <div className="stat-box"><span className="muted small">Moyenne</span><strong>{formatValue(stats.avg)}</strong></div>
        <div className="stat-box"><span className="muted small">Durée d'acquisition</span><strong>{formatDuration(stats.duration)}</strong></div>
      </div>
    </section>
  );
}
