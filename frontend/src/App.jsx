// ============================================================
// APPLICATION — Étape 2 : navigation et écrans principaux.
//
// Le routeur déclare la correspondance entre chaque ADRESSE
// (URL) et la PAGE à afficher. Ajouter un écran = ajouter une
// ligne <Route> ici + un fichier dans src/pages/.
//
// Parcours principal (§6) :
//   Accueil → Nouveau test → [manuel | automatique]
//   manuel     : Formulaire moteur → Analyse → Rapport
//   automatique: Connexion kit → Formulaire → Acquisition →
//                View Graph → Analyse → Rapport
//   Historique : accessible depuis l'Accueil et le menu.
// ============================================================
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';

import AppLayout from './layouts/AppLayout.jsx';

import HomePage from './pages/HomePage.jsx';
import KitConnectionPage from './pages/KitConnectionPage.jsx';
import HorsTensionPage from './pages/HorsTensionPage.jsx';
import SousTensionPage from './pages/SousTensionPage.jsx';
import AcquisitionPage from './pages/AcquisitionPage.jsx';
import ViewGraphPage from './pages/ViewGraphPage.jsx';
import AnalysePage from './pages/AnalysePage.jsx';
import ReportPage from './pages/ReportPage.jsx';
import HistoryPage from './pages/HistoryPage.jsx';
import RegistryPage from './pages/RegistryPage.jsx';

// Page affichée quand l'adresse ne correspond à aucune route
function NotFoundPage() {
  return (
    <section className="card">
      <h2>Page introuvable</h2>
      <p className="card-hint">L'adresse demandée ne correspond à aucun écran du parcours.</p>
      <Link className="btn btn-primary" to="/">← Retour à l'accueil</Link>
    </section>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Gabarit commun : en-tête + menu + pied de page */}
        <Route element={<AppLayout />}>
          {/* Accueil */}
          <Route path="/" element={<HomePage />} />

          {/* Parcours en étapes : moteur (accueil) → hors tension → sous tension */}
          <Route path="/test/hors-tension" element={<HorsTensionPage />} />
          <Route path="/test/sous-tension" element={<SousTensionPage />} />

          {/* Test automatique : connexion kit → formulaire → acquisition */}
          <Route path="/connexion-kit" element={<KitConnectionPage />} />
          <Route path="/test/automatique/connexion" element={<KitConnectionPage />} />
          <Route path="/test/:mode/acquisition" element={<AcquisitionPage />} />

          {/* Étapes communes aux deux modes */}
          <Route path="/test/visualisation" element={<ViewGraphPage />} />
          <Route path="/test/analyse" element={<AnalysePage />} />
          <Route path="/test/rapport" element={<ReportPage />} />

          {/* Historique */}
          <Route path="/historique" element={<HistoryPage />} />

          <Route path="/registre" element={<RegistryPage />} />

          {/* Toute autre adresse */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
