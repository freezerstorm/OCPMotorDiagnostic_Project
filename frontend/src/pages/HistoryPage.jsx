// ============================================================
// PAGE HISTORIQUE — alimentée par le VRAI backend (GET /api/v1/tests).
//
// Exigences (§17) :
//   - chaque test est un enregistrement indépendant (un même
//     moteur peut avoir plusieurs diagnostics) ;
//   - tableau type « Google Sheets » ;
//   - recherche par matricule (l'identifiant du moteur — UNE colonne) ;
//   - cohérence E4 : pas de lien Rapport direct, le rapport se
//     consulte depuis l'Analyse (bouton « Consulter ») ;
//   - filtres : service, période, mode, décision ;
//   - actions : consulter, ouvrir le rapport, archiver ;
//   - PAS de suppression définitive (traçabilité obligatoire).
//
// L'archivage est réel : PATCH /tests/{id} → status='archived'.
// Le filtrage s'effectue côté client ; il pourra être déplacé côté
// backend si l'historique grossit.
// ============================================================
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import DecisionBadge from '../components/DecisionBadge';
import {
  DECISIONS,
  DECISION_LABELS,
  SERVICE_OPTIONS,
  TEST_MODES,
  TEST_MODE_LABELS,
} from '../constants';
import { archiveTest, fetchTests } from '../services/api';
import { formatDateFr } from '../utils/format';

// Transformation d'une fiche API → ligne du tableau
function toRow(test) {
  const motor = test.motor ?? {};
  return {
    id: test.test_id,
    motorId: motor.motor_id,
    matricule: motor.matricule ?? '—',
    designation: motor.designation ?? '—',
    date: test.created_at,
    service: motor.service ?? '',
    mode: test.mode,
    decision: test.decision,
    status: test.status,
    archived: test.status === 'archived',
  };
}

export default function HistoryPage() {
  const [state, setState] = useState({ status: 'loading', rows: [] });
  const [archivingId, setArchivingId] = useState(null);
  const [message, setMessage] = useState(null); // { type, text }
  const [query, setQuery] = useState('');
  const [service, setService] = useState('');
  const [period, setPeriod] = useState('');
  const [mode, setMode] = useState('');
  const [decision, setDecision] = useState('');

  const loadTests = () => {
    setState({ status: 'loading', rows: [] });
    fetchTests(200)
      .then((tests) => setState({ status: 'ok', rows: tests.map(toRow) }))
      .catch(() => setState({ status: 'error', rows: [] }));
  };

  useEffect(() => {
    loadTests();
  }, []);

  // ===== Action : archiver (traçabilité — pas de suppression) =====
  const handleArchive = async (row) => {
    if (!window.confirm(
      `Archiver le test ${row.id} (${row.motorId}) ?\n\n` +
      'Un test archivé reste consultable dans l\'historique, mais il n\'apparaîtra plus dans « Derniers tests ».',
    )) return;

    setArchivingId(row.id);
    setMessage(null);
    try {
      await archiveTest(row.id);
      setMessage({ type: 'success', text: `Test ${row.id} archivé.` });
      loadTests();
    } catch (error) {
      setMessage({ type: 'error', text: `Impossible d'archiver : ${error.message}` });
    } finally {
      setArchivingId(null);
    }
  };

  // Filtrage local (recherche + filtres)
  const filtered = state.rows.filter((t) => {
    if (query) {
      const q = query.toLowerCase();
      if (!t.motorId.toLowerCase().includes(q) && !t.matricule.toLowerCase().includes(q)) {
        return false;
      }
    }
    if (service && t.service !== service) return false;
    if (mode && t.mode !== mode) return false;
    if (decision && t.decision !== decision) return false;
    if (period) {
      const days = { '7j': 7, '30j': 30, '90j': 90 }[period] ?? 0;
      const cutoff = new Date(Date.now() - days * 24 * 3600 * 1000);
      if (new Date(t.date) < cutoff) return false;
    }
    return true;
  });

  const resetFilters = () => {
    setQuery(''); setService(''); setPeriod(''); setMode(''); setDecision('');
  };

  return (
    <>
      <h1 className="page-title">Historique des diagnostics</h1>
      {message && (
        <div className={`alert alert-${message.type}`} role="status">
          {message.text}
        </div>
      )}

      {/* ===== Filtres ===== */}
      <section className="card">
        <div className="filters-grid">
          <div className="form-group">
            <label htmlFor="f_query">Recherche (matricule)</label>
            <input id="f_query" type="search" placeholder="Ex. : M-1042" value={query} onChange={(e) => setQuery(e.target.value)} />
          </div>
          <div className="form-group">
            <label htmlFor="f_service">Service</label>
            <select id="f_service" value={service} onChange={(e) => setService(e.target.value)}>
              <option value="">Tous</option>
              {SERVICE_OPTIONS.map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="f_period">Période</label>
            <select id="f_period" value={period} onChange={(e) => setPeriod(e.target.value)}>
              <option value="">Toutes</option>
              <option value="7j">7 derniers jours</option>
              <option value="30j">30 derniers jours</option>
              <option value="90j">90 derniers jours</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="f_mode">Mode</label>
            <select id="f_mode" value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="">Tous</option>
              <option value={TEST_MODES.MANUAL}>{TEST_MODE_LABELS[TEST_MODES.MANUAL]}</option>
              <option value={TEST_MODES.AUTO}>{TEST_MODE_LABELS[TEST_MODES.AUTO]}</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="f_decision">Décision</label>
            <select id="f_decision" value={decision} onChange={(e) => setDecision(e.target.value)}>
              <option value="">Toutes</option>
              <option value={DECISIONS.SERVICED}>{DECISION_LABELS[DECISIONS.SERVICED]}</option>
              <option value={DECISIONS.REPAIR}>{DECISION_LABELS[DECISIONS.REPAIR]}</option>
            </select>
          </div>
          <div className="form-group filter-actions">
            <span className="muted small">{filtered.length} résultat(s)</span>
            <button className="btn btn-ghost btn-sm" type="button" onClick={resetFilters}>Réinitialiser</button>
          </div>
        </div>
      </section>

      {/* ===== Tableau ===== */}
      <section className="card">
        {state.status === 'loading' && <p className="muted small">Chargement…</p>}

        {state.status === 'error' && (
          <p className="muted small">
            ⚠ Le backend est injoignable — lancez le backend (voir README) puis rechargez la
            page.
          </p>
        )}

        {state.status === 'ok' && (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Matricule</th>
                  <th>Désignation</th>
                  <th>Date</th>
                  <th>Service</th>
                  <th>Mode</th>
                  <th>Décision</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="muted">
                      {state.rows.length === 0
                        ? 'Aucun test enregistré pour le moment.'
                        : 'Aucun résultat pour ces filtres.'}
                    </td>
                  </tr>
                ) : (
                  filtered.map((t) => (
                    <tr key={t.id} className={t.archived ? 'row-archived' : ''}>
                      <td><strong>{t.matricule !== '—' ? t.matricule : t.motorId}</strong></td>
                      <td>{t.designation}</td>
                      <td>{formatDateFr(t.date)}</td>
                      <td>{t.service || '—'}</td>
                      <td>{TEST_MODE_LABELS[t.mode] ?? t.mode}</td>
                      <td>
                        {t.decision ? (
                          <DecisionBadge decision={t.decision} />
                        ) : (
                          <span className="badge badge-neutral">—</span>
                        )}
                      </td>
                      <td>
                        <div className="row-actions">
                          <Link className="btn btn-outline btn-sm" to={`/test/analyse?testId=${t.id}`}>Consulter</Link>
                          {t.archived ? (
                            <span className="badge badge-neutral">Archivé</span>
                          ) : (
                            <button
                              className="btn btn-ghost btn-sm"
                              type="button"
                              onClick={() => handleArchive(t)}
                              disabled={archivingId === t.id}
                              title="Archiver ce test (reste consultable)"
                            >
                              {archivingId === t.id ? '…' : 'Archiver'}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="actions-row">
        <Link className="btn btn-ghost" to="/">← Retour à l'accueil</Link>
      </div>
    </>
  );
}
