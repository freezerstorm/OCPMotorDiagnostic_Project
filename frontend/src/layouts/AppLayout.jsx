const navItems = [
  ['home', '⌂', 'Accueil'], ['kit', '⌁', 'Connexion kit'], ['motor', '▣', 'Nouveau test'],
  ['history', '▤', 'Historique'],
];

export function AppLayout({ activeRoute, navigate, backendState, children }) {
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="sidebar-brand"><span className="brand-mark">O</span><div><strong>OCP</strong><small>Diagnostic moteurs</small></div></div>
      <div className="nav-caption">ESPACE DE TRAVAIL</div>
      <nav aria-label="Navigation principale">{navItems.map(([id, icon, label]) => <button key={id} className={activeRoute === id ? 'nav-item active' : 'nav-item'} onClick={() => navigate(id)}><span>{icon}</span>{label}</button>)}</nav>
      <div className="sidebar-footer"><span className={`mini-dot ${backendState}`} /> Backend {backendState === 'ok' ? 'opérationnel' : backendState === 'checking' ? 'vérification…' : 'indisponible'}</div>
    </aside>
    <div className="main-area">
      <header className="topbar"><div><span className="eyebrow">ATELIER DE MAINTENANCE</span><h1>{activeRoute === 'home' ? 'Tableau de bord' : ({ kit: 'Connexion au kit', motor: 'Nouveau diagnostic', acquisition: 'Acquisition', graph: 'Visualisation des mesures', analysis: 'Analyse', report: 'Rapport de diagnostic', history: 'Historique' }[activeRoute] || 'Diagnostic')}</h1></div><div className="topbar-meta"><span className="secure-badge">● Session locale</span><span className="avatar">TM</span></div></header>
      <main className="page-content">{children}</main>
      <footer className="footer">Kit de diagnostic moteurs · Version MVP · Les seuils d'analyse seront ajoutés progressivement</footer>
    </div>
  </div>;
}
