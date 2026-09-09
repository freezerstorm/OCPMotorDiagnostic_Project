import { SectionIntro } from '../components';

export function KitConnectionPage({ navigate }) {
  // Étape 7 ajoutera la connexion MQTT réelle. Pour l'instant, bouton factice
  // qui simule un kit connecté et redirige vers le formulaire moteur en mode auto.
  const connect = () => navigate('motor', { mode: 'auto', kitId: 'KIT-SIM-001' });

  return (
    <>
      <SectionIntro
        eyebrow="ÉTAPE 1 — CONNEXION AU KIT"
        title="Connecter le kit de diagnostic"
        text="Vérifiez la liaison avec l'ESP32 avant de commencer l'acquisition. La connexion MQTT réelle sera activée à l'étape 7."
      />
      <div className="connection-card">
        <div className="connection-visual">
          <div className="kit-orb">⌁</div>
          <span className="status-pill neutral">Non connecté</span>
        </div>
        <div className="connection-details">
          <h3>Kit de diagnostic</h3>
          <dl>
            <dt>Identifiant</dt><dd>—</dd>
            <dt>ESP32</dt><dd>En attente de détection</dd>
            <dt>Firmware</dt><dd>—</dd>
            <dt>Capteurs</dt><dd>PT100 (MAX31865) · ADXL345 · SCT-013-000</dd>
          </dl>
          <button className="button primary" onClick={connect}>Connecter le kit <span>→</span></button>
          <p className="muted">En développement : ce bouton simule une connexion établie. La gestion MQTT réelle (états, reconnexion, perte de lien) sera ajoutée à l'étape 7.</p>
        </div>
      </div>
    </>
  );
}
