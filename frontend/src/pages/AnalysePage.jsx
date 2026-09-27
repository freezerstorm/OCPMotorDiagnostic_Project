// ============================================================
// PAGE ANALYSE — Étape 11 : branchée sur le moteur de règles.
//
// Les résultats viennent du BACKEND (GET /tests/{id}/analysis) :
// l'interface n'applique AUCUNE règle elle-même — elle affiche la
// chaîne demandée pour chaque paramètre :
//   valeur mesurée → référence/seuil → résultat → interprétation →
//   risque éventuel → recommandation éventuelle
//
// La CONCLUSION GÉNÉRALE automatique est prévue pour plus tard
// (simple synthèse des règles affichée en attendant). La DÉCISION
// du technicien (remis en service / réparation) reste indépendante
// de l'analyse et inchangée (§14).
// ============================================================
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { DECISIONS, DECISION_LABELS, TEST_MODE_LABELS } from '../constants';
import { fetchAnalysis, fetchTest, updateTest } from '../services/api';
import { formatDateFr } from '../utils/format';

// Évaluation (code machine) → teinte du badge.
const EVALUATION_TONES = {
  conforme: 'ok',
  non_critique: 'ok',
  problematique: 'warn',
  critique: 'danger',
  non_evaluable: 'neutral',
};

function EvaluationBadge({ code, label }) {
  return (
    <span className={`badge badge-${EVALUATION_TONES[code] ?? 'neutral'}`}>
      <span className="badge-dot" aria-hidden="true" />
      {label ?? code}
    </span>
  );
}

// Libellés + formats des chiffres clés renvoyés par chaque règle
// (result.display) — déjà calculés côté règles, on ne réinvente rien.
const DISPLAY_LABELS = {
  rated_current_a: 'Courant nominal (In)',
  limit_min_a: 'Limite minimale',
  limit_max_a: 'Limite maximale',
  limit_c: 'Limite critique',
  test_voltage_v: 'Tension de test',
  rmin_text: 'Résistance minimale requise',
};
const DISPLAY_FORMATS = {
  rated_current_a: (v) => `${v.toLocaleString('fr-FR')} A`,
  limit_min_a: (v) => `${v.toLocaleString('fr-FR')} A`,
  limit_max_a: (v) => `${v.toLocaleString('fr-FR')} A`,
  limit_c: (v) => `${v.toLocaleString('fr-FR')} °C`,
  test_voltage_v: (v) => `${v} V`,
  rmin_text: (v) => v,
};

// ===== Carte d'UN paramètre analysé =====
function ParameterCard({ result }) {
  return (
    <section className="card">
      <div className="card-head">
        <h2>{result.label}</h2>
        <EvaluationBadge code={result.evaluation} label={result.evaluation_label} />
      </div>

      {result.evaluation === 'non_evaluable' ? (
        <div className="alert alert-warn">
          <strong>Règle non applicable</strong> — information manquante :
          <ul className="diag-ul">
            {(result.missing_info ?? []).map((m) => <li key={m}>{m}</li>)}
          </ul>
        </div>
      ) : (
        <>
          {/* Chiffres clés (In, limites, tension de test, Rmin, seuil…) */}
          {Object.keys(result.display ?? {}).length > 0 && (
            <div className="kit-info">
              {Object.entries(result.display)
                .filter(([key]) => DISPLAY_LABELS[key])
                .map(([key, value]) => (
                  <div className="kit-info-item" key={key}>
                    <span className="muted small">{DISPLAY_LABELS[key]}</span>
                    <strong>{DISPLAY_FORMATS[key](value)}</strong>
                  </div>
                ))}
            </div>
          )}

          <div className="diag-steps">
            <div className="diag-step">
              <span className="diag-step-label">Valeur mesurée</span>
              <strong className="diag-value">{result.measured_text}</strong>
              {result.measured_source && (
                <span className="muted small"> — {result.measured_source}</span>
              )}
            </div>
            {result.reference_text && (
              <div className="diag-step">
                <span className="diag-step-label">Référence / seuil appliqué</span>
                <span>{result.reference_text}</span>
              </div>
            )}
            <div className="diag-step">
              <span className="diag-step-label">Interprétation</span>
              <span>{result.interpretation ?? '—'}</span>
            </div>
            <div className="diag-step">
              <span className="diag-step-label">Risque éventuel</span>
              <DiagValues value={result.risk} />
            </div>
            <div className="diag-step">
              <span className="diag-step-label">Action / recommandation</span>
              <DiagValues value={result.recommendation} />
            </div>
            {(result.environment_hypotheses ?? []).length > 0 && (
              <>
                <div className="diag-step">
                  <span className="diag-step-label">
                    Causes possibles liées à l'environnement (hypothèses — non certitudes)
                  </span>
                  <ul className="diag-ul">
                    {result.environment_hypotheses.flatMap((h) => h.possible_causes).map((c) => <li key={c}>{c}</li>)}
                  </ul>
                </div>
                <div className="diag-step">
                  <span className="diag-step-label">Contrôles recommandés (contexte environnemental)</span>
                  <ul className="diag-ul">
                    {result.environment_hypotheses.flatMap((h) => h.recommendations).map((r) => <li key={r}>{r}</li>)}
                  </ul>
                </div>
              </>
            )}
          </div>
        </>
      )}

      {/* Détail des six mesures (paramètre « Isolement ») */}
      {result.items?.length > 0 && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr><th>Mesure</th><th>Valeur mesurée</th><th>Évaluation</th></tr>
            </thead>
            <tbody>
              {result.items.map((item) => (
                <tr key={item.key}>
                  <td>{item.label}</td>
                  <td>{item.value_text}</td>
                  <td><EvaluationBadge code={item.evaluation} label={item.evaluation_label} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

// ===== Vue principale : fiche + analyse des règles =====
function TestAnalysisView({ testId, justSaved }) {
  const [state, setState] = useState({ status: 'loading', test: null, analysis: null });

  const load = () => {
    setState({ status: 'loading', test: null, analysis: null });
    Promise.all([fetchTest(testId), fetchAnalysis(testId)])
      .then(([test, analysis]) => setState({ status: 'ok', test, analysis }))
      .catch(() => setState({ status: 'error', test: null, analysis: null }));
  };
  useEffect(load, [testId]);

  if (state.status === 'loading') return <p className="muted small">Chargement de l'analyse…</p>;

  if (state.status === 'error') {
    return (
      <section className="card">
        <div className="alert alert-error">
          Impossible de charger le test {testId} ou son analyse — le backend est
          peut-être injoignable.
        </div>
        <div className="actions-row">
          <button type="button" className="btn btn-primary" onClick={load}>Réessayer</button>
          <Link className="btn btn-ghost" to="/historique">Historique</Link>
        </div>
      </section>
    );
  }

  const { test, analysis } = state;
  const motor = test.motor ?? {};
  const m = test.measurements ?? {};
  const iso = m.insulation ?? {};
  const wind = m.winding ?? {};
  const vals = m.values ?? {};
  const summary = analysis.summary ?? {};
  const summaryText = [
    summary.conforme ? `${summary.conforme} conforme(s)` : null,
    summary.non_critique ? `${summary.non_critique} non critique(s)` : null,
    summary.problematique ? `${summary.problematique} problématique(s)` : null,
    summary.critique ? `${summary.critique} critique(s)` : null,
    summary.non_evaluable ? `${summary.non_evaluable} non évaluable(s)` : null,
  ].filter(Boolean).join(' · ');

  return (
    <>
      {justSaved && (
        <div className="alert alert-success">
          <strong>Test {test.test_id} enregistré avec succès</strong> — l'analyse
          par règles est affichée ci-dessous.
        </div>
      )}

      {/* ===== 1. Fiche du diagnostic ===== */}
      <section className="card">
        <div className="card-head">
          <h2>Fiche du diagnostic {test.test_id}</h2>
          <span className="badge badge-info">
            <span className="badge-dot" aria-hidden="true" />
            {TEST_MODE_LABELS[test.mode] ?? test.mode}
          </span>
        </div>

        <div className="kit-info">
          <div className="kit-info-item">
            <span className="muted small">Date</span>
            <strong>{formatDateFr(test.created_at)}</strong>
          </div>
          <div className="kit-info-item">
            <span className="muted small">Moteur</span>
            <strong>{motor.motor_id ?? '—'}</strong>
          </div>
          <div className="kit-info-item">
            <span className="muted small">Désignation</span>
            <strong>{motor.designation ?? '—'}</strong>
          </div>
          <div className="kit-info-item">
            <span className="muted small">Courant nominal (In)</span>
            <strong>{motor.rated_current_a != null ? `${motor.rated_current_a.toLocaleString('fr-FR')} A` : '—'}</strong>
          </div>
        </div>

        <h3 className="summary-h">Mesures enregistrées</h3>
        <div className="table-wrap">
          <table className="data-table">
            <tbody>
              {Object.entries({
                "Tension de test d'isolement": iso.test_voltage_v != null ? `${iso.test_voltage_v} V` : null,
                'Réf. appareil (isolement)': iso.ref_meter_insulation,
                'Isolement Ph1–Ph2 (MΩ)': iso.ph1_ph2_mohm,
                'Isolement Ph2–Ph3 (MΩ)': iso.ph2_ph3_mohm,
                'Isolement Ph3–Ph1 (MΩ)': iso.ph3_ph1_mohm,
                'Isolement Ph1–Masse (MΩ)': iso.ph1_ground_mohm,
                'Isolement Ph2–Masse (MΩ)': iso.ph2_ground_mohm,
                'Isolement Ph3–Masse (MΩ)': iso.ph3_ground_mohm,
                'Résistance R12 (Ω)': wind.r12_ohm,
                'Résistance R23 (Ω)': wind.r23_ohm,
                'Résistance R31 (Ω)': wind.r31_ohm,
                'Continuité des enroulements': wind.continuity_ok == null ? null : (wind.continuity_ok ? 'Oui' : 'Non'),
                'Réf. appareil (résistances)': wind.ref_meter_resistance,
                'Température palier côté accouplement (°C)': vals.temp_bearing_de_c,
                'Température palier C.O.A (°C)': vals.temp_bearing_nde_c,
                'Température unique — ancien format (°C)': vals.temperature_c,
                'Réf. appareil (température)': vals.ref_meter_temperature,
                'Courant à vide I0 (A)': vals.current_a,
                'Réf. appareil (tension/courant)': vals.ref_meter_cl,
                'Vibration (mm/s)': vals.vibration_mm_s,
              }).map(([label, value]) => (
                <tr key={label}>
                  <td>{label}</td>
                  <td>{value !== undefined && value !== null ? value : <span className="muted">non renseignée</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* É18 — zone administrative de la fiche papier (affichée si renseignée) */}
        {(() => {
          const admin = test.admin ?? {};
          const adminRows = {
            'Service demandeur': admin.requested_by_service,
            'AVIS': admin.notice,
            'ORDRE': admin.work_order,
            'Date de réception': admin.received_at ? formatDateFr(admin.received_at) : null,
            'Réparation interne': admin.repair_internal == null ? null : (admin.repair_internal ? 'Oui' : 'Non'),
            'Réparation externe': admin.repair_external == null ? null : (admin.repair_external ? 'Oui' : 'Non'),
          };
          const present = Object.entries(adminRows)
            .filter(([, value]) => value !== null && value !== undefined);
          if (present.length === 0) return null;
          return (
            <>
              <h3 className="summary-h">Zone administrative (fiche papier)</h3>
              <div className="table-wrap">
                <table className="data-table">
                  <tbody>
                    {present.map(([label, value]) => (
                      <tr key={label}>
                        <td>{label}</td>
                        <td>{value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          );
        })()}
      </section>

      {/* ===== 2. Analyse par paramètre (résultats du moteur) ===== */}
      <h2 className="summary-h">Analyse par paramètre</h2>
      {analysis.results.map((result) => (
        <ParameterCard key={result.parameter} result={result} />
      ))}

      {/* ===== B. Analyse environnementale (base de connaissances) ===== */}
      <h2 className="summary-h">Analyse environnementale</h2>
      <section className="card">
        {analysis.environment_analysis?.known ? (
          <>
            <div className="card-head">
              <h2>Environnement : {analysis.environment_analysis.environment}</h2>
              <span className="badge badge-info">
                <span className="badge-dot" aria-hidden="true" />Base de connaissances
              </span>
            </div>
            <div className="diag-steps">
              <div className="diag-step">
                <span className="diag-step-label">Principaux risques associés</span>
                <ul className="diag-ul">
                  {analysis.environment_analysis.constraints.map((c) => <li key={c}>{c}</li>)}
                </ul>
              </div>
              <div className="diag-step">
                <span className="diag-step-label">Paramètres particulièrement sensibles</span>
                <span>{analysis.environment_analysis.relevant_parameters.map((p) => p.label).join(' · ')}</span>
              </div>
            </div>
            {analysis.environment_analysis.triggered.length > 0 ? (
              <div className="alert alert-warn">
                <strong>Hypothèses de causes liées à l'environnement</strong> — anomalies
                détectées ; causes POSSIBLES à investiguer, non certitudes :
                <ul className="diag-ul">
                  {analysis.environment_analysis.triggered.map((t) => (
                    <li key={t.parameter}>{t.parameter_label} — {t.possible_causes.join(' ; ')}</li>
                  ))}
                </ul>
              </div>
            ) : (
              analysis.environment_analysis.watch_note && (
                <div className="alert alert-success">{analysis.environment_analysis.watch_note}</div>
              )
            )}
          </>
        ) : (
          <>
            <h2>Environnement non renseigné</h2>
            <p className="card-hint mb-0">{analysis.environment_analysis?.message ?? '—'}</p>
          </>
        )}
      </section>

      {/* ===== C. Conclusion générale (automatique, formulations prudentes) ===== */}
      <section className="card">
        <h2>Conclusion générale de l'analyse (automatique)</h2>
        <p className="card-hint">{summaryText || 'Aucune règle évaluable.'}</p>
        {(analysis.general_conclusion ?? []).map((paragraph, i) => (
          <div className="conclusion-box" key={i}>{paragraph}</div>
        ))}
      </section>

      {/* ===== 4. Décision du technicien (inchangée, indépendante) ===== */}
      <DecisionCard test={test} />
    </>
  );
}

// ===== Décision du technicien + observation =====
// DISTINCTE de l'analyse automatique (§14) : c'est le technicien qui
// décide. Le choix + l'observation sont ENREGISTRÉS dans la fiche via
// PATCH /tests/{id} ; ils apparaissent ensuite dans le rapport PDF.
function DecisionCard({ test }) {
  // État affiché (modifiable) — initialisé avec ce qui est déjà enregistré
  const [decision, setDecision] = useState(test.decision ?? null);
  const [observation, setObservation] = useState(test.observation ?? '');
  // Société en charge de la réparation (décision client 24/09/2026) :
  // saisie quand la décision est « Envoyé en réparation » ; elle
  // alimente la colonne « Société » de la ligne du registre.
  const [repairCompany, setRepairCompany] = useState('');
  // Ce qui est réellement SAUVEGARDÉ en base (pour l'indicateur)
  const [saved, setSaved] = useState({
    decision: test.decision ?? null,
    observation: test.observation ?? '',
    repair_company: '',
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null); // {type, text}

  const changed = decision !== saved.decision
    || observation !== saved.observation
    || repairCompany.trim() !== saved.repair_company;

  const handleSave = async () => {
    if (!decision) {
      setMessage({ type: 'error', text: 'Choisis d’abord une décision (remis en service ou envoyé en réparation).' });
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      const changes = { decision, observation };
      if (decision === DECISIONS.REPAIR && repairCompany.trim()) {
        changes.repair_company = repairCompany.trim();
      }
      const updated = await updateTest(test.test_id, changes);
      setSaved({
        decision: updated.decision,
        observation: updated.observation,
        repair_company: changes.repair_company ?? '',
      });
      setMessage({
        type: 'success',
        text: `Décision enregistrée : ${DECISION_LABELS[updated.decision] ?? updated.decision}. Elle apparaît dans le rapport.`,
      });
    } catch (error) {
      setMessage({ type: 'error', text: `Enregistrement impossible : ${error.message}` });
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="card">
      <h2>Décision du technicien</h2>
      {saved.decision && !changed && (
        <div className="alert alert-success">
          Décision enregistrée pour {test.test_id} :{' '}
          <strong>{DECISION_LABELS[saved.decision] ?? saved.decision}</strong>
        </div>
      )}

      <div className="decision-buttons">
        <button
          type="button"
          className={`btn ${decision === DECISIONS.SERVICED ? 'btn-ok-selected' : 'btn-outline'}`}
          onClick={() => setDecision(DECISIONS.SERVICED)}
        >
          ✓ Remis en service
        </button>
        <button
          type="button"
          className={`btn ${decision === DECISIONS.REPAIR ? 'btn-danger-selected' : 'btn-outline'}`}
          onClick={() => setDecision(DECISIONS.REPAIR)}
        >
          ✕ Envoyé en réparation
        </button>
      </div>

      {decision === DECISIONS.REPAIR && (
        <div className="form-section">
          <h3>Société de réparation</h3>
          <input
            type="text"
            maxLength="200"
            placeholder="Ex. : FAR"
            value={repairCompany}
            onChange={(e) => setRepairCompany(e.target.value)}
          />
        </div>
      )}

      <div className="form-section">
        <h3>Observation du technicien</h3>
        <textarea
          rows="4"
          placeholder="Ex. : bruit anormal côté accouplement, graisse d'aspect inhabituel…"
          value={observation}
          onChange={(e) => setObservation(e.target.value)}
        />
      </div>

      {message && (
        <div className={`alert alert-${message.type}`} role="status">{message.text}</div>
      )}

      <div className="actions-row">
        <Link className="btn btn-ghost" to="/">← Accueil</Link>
        <span className="flex-spacer" />
        <Link className="btn btn-outline" to="/historique">Historique</Link>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleSave}
          disabled={saving || !changed}
          title={changed ? 'Enregistrer la décision et l’observation dans la fiche' : 'Rien de nouveau à enregistrer'}
        >
          {saving ? 'Enregistrement…' : '💾 Enregistrer la décision'}
        </button>
        <Link className="btn btn-accent btn-lg" to={`/test/rapport?testId=${test.test_id}`}>
          Générer le rapport →
        </Link>
      </div>
    </section>
  );
}

// Risque / Action : texte simple (« Aucun risque ») OU liste de causes /
// actions fournie par les règles — rendue en puces dans ce cas.
function DiagValues({ value }) {
  if (Array.isArray(value)) {
    return (
      <ul className="diag-ul">
        {value.map((item) => <li key={item}>{item}</li>)}
      </ul>
    );
  }
  return <span>{value ?? '—'}</span>;
}

export default function AnalysePage() {
  const [searchParams] = useSearchParams();
  const testId = searchParams.get('testId');

  if (testId) {
    return (
      <>
        <h1 className="page-title">Analyse des résultats</h1>
        <TestAnalysisView testId={testId} justSaved={searchParams.get('justSaved') === '1'} />
      </>
    );
  }

  return (
    <>
      <h1 className="page-title">Analyse des résultats</h1>
      <section className="card">
        <h2>Aucun test sélectionné</h2>
        <div className="actions-row">
          <Link className="btn btn-ghost" to="/">← Accueil</Link>
          <Link className="btn btn-outline" to="/historique">Historique</Link>
          <Link className="btn btn-accent btn-lg" to="/">
            + Nouveau diagnostic
          </Link>
        </div>
      </section>
    </>
  );
}
