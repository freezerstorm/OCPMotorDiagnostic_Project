// ============================================================
// HOOK TEMPS RÉEL — connecte la page au backend en WebSocket (/ws/kits).
//
//   wsState   : 'connecting' | 'open' | 'closed'
//   kits      : [{ kit_id, state, firmware, esp32_detected, ... }]
//   lastEvent : dernier événement reçu autre que le snapshot :
//                 - kit_status / acquisition_started /
//                   acquisition_completed / acquisition_stopped /
//                   acquisition_error / sample
//               (null s'il n'y en a pas encore)
//
// Reconnexion automatique si la liaison est coupée (utile aussi quand
// le kit disparaît en plein test, §8).
// ============================================================
import { useEffect, useRef, useState } from 'react';

function kitSocketUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${protocol}://${window.location.host}/ws/kits`;
}

export default function useKitSocket() {
  const [wsState, setWsState] = useState('connecting'); // connecting|open|closed
  const [kits, setKits] = useState([]);
  const [lastEvent, setLastEvent] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    const connect = () => {
      setWsState('connecting');
      const socket = new WebSocket(kitSocketUrl());
      socketRef.current = socket;

      socket.onopen = () => !cancelled && setWsState('open');

      socket.onmessage = (event) => {
        if (cancelled) return;
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'kits_snapshot') {
            setKits(message.kits ?? []);
            return;
          }
          if (message.type === 'kit_status' && message.kit) {
            // Met à jour le kit concerné (ou l'ajoute) dans la liste
            setKits((previous) => {
              const others = previous.filter((k) => k.kit_id !== message.kit.kit_id);
              return [...others, message.kit];
            });
          }
          // Tous les autres événements (samples, acquisition_*) sont
          // exposés via lastEvent pour que les pages puissent réagir.
          setLastEvent(message);
        } catch {
          /* message illisible : ignoré */
        }
      };

      socket.onclose = () => {
        if (cancelled) return;
        setWsState('closed');
        // Reconnexion automatique après 2 s (le backend peut redémarrer)
        setTimeout(() => { if (!cancelled) connect(); }, 2000);
      };

      socket.onerror = () => socket.close();
    };

    connect();

    return () => {
      cancelled = true;
      socketRef.current?.close();
    };
  }, []);

  return { wsState, kits, lastEvent };
}
