// ============================================================
// PAGE VIEW GRAPH — Étape 9 : les TROIS FIGURES réelles (Recharts).
//
//   Figure 1 — Température (°C)
//   Figure 2 — Courant (A)
//   Figure 3 — Vibration (g, norme des 3 axes)
//
// Chaque figure : courbe temps ↔ grandeur, grille, curseur de
// survol, infobulle « temps + valeur », puis minimum / maximum /
// moyenne / durée sous la figure.
//
// SOURCES : GET /tests/{id} (fiche) et GET /tests/{id}/samples
// (série). PENDANT l'acquisition, la page se rafraîchit toute
// seule toutes les 2 s (statut « acquiring ») : on voit les
// points arriver en direct. APRÈS, elle affiche la série finale.
//
// RAPPEL : page réservée à la VISUALISATION — aucun seuil, aucune
// conclusion ici (c'est le rôle du moteur de règles + Analyse).
// ============================================================
import { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { fetchSamples, fetchTest } from '../services/api';
import SampleFigure from '../components/SampleFigure';
import { buildSeriesPoints } from '../utils/series';
import { TEST_MODE_LABELS, TEST_STATUS_LABELS, TEST_STATUSES } from '../constants';

// Pendant l'acquisition : rafraîchissement des données (2 s ≈
// la fréquence des échantillons, sans surcharger l'API).
const REFRESH_MS = 2000;

// Couleurs des courbes — charte OCP (voir :root de styles.css ;
// valeurs répétées ici car SVG n'accepte pas les variables CSS).
const CHART_COLORS = {
  temperature: '#1f6a30', // vert foncé
  current: '#77b731',     // vert clair OCP
  vibration: '#2b843d',   // vert OCP principal
};

// Les trois figures (§12) — la description, le rendu est dans SampleFigure.
const FIGURES = [
  { number: 1, dataKey: 'temperature_c', title: 'Température', unit: '°C',
    yLabel: 'Température (°C)', color: CHART_COLORS.temperature, note: null },
  { number: 2, dataKey: 'current_a', title: 'Courant', unit: 'A',
    yLabel: 'Courant (A)', color: CHART_COLORS.current, note: null },
  { number: 3, dataKey: 'vibration_mm_s', title: 'Vibration', unit: 'mm/s',
    yLabel: 'Vibration (mm/s)', color: CHART_COLORS.vibration,
    note: null },
];

// Badge de statut du test (couleur selon l'état).
function statusBadgeClass(status) {
  if (status === TEST_STATUSES.COMPLETED) return 'badge badge-ok';
  if (status === TEST_STATUSES.ERROR) return 'badge badge-warn';
  return 'badge badge-neutral';
}

// En-tête : rappel du test visualisé (identifiant, moteur, date, statut).
function TestHeader({ test, sampleCount, live }) {
  return (
    <section className="card">
      <div className="card-head">
        <h2>
          {test.test_id} · {test.motor?.motor_id}
          {test.motor?.designation ? <span className="muted small"> — {test.motor.designation}</span> : null}
        </h2>
        <span className={statusBadgeClass(test.status)}>
          <span className="badge-dot" aria-hidden="true" />
          {TEST_STATUS_LABELS[test.status] ?? test.status}
        </span>
      </div>
      <p className="card-hint">
        {TEST_MODE_LABELS[test.mode] ?? test.mode} ·{' '}
        {new Date(test.created_at).toLocaleString('fr-FR')} · {sampleCount} échantillon{sampleCount > 1 ? 's' : ''}
      </p>
    </section>
  );
}

// Carte d'état « rien à afficher » (pas de test sélectionné, 404,
// erreur réseau, test sans échantillon).
function EmptyCard({ title, children }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      <div className="actions-row">{children}</div>
    </section>
  );
}

export default function ViewGraphPage() {
  const [searchParams] = useSearchParams();
  const testId = searchParams.get('testId');

  // phase : noTestId | loading | ready | notFound | error
  const [phase, setPhase] = useState(testId ? 'loading' : 'noTestId');
  const [test, setTest] = useState(null);
  const [points, setPoints] = useState([]);

  const load = useCallback(async ({ silent = false } = {}) => {
    try {
      if (!silent) setPhase('loading');
      const [testData, samplesData] = await Promise.all([
        fetchTest(testId),
        fetchSamples(testId),
      ]);
      setTest(testData);
      setPoints(buildSeriesPoints(samplesData.samples));
      setPhase('ready');
    } catch (err) {
      setPhase(err?.status === 404 ? 'notFound' : 'error');
    }
  }, [testId]);

  // (Re)chargement au changement de test.
  useEffect(() => {
    if (testId) load();
  }, [testId, load]);

  // Pendant l'acquisition : rafraîchissement automatique toutes les 2 s.
  useEffect(() => {
    if (phase !== 'ready' || test?.status !== TEST_STATUSES.ACQUIRING) return undefined;
    const timer = setInterval(() => load({ silent: true }), REFRESH_MS);
    return () => clearInterval(timer);
  }, [phase, test?.status, load]);

  if (phase === 'noTestId') {
    return (
      <>
        <h1 className="page-title">Visualisation des mesures</h1>
        <EmptyCard title="Aucun test sélectionné">
          <Link className="btn btn-ghost" to="/historique">Historique</Link>
          <Link className="btn btn-primary" to="/">← Accueil</Link>
        </EmptyCard>
      </>
    );
  }

  if (phase === 'loading') {
    return (
      <>
        <h1 className="page-title">Visualisation des mesures</h1>
        <section className="card"><p className="card-hint">Chargement des mesures…</p></section>
      </>
    );
  }

  if (phase === 'notFound') {
    return (
      <>
        <h1 className="page-title">Visualisation des mesures</h1>
        <EmptyCard title="Test introuvable">
          <Link className="btn btn-primary" to="/">← Accueil</Link>
        </EmptyCard>
      </>
    );
  }

  if (phase === 'error') {
    return (
      <>
        <h1 className="page-title">Visualisation des mesures</h1>
        <EmptyCard title="Impossible de charger les mesures">
          <button type="button" className="btn btn-primary" onClick={() => load()}>Réessayer</button>
          <Link className="btn btn-ghost" to="/">← Accueil</Link>
        </EmptyCard>
      </>
    );
  }

  const live = test.status === TEST_STATUSES.ACQUIRING;

  return (
    <>
      <h1 className="page-title">Visualisation des mesures</h1>
      <TestHeader test={test} sampleCount={points.length} live={live} />

      {points.length === 0 ? (
        <EmptyCard
          title="Aucun échantillon pour l'instant"
          hint={live
            ? "L'acquisition vient de démarrer : les premiers points vont apparaître ici automatiquement."
            : "Ce test n'a reçu aucune mesure du kit — les graphiques seront disponibles après une acquisition."}
        >
          {live
            ? <Link className="btn btn-primary" to={`/test/automatique/acquisition?testId=${test.test_id}`}>← Retour à l'acquisition</Link>
            : <Link className="btn btn-primary" to="/">← Accueil</Link>}
        </EmptyCard>
      ) : (
        FIGURES.map((figure) => (
          <SampleFigure key={figure.dataKey} {...figure} data={points} />
        ))
      )}

      <section className="card">
        <div className="actions-row">
          <span className="flex-spacer" />
          <Link className="btn btn-ghost" to={`/test/automatique/acquisition?testId=${test.test_id}`}>
            ← Acquisition
          </Link>
          <Link className="btn btn-accent btn-lg" to={`/test/analyse?testId=${test.test_id}`}>
            Analyser les résultats →
          </Link>
        </div>
      </section>
    </>
  );
}
