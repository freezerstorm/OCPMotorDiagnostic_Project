export function SectionIntro({ eyebrow, title, text }) {
  return (
    <div className="section-intro">
      {eyebrow && <span className="eyebrow accent">{eyebrow}</span>}
      <h2>{title}</h2>
      {text && <p>{text}</p>}
    </div>
  );
}

export function SectionTitle({ title, action, onAction }) {
  return (
    <div className="section-title">
      <h2>{title}</h2>
      {action && <button onClick={onAction}>{action} →</button>}
    </div>
  );
}
