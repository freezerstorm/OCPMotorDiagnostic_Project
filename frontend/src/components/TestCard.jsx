import { MODE_LABELS } from '../services/apiClient';
import { StatusPill } from './StatusPill';

// Petite carte affichée dans la section « Derniers tests » de la page d'accueil.
export function TestCard({ test, onOpen }) {
  return (
    <article className="test-card" onClick={() => onOpen && onOpen(test)}>
      <div className="test-card-icon">⚙</div>
      <div className="test-card-body">
        <div className="test-card-title">{test.motor_label}</div>
        {test.motor_serial && <div className="test-card-sub">Matricule {test.motor_serial}</div>}
        <div className="test-card-meta">
          <StatusPill kind="decision" value={test.technician_decision} />
          <span className="badge">{MODE_LABELS[test.mode]}</span>
          <span className="muted">{new Date(test.created_at).toLocaleString('fr-FR')}</span>
        </div>
      </div>
    </article>
  );
}
