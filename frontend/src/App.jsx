import { useEffect, useState } from 'react';
import { AppLayout } from './layouts/AppLayout';
import {
  HomePage,
  KitConnectionPage,
  MotorFormPage,
  AcquisitionPage,
  GraphPage,
  AnalysisPage,
  ReportPage,
  HistoryPage,
} from './pages';
import {
  setPendingKitId,
  setPendingMode,
  setCurrentTestId,
} from './state/session';
import './styles.css';

const routes = {
  home:        { label: 'Accueil',        component: HomePage },
  kit:         { label: 'Connexion kit',  component: KitConnectionPage },
  motor:       { label: 'Fiche moteur',   component: MotorFormPage },
  acquisition: { label: 'Acquisition',    component: AcquisitionPage },
  graph:       { label: 'View graph',     component: GraphPage },
  analysis:    { label: 'Analysis',       component: AnalysisPage },
  report:      { label: 'Rapport',        component: ReportPage },
  history:     { label: 'Historique',     component: HistoryPage },
};

function getRoute() {
  const name = window.location.hash.replace('#/', '') || 'home';
  return routes[name] ? name : 'home';
}

export default function App() {
  const [route, setRoute] = useState(getRoute);
  const [backendState, setBackendState] = useState('checking');

  useEffect(() => {
    const onHashChange = () => setRoute(getRoute());
    window.addEventListener('hashchange', onHashChange);
    fetch('/api/v1/health')
      .then((r) => setBackendState(r.ok ? 'ok' : 'error'))
      .catch(() => setBackendState('error'));
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  // Fonction de navigation. Accepte un deuxième paramètre « params » qui
  // est stocké dans sessionStorage (mode du test, kit connecté, test courant).
  const navigate = (name, params = {}) => {
    if (params.mode) setPendingMode(params.mode);
    if ('kitId' in params) setPendingKitId(params.kitId);
    if ('testId' in params) setCurrentTestId(params.testId);
    window.location.hash = `/${name}`;
  };

  const Page = routes[route].component;

  return (
    <AppLayout activeRoute={route} navigate={navigate} backendState={backendState}>
      <Page navigate={navigate} />
    </AppLayout>
  );
}
