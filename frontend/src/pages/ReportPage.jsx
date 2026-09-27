// ============================================================
// PAGE RAPPORT — Étape 12 : aperçu RÉEL + téléchargement PDF.
//
// Le rapport reprend les 10 rubriques du §16, avec les vraies
// données du test (fiche + résultats du moteur de règles). Le
// fichier PDF est généré par le BACKEND :
//   GET /api/v1/tests/{id}/report.pdf
// L'aperçu ci-dessous reflète le contenu du PDF ; le bouton
// télécharge le fichier (même fiche pour les 2 modes).
//
// Rien d'inventé : risques / recommandations / conclusion
// automatique n'affichent que ce que les règles fournissent.
// ============================================================
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { DECISION_LABELS, TEST_MODE_LABELS } from '../constants';
import { fetchAnalysis, fetchTest } from '../services/api';
import { formatDateFr } from '../utils/format';


function valueOrDash(value, suffix = '') {
  if (value === undefined || value === null || value === '') return '—';
  return `${value}${suffix}`;
}

function Section({ number, title, children }) {
  return (
    <div className="report-section">
      <div className="report-section-title">{number}. {title}</div>
      {children}
    </div>
  );
}

function Line({ children }) {
  return <div className="report-line">{children}</div>;
}

// Aperçu réel du rapport (les mêmes informations que le PDF).
function ReportPreview({ test, analysis }) {
  const motor = test.motor ?? {};
  const m = test.measurements ?? {};
  const iso = m.insulation ?? {};
  const wind = m.winding ?? {};
  const vals = m.values ?? {};
  const byParam = Object.fromEntries(analysis.results.map((r) => [r.parameter, r]));
  const summary = analysis.summary ?? {};

  // Les règles renvoient soit un texte (« Aucun risque »), soit une
  // liste de causes / actions (connaissances client par paramètre).
  const flat = (v) => v.flatMap((t) => (Array.isArray(t) ? t : [t]));
  const risks = flat(analysis.results.map((r) => r.risk).filter(Boolean));
  const realRisks = risks.filter((t) => t !== 'Aucun risque');
  const recommendations = flat(analysis.results.map((r) => r.recommendation).filter(Boolean));
  // Paramètre normal → « Aucune action recommandée » : ne figure pas
  // dans la liste des actions du rapport (comme « Aucun risque » en 5).
  const realRecommendations = recommendations.filter((t) => t !== 'Aucune action recommandée');

  const synthesisParts = [
    summary.conforme ? `${summary.conforme} conforme(s)` : null,
    summary.non_critique ? `${summary.non_critique} non critique(s)` : null,
    summary.problematique ? `${summary.problematique} PROBLÉMATIQUE(S)` : null,
    summary.critique ? `${summary.critique} CRITIQUE(S)` : null,
    summary.non_evaluable ? `${summary.non_evaluable} non évaluable(s)` : null,
  ].filter(Boolean);

  return (
    <section className="card report-preview">
      <div className="report-masthead">
        <div>
          <div className="brand-logo" aria-hidden="true" />
          <span className="report-title">FICHE DE DIAGNOSTIC MOTEUR</span>
        </div>
        <div className="small muted" style={{ textAlign: 'right' }}>
          <div>Mode : {TEST_MODE_LABELS[test.mode] ?? test.mode}</div>
          <div>Test : {test.test_id}</div>
        </div>
      </div>

      <div className="report-grid">
        <Section number={1} title="Identification du moteur">
          <Line>{motor.matricule ?? motor.motor_id ?? '—'}{motor.designation ? ` — ${motor.designation}` : ''}</Line>
          <Line>Marque/Modèle : {valueOrDash(motor.brand)} / {valueOrDash(motor.model)} · N° : {valueOrDash(motor.serial_number)}</Line>
          <Line>{valueOrDash(motor.rated_power_kw, ' kW')} · {valueOrDash(motor.rated_voltage_v, ' V')} · In = {valueOrDash(motor.rated_current_a, ' A')} · {valueOrDash(motor.rated_speed_rpm, ' tr/min')}</Line>
          <Line>Couplage : {valueOrDash(motor.coupling)} · Service : {valueOrDash(motor.service)} · DI/OT : {valueOrDash(motor.di_ot)}</Line>
        </Section>

        <Section number={2} title="Données de référence (seuils appliqués)">
          <Line>Courant à vide : plage attendue 1/3 In – 2/3 In
            {byParam.current_no_load?.evaluation !== 'non_evaluable' && byParam.current_no_load
              ? ` = ${byParam.current_no_load.display.limit_min_a} – ${byParam.current_no_load.display.limit_max_a} A`
              : ' (In non renseignée)'}
          </Line>
          <Line>Isolement : {byParam.insulation?.evaluation !== 'non_evaluable' ? byParam.insulation.reference_text : 'Rmin = 1 kΩ × Vtest (tension non renseignée)'}</Line>
          <Line>Température : limite critique 85 °C</Line>
          <Line>Résistances d'enroulements : les trois valeurs doivent être identiques (R12 = R23 = R31)</Line>
          <Line>Vibration : seuil à définir (non fourni)</Line>
        </Section>

        <Section number={3} title="Données de mesure">
          <Line>Tension de test d'isolement : {valueOrDash(iso.test_voltage_v, ' V')}</Line>
          <Line>Isolement Ph–Ph : {valueOrDash(iso.ph1_ph2_mohm, ' MΩ')} · {valueOrDash(iso.ph2_ph3_mohm, ' MΩ')} · {valueOrDash(iso.ph3_ph1_mohm, ' MΩ')}</Line>
          <Line>Isolement Ph–Masse : {valueOrDash(iso.ph1_ground_mohm, ' MΩ')} · {valueOrDash(iso.ph2_ground_mohm, ' MΩ')} · {valueOrDash(iso.ph3_ground_mohm, ' MΩ')}</Line>
          <Line>Résistances : {valueOrDash(wind.r12_ohm, ' Ω')} · {valueOrDash(wind.r23_ohm, ' Ω')} · {valueOrDash(wind.r31_ohm, ' Ω')}</Line>
          <Line>Tension d'alimentation : {valueOrDash(vals.supply_voltage_v, ' V')}</Line>
          <Line>Température : {valueOrDash(vals.temperature_c, ' °C')} · Courant : {valueOrDash(vals.current_a, ' A')} · Vibration : {valueOrDash(vals.vibration_mm_s, ' mm/s')}</Line>
        </Section>

        <Section number={4} title="Résultats d'analyse (règles appliquées)">
          {analysis.results.map((r) => (
            <Line key={r.parameter}>
              <strong>{r.label}</strong> :{' '}
              {r.evaluation === 'non_evaluable'
                ? `NON ÉVALUABLE (${(r.missing_info ?? []).join('; ') || 'information manquante'})`
                : `${r.evaluation_label} — ${r.measured_text}`}
            </Line>
          ))}
        </Section>

        <Section number={5} title="Risques potentiels">
          {realRisks.length ? (
            <ul className="report-ul">
              {realRisks.map((t) => <li key={t}>{t}</li>)}
            </ul>
          ) : (
            <Line>— Aucun risque fourni par les règles à ce jour.</Line>
          )}
        </Section>

        <Section number={6} title="Mesures préventives / recommandations">
          {realRecommendations.length ? (
            <ul className="report-ul">
              {recommendations.map((t) => <li key={t}>{t}</li>)}
            </ul>
          ) : (
            <Line>— Aucune recommandation fournie par les règles à ce jour.</Line>
          )}
        </Section>

        <Section number={7} title="Observation du technicien">
          <Line>{valueOrDash(test.observation)}</Line>
        </Section>

        <Section number={8} title="Conclusion automatique de l'application">
          <Line>Synthèse des règles : {synthesisParts.length ? synthesisParts.join(' ; ') : 'aucune règle évaluable.'}</Line>
          <Line><span className="muted small">La conclusion générale automatisée sera définie ultérieurement ; la décision finale reste celle du technicien.</span></Line>
        </Section>

        <Section number={9} title="Décision finale du technicien">
          <div className="decision-line">
            {test.decision ? DECISION_LABELS[test.decision] ?? test.decision : 'Non enregistrée à ce jour.'}
          </div>
        </Section>

        <Section number={10} title="Informations de traçabilité">
          <Line>ID du test : <strong>{test.test_id}</strong> · Mode : {TEST_MODE_LABELS[test.mode] ?? test.mode}</Line>
          <Line>Enregistré le : {formatDateFr(test.created_at)} · Statut : {test.status}</Line>
          <Line><span className="muted small">Fiche générée automatiquement à partir des données enregistrées.</span></Line>
        </Section>
      </div>
    </section>
  );
}

// ===== PDF RÉEL : affiché dans la page + téléchargement =====
//
// Le PDF est généré par le backend (GET /tests/{id}/report.pdf). Il est
// récupéré en « blob » puis :
//   - AFFICHÉ dans la page (lecteur intégré) : fonctionne même dans les
//     fenêtres d'aperçu qui bloquent les téléchargements de fichiers ;
//   - TÉLÉCHARGÉ par un clic programmatique (attribut « download ») ;
//   - OUVRABLE dans un onglet séparé (lien direct).
// Dans un déploiement normal (Docker sur le poste de l'atelier), le
// bouton « Télécharger » enregistre directement le fichier.
function PdfDownload({ testId }) {
  const [state, setState] = useState({ status: 'loading', url: null, error: null });

  const loadPdf = () => {
    setState({ status: 'loading', url: null, error: null });
    fetch(`/api/v1/tests/${encodeURIComponent(testId)}/report.pdf`)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.blob();
      })
      .then((blob) => {
        setState({ status: 'ok', url: URL.createObjectURL(blob), error: null });
      })
      .catch((error) => setState({ status: 'error', url: null, error }));
  };
  useEffect(loadPdf, [testId]);

  const handleDownload = () => {
    if (!state.url) return;
    const link = document.createElement('a');
    link.href = state.url;
    link.download = `fiche-essai-${testId}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <section className="card">
      <div className="card-head">
        <h2>Fiche d'essai PDF (générée par le backend)</h2>
        <div className="actions-row">
          <button
            type="button"
            className="btn btn-outline"
            onClick={loadPdf}
            disabled={state.status === 'loading'}
          >
            {state.status === 'loading' ? 'Préparation…' : '↺ Régénérer'}
          </button>
          <a
            className="btn btn-ghost"
            href={`/api/v1/tests/${encodeURIComponent(testId)}/report.pdf`}
            target="_blank"
            rel="noreferrer"
          >
            Ouvrir dans un onglet
          </a>
          <button
            type="button"
            className="btn btn-primary btn-lg"
            onClick={handleDownload}
            disabled={state.status !== 'ok'}
          >
            ⬇ Télécharger le PDF
          </button>
        </div>
      </div>
      {state.status === 'error' && (
        <div className="alert alert-error">
          Impossible de récupérer le PDF ({String(state.error)}). Vérifie que le backend
          est lancé, puis clique sur « ↺ Régénérer ».
        </div>
      )}

      {state.url && (
        <iframe
          src={state.url}
          title={`Fiche d'essai PDF ${testId}`}
          style={{ width: '100%', height: '80vh', border: '1px solid var(--c-border)', borderRadius: 8 }}
        />
      )}
    </section>
  );
}

// Vue principale : aperçu + bouton de téléchargement du PDF backend.
function TestReportView({ testId }) {
  const [state, setState] = useState({ status: 'loading', test: null, analysis: null });

  const load = () => {
    setState({ status: 'loading', test: null, analysis: null });
    Promise.all([fetchTest(testId), fetchAnalysis(testId)])
      .then(([test, analysis]) => setState({ status: 'ok', test, analysis }))
      .catch(() => setState({ status: 'error', test: null, analysis: null }));
  };
  useEffect(load, [testId]);

  if (state.status === 'loading') return <p className="muted small">Préparation du rapport…</p>;

  if (state.status === 'error') {
    return (
      <section className="card">
        <div className="alert alert-error">
          Impossible de charger le test {testId} — le backend est peut-être injoignable.
        </div>
        <div className="actions-row">
          <button type="button" className="btn btn-primary" onClick={load}>Réessayer</button>
          <Link className="btn btn-ghost" to="/historique">Historique</Link>
        </div>
      </section>
    );
  }

  const { test, analysis } = state;

  return (
    <>
      <ReportPreview test={test} analysis={analysis} />

      <PdfDownload testId={test.test_id} />

      <div className="actions-row">
        <Link className="btn btn-ghost" to={`/test/analyse?testId=${test.test_id}`}>← Analyse</Link>
        <span className="flex-spacer" />
        <Link className="btn btn-outline" to="/historique">Historique</Link>
      </div>
    </>
  );
}

export default function ReportPage() {
  const [searchParams] = useSearchParams();
  const testId = searchParams.get('testId');

  return (
    <>
      <h1 className="page-title">Rapport de diagnostic</h1>
      {testId ? (
        <TestReportView testId={testId} />
      ) : (
        <section className="card">
          <h2>Aucun test sélectionné</h2>
          <div className="actions-row">
            <Link className="btn btn-ghost" to="/">← Accueil</Link>
            <Link className="btn btn-outline" to="/historique">Historique</Link>
          </div>
        </section>
      )}
    </>
  );
}
