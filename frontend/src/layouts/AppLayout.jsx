// ============================================================
// GABARIT COMMUN — SANS MENU.
//
// Conformément au cahier des charges, la navigation ne passe pas
// par un menu : elle se fait par les boutons d'action de la page
// d'accueil (§6 et §7). L'en-tête ne contient que la marque OCP
// et un lien discret « Accueil » pour revenir au point de départ.
//
// Pour ajouter une page, ajouter une route dans App.jsx ; la page
// doit être atteignable par un bouton/lien du parcours (§6).
// ============================================================
import { Link, Outlet } from 'react-router-dom';

export default function AppLayout() {
  return (
    <div className="app-frame">
      {/* Liseré supérieur (vert OCP) */}
      <div className="brand-strip" aria-hidden="true" />

      {/* En-tête : marque seule, pas de menu */}
      <header className="topbar">
        <div className="topbar-inner">
          {/* Logo OCP : à gauche (lien discret vers l'accueil) */}
          <Link to="/" className="topbar-logo-link" title="Accueil">
            <img src="/brand/ocp-emblem.png" alt="Logo OCP" className="topbar-logo" />
          </Link>

          {/* Titre : centré entre le logo et l'icône Accueil (texte simple,
              sans lien : le retour à l'accueil se fait par le logo ou
              l'icône « Accueil ») */}
          <div className="topbar-title">
            <span className="topbar-brand-name">Diagnostic Moteurs</span>
            <span className="topbar-brand-sub">
              Atelier de maintenance · Kit de diagnostic 60 s
            </span>
          </div>

          <Link className="topbar-home" to="/" aria-label="Retour à l'accueil">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
              strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M3 10.5 12 3l9 7.5" />
              <path d="M5 9.5V21h14V9.5" />
              <path d="M9.5 21v-6h5v6" />
            </svg>
            <span>Accueil</span>
          </Link>
        </div>
      </header>

      {/* Contenu de la page active */}
      <div className="app-main">
        <main className="content">
          <Outlet />
        </main>

        <footer className="app-footer">
          OCP Motor Diagnostic — projet de fin d'études · développement progressif et
          modulaire · l'emblème OCP reste la propriété d'OCP Group (usage interne)
        </footer>
      </div>
    </div>
  );
}
