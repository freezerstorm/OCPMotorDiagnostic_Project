import { SectionIntro } from '../components';

export function GraphPage({ navigate }) {
  return (
    <>
      <SectionIntro
        eyebrow="ÉTAPE — VIEW GRAPH"
        title="Visualisation des mesures"
        text="Trois figures distinctes (température, courant, vibration) avec grille, curseur et statistiques (min / max / moyenne / durée)."
      />
      <div className="coming-soon">
        <span>◌</span>
        <h3>Module prévu à l'étape 9</h3>
        <p>Les graphiques Recharts seront ajoutés ici avec leurs statistiques associées.</p>
        <div className="form-actions" style={{ justifyContent: 'center' }}>
          <button className="button secondary" onClick={() => navigate('acquisition')}>← Retour</button>
          <button className="button primary" onClick={() => navigate('analysis')}>Analysis →</button>
        </div>
      </div>
    </>
  );
}
