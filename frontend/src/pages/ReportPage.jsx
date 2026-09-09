import { SectionIntro } from '../components';

export function ReportPage({ navigate }) {
  return (
    <>
      <SectionIntro
        eyebrow="ÉTAPE — RAPPORT"
        title="Rapport de diagnostic (PDF)"
        text="Rapport PDF officiel généré côté backend, reprenant l'esprit de la fiche d'essai OCP (moteur, mesures, analyse, risques, recommandations, décision, traçabilité)."
      />
      <div className="coming-soon">
        <span>◌</span>
        <h3>Module prévu à l'étape 12</h3>
        <p>Le PDF sera généré par WeasyPrint à partir d'un modèle HTML/CSS.</p>
        <div className="form-actions" style={{ justifyContent: 'center' }}>
          <button className="button secondary" onClick={() => navigate('history')}>Historique</button>
          <button className="button primary" onClick={() => navigate('home')}>Terminer → Accueil</button>
        </div>
      </div>
    </>
  );
}
