export function ActionCard({ icon, title, text, action, label }) {
  return (
    <article className="action-card">
      <span className="action-icon">{icon}</span>
      <div>
        <h3>{title}</h3>
        <p>{text}</p>
        <button className="button primary" onClick={action}>
          {label} <span>→</span>
        </button>
      </div>
    </article>
  );
}
