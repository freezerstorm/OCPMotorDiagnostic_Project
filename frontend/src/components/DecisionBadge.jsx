// ============================================================
// BADGE « Décision » — petit bloc réutilisable (accueil,
// historique…). Affiche la décision d'un test avec sa couleur :
//   serviced (remis en service) → vert
//   repair (envoyé en réparation) → ambre
// ============================================================
import { DECISIONS, DECISION_LABELS } from '../constants';

export default function DecisionBadge({ decision }) {
  const ok = decision === DECISIONS.SERVICED;
  const label = DECISION_LABELS[decision] ?? decision;

  return (
    <span className={`badge ${ok ? 'badge-ok' : 'badge-warn'}`}>
      <span className="badge-dot" aria-hidden="true" />
      {label}
    </span>
  );
}
