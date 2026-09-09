import { SectionIntro } from '../components';

// Étape 8 ajoutera l'acquisition WebSocket/MQTT réelle.
// Pour l'instant, écran statique qui respecte la maquette visuelle.
export function AcquisitionPage({ navigate }) {
  return (
    <>
      <SectionIntro
        eyebrow="ÉTAPE — ACQUISITION ~60 s"
        title="Acquisition des mesures automatiques"
        text="Le kit acquiert température, courant et vibration. Les boutons VIEW GRAPH / ANALYSIS / REPORT seront activés aux étapes 9-12."
      />
      <div className="acquisition-card">
        <div className="acquisition-status">
          <span className="big-status-dot ready" />
          <span>Prêt (kit connecté)</span>
          <small>Appuyez sur START pour lancer l'acquisition de 60 secondes.</small>
        </div>
        <div className="progress-track"><span style={{ width: '0%' }} /></div>
        <div className="acquisition-actions">
          <button className="button primary" onClick={() => navigate('graph')}>START (simulé)</button>
          <button className="button secondary" onClick={() => navigate('home')}>Quitter</button>
        </div>
        <div className="state-list">
          <span className="done">IDLE</span>
          <span className="done">READY</span>
          <span>ACQUIRING</span>
          <span>COMPLETED</span>
        </div>
        <p className="muted" style={{ marginTop: 20 }}>L'acquisition réelle (MQTT + WebSocket + gestion des états et des pertes de connexion) sera implémentée aux étapes 7 et 8.</p>
      </div>
    </>
  );
}
