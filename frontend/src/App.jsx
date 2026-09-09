// Étape 1 : squelette de l'application.
// Cette page ne contient que l'en-tête et un contrôle de connexion au backend.
// La navigation entre les écrans arrive à l'Étape 2.
import { useEffect, useState } from 'react';

function App() {
  const [backendState, setBackendState] = useState('checking'); // checking | ok | error
  const [backendInfo, setBackendInfo] = useState(null);

  // Au démarrage, on interroge le backend via le proxy Vite (/api → port 8000).
  useEffect(() => {
    fetch('/api/v1/health')
      .then((response) => {
        if (!response.ok) throw new Error('Réponse non valide');
        return response.json();
      })
      .then((data) => {
        setBackendInfo(data);
        setBackendState('ok');
      })
      .catch(() => setBackendState('error'));
  }, []);

  return (
    <div className="page">
      {/* En-tête sobre aux couleurs inspirées de l'identité OCP */}
      <header className="app-header">
        <div className="app-header-inner">
          <div className="brand">
            <span className="brand-logo" aria-hidden="true" />
            <div>
              <h1>Diagnostic Moteurs</h1>
              <p className="brand-subtitle">Atelier de maintenance — Kit de diagnostic 60 s</p>
            </div>
          </div>
          <span className="version-badge">v0.1.0</span>
        </div>
      </header>

      <main className="content">
        <section className="card">
          <h2>État du système</h2>
          <p className="card-hint">
            Ce contrôle vérifie que le frontend (React) arrive à joindre le backend
            (FastAPI) au travers du serveur de développement.
          </p>

          <div className={`status-row status-${backendState}`}>
            <span className="status-dot" aria-hidden="true" />
            {backendState === 'checking' && <span>Connexion au backend en cours…</span>}
            {backendState === 'ok' && (
              <span>
                Backend connecté — <strong>{backendInfo?.application}</strong> (version{' '}
                {backendInfo?.version})
              </span>
            )}
            {backendState === 'error' && (
              <span>
                Backend injoignable — vérifie que le backend est lancé sur le port 8000.
              </span>
            )}
          </div>
        </section>

        <section className="card">
          <h2>Prochaines étapes</h2>
          <p className="card-hint">Le squelette du projet est en place. La suite arrive étape par étape :</p>
          <ol className="next-steps">
            <li>Étape 2 — Navigation entre les écrans de l'application</li>
            <li>Étape 3 — API de base (moteurs, tests)</li>
            <li>Étape 4 — Base de données PostgreSQL</li>
            <li>Étape 5 — Formulaire de diagnostic manuel</li>
          </ol>
        </section>
      </main>

      <footer className="app-footer">
        Application de diagnostic — projet de fin d'études · aucune donnée de test
        n'est affichée comme réelle
      </footer>
    </div>
  );
}

export default App;
