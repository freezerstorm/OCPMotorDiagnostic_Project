import { useEffect, useState } from 'react';
import { SectionIntro, EmptyState } from '../components';
import { StatusPill } from '../components/StatusPill';
import { listAllTests } from '../services/tests';
import { MODE_LABELS } from '../services/apiClient';

export function HistoryPage({ navigate }) {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    listAllTests()
      .then(setTests)
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  const filtered = tests.filter((t) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      t.motor_label.toLowerCase().includes(q) ||
      (t.motor_serial || '').toLowerCase().includes(q) ||
      (t.motor_service || '').toLowerCase().includes(q)
    );
  });

  return (
    <>
      <SectionIntro
        eyebrow="HISTORIQUE"
        title="Diagnostics enregistrés"
        text="Chaque test est conservé indépendamment pour assurer la traçabilité (pas de suppression définitive). Filtres par service, période, mode et décision à venir (étape 6)."
      />
      <div className="table-card">
        <div className="table-toolbar">
          <input
            placeholder="Rechercher par ID, matricule, service…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button className="button secondary">Filtrer</button>
        </div>

        {loading ? (
          <EmptyState icon="◌" title="Chargement…" compact />
        ) : filtered.length === 0 ? (
          <EmptyState icon="▤" title="Aucun diagnostic" text="Les tests terminés apparaîtront dans ce tableau." compact />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th><th>Mode</th><th>Moteur</th><th>Matricule</th><th>Service</th><th>État</th><th>Décision</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t) => (
                  <tr key={t.id}>
                    <td>{new Date(t.created_at).toLocaleString('fr-FR')}</td>
                    <td><span className="badge">{MODE_LABELS[t.mode]}</span></td>
                    <td>{t.motor_label}</td>
                    <td>{t.motor_serial || '—'}</td>
                    <td>{t.motor_service || '—'}</td>
                    <td><StatusPill value={t.status} /></td>
                    <td><StatusPill kind="decision" value={t.technician_decision} /></td>
                    <td className="row-actions">
                      <button className="link" onClick={() => navigate('report', { testId: t.id })}>Consulter</button>
                      <button className="link" disabled>PDF</button>
                      <button className="link" disabled>Archiver</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
