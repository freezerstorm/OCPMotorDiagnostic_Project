// ============================================================
// PAGE CONNEXION AU KIT — Étape 7 (réelle, temps réel).
//
// La page observe les kits présents sur le broker MQTT via le
// backend (WebSocket /ws/kits). Elle affiche :
//   - l'état du service (liaison au backend) ;
//   - les kits détectés : identifiant, firmware, ESP32, état ;
//   - la sélection d'un kit → « Kit connecté — prêt pour le diagnostic ».
//
// Conformément au §8 :
//   - la « connexion » n'est pas inventée : elle reflète la présence
//     réelle du kit (messages MQTT reçus par le backend) ;
//   - si le kit choisi disparaît, la page le signale clairement et
//     revient à l'état déconnecté ;
//   - le bouton START (écran suivant) ne sera actif que si un kit est
//     réellement connecté (Étape 8).
//
// Le kit retenu est transmis aux écrans suivants via l'URL (?kitId=).
// ============================================================
import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import useKitSocket from '../websocket/useKitSocket';

export default function KitConnectionPage() {
  const { wsState, kits } = useKitSocket();
  const [selectedKitId, setSelectedKitId] = useState(null);
  // Session en cours ? (arrivée depuis « Continuer avec le kit ») :
  // l'action du bas enchaîne alors vers l'ACQUISITION avec le kit retenu.
  const [searchParams] = useSearchParams();
  const testId = searchParams.get('testId');

  const onlineKits = kits.filter((kit) => kit.state === 'online');
  const selectedKit = kits.find((kit) => kit.kit_id === selectedKitId) ?? null;
  const selectedOnline = selectedKit?.state === 'online';

  // Si le kit sélectionné se déconnecte → on revient à l'état d'attente
  useEffect(() => {
    if (selectedKitId && !selectedOnline) {
      setSelectedKitId(null);
    }
  }, [selectedKitId, selectedOnline]);

  const serviceOk = wsState === 'open';
  const navigate = useNavigate();

  // REDIRECTION AUTOMATIQUE (demande client) : une fois le kit connecté,
  // si une session de diagnostic est en cours (?testId=…), on rejoint
  // l'ACQUISITION automatiquement — après un court instant pour laisser
  // voir le retour « Connecté ✓ ».
  useEffect(() => {
    if (!selectedOnline || !testId || !selectedKitId) return undefined;
    const timer = setTimeout(() => {
      navigate(
        `/test/automatique/acquisition?testId=${testId}&kitId=${encodeURIComponent(selectedKitId)}`,
      );
    }, 900);
    return () => clearTimeout(timer);
  }, [selectedOnline, testId, selectedKitId, navigate]);

  return (
    <>
      <h1 className="page-title">Connexion au kit</h1>
      {/* ===== État général ===== */}
      <section className="card">
        <div className="kit-banner">
          {!serviceOk && (
            <span className="badge badge-warn badge-lg">
              <span className="badge-dot" aria-hidden="true" />
              {wsState === 'connecting' ? 'Connexion au service…' : 'Service temps réel coupé — reconnexion…'}
            </span>
          )}
          {serviceOk && onlineKits.length === 0 && (
            <span className="badge badge-warn badge-lg">
              <span className="badge-dot" aria-hidden="true" />
              Kit déconnecté — aucun kit détecté
            </span>
          )}
          {serviceOk && onlineKits.length > 0 && !selectedKitId && (
            <span className="badge badge-info badge-lg">
              <span className="badge-dot" aria-hidden="true" />
              {onlineKits.length} kit{onlineKits.length > 1 ? 's' : ''} détecté{onlineKits.length > 1 ? 's' : ''} — sélectionnez-en un
            </span>
          )}
          {selectedOnline && (
            <span className="badge badge-ok badge-lg">
              <span className="badge-dot" aria-hidden="true" />
              Kit connecté — prêt pour le diagnostic
            </span>
          )}
        </div>

        {/* ===== Kit sélectionné ===== */}
        {selectedOnline && selectedKit && (
          <div className="kit-info kit-selected">
            <div className="kit-info-item">
              <span className="muted small">Identifiant du kit</span>
              <strong>{selectedKit.kit_id}</strong>
            </div>
            <div className="kit-info-item">
              <span className="muted small">ESP32 détecté</span>
              <strong>{selectedKit.esp32_detected ? 'Oui' : 'Non'}</strong>
            </div>
            <div className="kit-info-item">
              <span className="muted small">Version du firmware</span>
              <strong>{selectedKit.firmware ?? '—'}</strong>
            </div>
            {selectedKit.simulated && (
              <div className="kit-info-item">
                <span className="muted small">Type</span>
                <strong>Simulateur (développement)</strong>
              </div>
            )}
          </div>
        )}

        {/* ===== Liste des kits détectés ===== */}
        {serviceOk && (
          <>
            <h3 className="summary-h">Kits sur le réseau MQTT</h3>
            {kits.length === 0 ? (
              <p className="muted small">
                Aucun kit connu pour le moment. Vérifiez que le broker MQTT est lancé et
                qu'un kit (ou le simulateur) publie sa présence.
              </p>
            ) : (
              <div className="kit-device-list">
                {kits.map((kit) => (
                  <div className={`kit-device ${kit.kit_id === selectedKitId ? 'kit-device-selected' : ''}`} key={kit.kit_id}>
                    <span className={`badge ${kit.state === 'online' ? 'badge-ok' : 'badge-neutral'}`}>
                      <span className="badge-dot" aria-hidden="true" />
                      {kit.state === 'online' ? 'En ligne' : 'Hors ligne'}
                    </span>
                    <div className="kit-device-info">
                      <strong>{kit.kit_id}</strong>
                      <span className="muted small">
                        firmware {kit.firmware ?? '?'} · ESP32 {kit.esp32_detected ? 'détecté' : '—'}
                      </span>
                    </div>
                    {kit.state === 'online' && (
                      <button
                        className={`btn btn-sm ${kit.kit_id === selectedKitId ? 'btn-connected' : 'btn-primary'}`}
                        type="button"
                        onClick={() => setSelectedKitId(kit.kit_id)}
                        title={kit.kit_id === selectedKitId ? 'Kit connecté — redirection vers l\'acquisition…' : 'Connecter ce kit pour le diagnostic'}
                      >
                        {kit.kit_id === selectedKitId ? 'Connecté ✓' : 'Connecter le kit'}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* ===== Actions ===== */}
        <div className="actions-row">
          <Link className="btn btn-ghost" to="/">← Accueil</Link>
          <span className="flex-spacer" />
          {selectedOnline && testId && (
            <Link
              className="btn btn-accent btn-lg"
              to={`/test/automatique/acquisition?testId=${testId}&kitId=${encodeURIComponent(selectedKit.kit_id)}`}
            >
              Aller à l'acquisition →
            </Link>
          )}
          {selectedOnline && !testId && (
            <Link
              className="btn btn-accent btn-lg"
              to="/test/sous-tension"
            >
              Continuer le parcours →
            </Link>
          )}
        </div>
      </section>

    </>
  );
}
