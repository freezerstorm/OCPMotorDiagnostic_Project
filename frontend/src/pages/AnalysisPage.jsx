import { SectionIntro } from '../components';

export function AnalysisPage({ navigate }) {
  return (
    <>
      <SectionIntro
        eyebrow="ÉTAPE — ANALYSIS"
        title="Analyse du diagnostic"
        text="Analyse paramètre par paramètre (valeur mesurée → référence → évaluation → interprétation → risque → recommandation), plus conclusion automatique et décision du technicien."
      />
      <div className="coming-soon">
        <span>◌</span>
        <h3>Module prévu aux étapes 10 et 11</h3>
        <p>Le moteur de règles modulaires (dossier diagnostic_rules/) puis la page d'analyse seront implémentés ici.</p>
        <div className="form-actions" style={{ justifyContent: 'center' }}>
          <button className="button secondary" onClick={() => navigate('graph')}>← Retour</button>
          <button className="button primary" onClick={() => navigate('report')}>Rapport →</button>
        </div>
      </div>
    </>
  );
}
