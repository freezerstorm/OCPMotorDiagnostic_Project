// ============================================================
// PAGE REGISTRE NUMÉRIQUE DES MOTEURS
//
// Tableau reprenant EXACTEMENT les colonnes du fichier réel du
// client, dans le même ordre (intitulés et unités conservés) :
//   - les 14 colonnes du premier export (JSON « p1 ») ;
//   - 3 colonnes du lot 4 (format 4) : Couplage, Isolement ph-m
//     (distinct de « Isolement » = phase-phase) et R — décision
//     client : les trois colonnes sont AFFICHÉES ; Couplage rempli
//     quand la ligne en a un, vide sinon.
//
// Le registre réunit :
//   - les lignes du registre réel importées (fichier client) ;
//   - les essais réalisés dans l'application (ajoutés automatiquement
//     après la décision du technicien).
//
// Une ligne par essai : les entrées ne sont jamais remplacées ni
// supprimées. Les valeurs sont BRUTES (« 525V », « 1,2 GΩ ») et les
// champs absents restent VIDES (rien d'inventé). Les données viennent
// du BACKEND (GET /api/v1/registre) — la page ne fait qu'afficher.
// ============================================================
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchRegistre } from '../services/api';

// Colonnes du registre réel — intitulés et ordre du fichier client
// (14 colonnes d'origine + Couplage + Isolement ph-m + R, lot 4).
const REGISTRE_COLUMNS = [
  { label: 'Date', key: 'entry_date', type: 'date' },
  { label: 'Matricule', key: 'matricule' },
  { label: 'DI/OT', key: 'di_ot' },
  { label: 'Couplage', key: 'couplage' },
  { label: 'Service (Sce)', key: 'service' },
  { label: 'Un', key: 'un_v' },
  { label: 'In', key: 'in_a' },
  { label: 'U0', key: 'uo_v' },
  { label: 'I0', key: 'io_a' },
  { label: 'Isolement', key: 'isolement' },
  { label: 'Isolement ph-m', key: 'isolement_ph_m' },
  { label: 'R', key: 'r' },
  { label: 'Nature', key: 'nature' },
  { label: 'Puissance (P)', key: 'puissance' },
  { label: 'Société', key: 'societe' },
  { label: 'BT/MT (Tension)', key: 'bt_mt' },
  { label: 'Observation', key: 'observation' },
];

/** Date ISO (AAAA-MM-JJ) → JJ/MM/AAAA — vide si absente. */
function formatDate(iso) {
  if (!iso) return '';
  const [y, m, d] = String(iso).slice(0, 10).split('-');
  return d ? `${d}/${m}/${y}` : iso;
}

/** Valeur d'une cellule (texte brut ; vide si le champ est absent). */
function cellValue(entry, column) {
  const value = entry[column.key];
  if (value === null || value === undefined || value === '') return '';
  if (column.type === 'date') return formatDate(value);
  return String(value);
}

export default function RegistryPage() {
  // phase : loading | ready | error
  const [phase, setPhase] = useState('loading');
  const [entries, setEntries] = useState([]);

  const load = async () => {
    setPhase('loading');
    try {
      const data = await fetchRegistre();
      setEntries(data.entries ?? []);
      setPhase('ready');
    } catch {
      setPhase('error');
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <>
      <h1 className="page-title">Registre des moteurs</h1>

      {phase === 'loading' && (
        <section className="card"><p>Chargement du registre…</p></section>
      )}

      {phase === 'error' && (
        <section className="card">
          <div className="alert alert-error" role="status">
            Registre indisponible : vérifiez la connexion au serveur.
          </div>
          <div className="actions-row">
            <button type="button" className="btn btn-ghost" onClick={load}>Réessayer</button>
            <Link className="btn btn-primary" to="/">← Formulaire moteur</Link>
          </div>
        </section>
      )}

      {phase === 'ready' && (
        <section className="card">
          <div className="card-head">
            <h2>Registre numérique</h2>
            <span className="badge badge-neutral">
              <span className="badge-dot" aria-hidden="true" />
              {entries.length} entrée{entries.length > 1 ? 's' : ''}
            </span>
          </div>

          {entries.length === 0 ? (
            <p>Aucune entrée.</p>
          ) : (
            <div className="table-scroll">
              <table className="data-table registre-table">
                <thead>
                  <tr>
                    {REGISTRE_COLUMNS.map((column) => (
                      <th key={column.key}>{column.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry, index) => (
                    // Liste jamais réordonnée : l'index est une clé stable.
                    <tr key={`${index}-${entry.matricule ?? ''}`}>
                      {REGISTRE_COLUMNS.map((column) => (
                        <td key={column.key}>{cellValue(entry, column)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {phase === 'ready' && (
        <div className="actions-row">
          <Link className="btn btn-primary" to="/">← Formulaire moteur</Link>
          <Link className="btn btn-ghost" to="/historique">Historique des diagnostics</Link>
        </div>
      )}
    </>
  );
}
