import { STATUS_LABELS, DECISION_LABELS } from '../services/apiClient';

export function StatusPill({ kind = 'status', value }) {
  const labels = kind === 'decision' ? DECISION_LABELS : STATUS_LABELS;
  const cls = value === 'return_to_service' || value === 'ok' || value === 'completed'
    ? 'ok'
    : value === 'sent_to_repair' || value === 'error'
    ? 'bad'
    : 'neutral';
  return <span className={`status-pill ${cls}`}>{labels[value] || value}</span>;
}
