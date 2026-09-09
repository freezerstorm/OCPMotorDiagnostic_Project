export function EmptyState({ icon = '▤', title, text, compact = false }) {
  return (
    <div className={`empty-state ${compact ? 'compact' : ''}`}>
      <span>{icon}</span>
      <strong>{title}</strong>
      {text && <p>{text}</p>}
    </div>
  );
}
