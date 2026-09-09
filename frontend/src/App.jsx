import { useEffect, useState } from 'react';
import { AppLayout } from './layouts/AppLayout';
import { HomePage } from './pages/HomePage';
import { KitConnectionPage } from './pages/KitConnectionPage';
import { MotorFormPage } from './pages/MotorFormPage';
import { AcquisitionPage } from './pages/AcquisitionPage';
import { GraphPage } from './pages/GraphPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { ReportPage } from './pages/ReportPage';
import { HistoryPage } from './pages/HistoryPage';
import './styles.css';

const routes = {
  home: { label: 'Accueil', component: HomePage },
  kit: { label: 'Connexion au kit', component: KitConnectionPage },
  motor: { label: 'Fiche moteur', component: MotorFormPage },
  acquisition: { label: 'Acquisition', component: AcquisitionPage },
  graph: { label: 'View graph', component: GraphPage },
  analysis: { label: 'Analysis', component: AnalysisPage },
  report: { label: 'Rapport', component: ReportPage },
  history: { label: 'Historique', component: HistoryPage },
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
    fetch('/api/v1/health').then((r) => setBackendState(r.ok ? 'ok' : 'error')).catch(() => setBackendState('error'));
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const navigate = (name) => { window.location.hash = `/${name}`; };
  const Page = routes[route].component;

  return (
    <AppLayout activeRoute={route} navigate={navigate} backendState={backendState}>
      <Page navigate={navigate} />
    </AppLayout>
  );
}
