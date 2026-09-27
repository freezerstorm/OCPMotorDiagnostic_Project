// ============================================================
// PAGE ACQUISITION — Étape 8 (réelle, branchée sur le backend).
//
// Machine à états (§11) :  IDLE → READY → ACQUIRING → COMPLETED
//                          (ou ERROR si le kit est perdu)
//
// Règles :
//   START  cliquable UNIQUEMENT si le kit est réellement connecté ;
//   QUIT   arrête l'acquisition (les mesures déjà reçues sont gardées) ;
//   VIEW GRAPH  pendant et après l'acquisition ;
//   ANALYSIS    après l'acquisition ;
//   REPORT      quand les données nécessaires sont présentes.
//
// Arrivée : /test/automatique/acquisition?testId=…&kitId=…
// Les événements temps réel (échantillons, fin, erreur) arrivent par
// WebSocket (useKitSocket) ; les boutons appellent l'API (start/stop).
// ============================================================
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { fetchSamples, fetchTest, startAcquisition, stopAcquisition, validateOnline } from '../services/api';
import useKitSocket from '../websocket/useKitSocket';

// États possibles de l'écran
const UI_STATES = {
  IDLE: 'IDLE',           // test créé, kit requis
  READY: 'READY',         // kit connecté : START est actif
  ACQUIRING: 'ACQUIRING', // acquisition en cours
  COMPLETED: 'COMPLETED', // terminée (~60 s ou QUIT)
  ERROR: 'ERROR',         // kit perdu pendant le test
};

export default function AcquisitionPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const testId = searchParams.get('testId');
  const requestedKitId = searchParams.get('kitId') ?? '';

  const { wsState, kits, lastEvent } = useKitSocket();

  const [uiState, setUiState] = useState(UI_STATES.IDLE);
  const [durationS, setDurationS] = useState(60);     // durée annoncée par le backend
  const [elapsedS, setElapsedS] = useState(0);        // décompte affiché
  const [sampleCount, setSampleCount] = useState(0);
  const [lastValues, setLastValues] = useState(null); // dernières mesures reçues
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);
  // Statut du test (chargé à l'ouverture, rafraîchi après validation) :
  // sert à n'afficher la VALIDATION que s'il reste à faire. La tension
  // d'alimentation est saisie sur la page « Test sous tension » (client).
  const [testStatus, setTestStatus] = useState(null);
  const startedAtRef = useRef(null);
  // Miroir de l'état d'affichage pour les gestionnaires d'événements
  // (évite de les relancer à chaque changement d'état).
  const uiStateRef = useRef(uiState);
  useEffect(() => {
    uiStateRef.current = uiState;
  }, [uiState]);

  // É17 — si aucun kit n'est indiqué dans l'URL (arrivée depuis le choix
  // « Continuer avec le kit » de la page Test sous tension), on retient
  // AUTOMATIQUEMENT le premier kit EN LIGNE. Sinon, on garde le kit
  // demandé ; s'il est absent de la liste, il apparaît hors ligne.
  const kit =
    kits.find((k) => k.kit_id === requestedKitId) ??
    (requestedKitId === '' ? kits.find((k) => k.state === 'online') : undefined);
  const kitId = kit?.kit_id ?? requestedKitId;
  const kitOnline = kit?.state === 'online';

  // ===== Au repos : IDLE ↔ READY selon la connexion du kit =====
  // IDLE  : le kit n'est pas (ou plus) connecté → START inactif.
  // READY : le kit est connecté → START actif.
  //
  // IMPORTANT : les états ACQUIRING et surtout COMPLETED / ERROR sont
  // GELÉS. Un état final ne doit JAMAIS être écrasé automatiquement par
  // cet effet, sinon le résultat de l'acquisition (badge, message et
  // activation de Analysis/Report) disparaîtrait aussitôt affiché.
  useEffect(() => {
    setUiState((current) => {
      if (
        current === UI_STATES.ACQUIRING ||
        current === UI_STATES.COMPLETED ||
        current === UI_STATES.ERROR
      ) {
        return current;
      }
      return kitOnline && wsState === 'open' ? UI_STATES.READY : UI_STATES.IDLE;
    });
  }, [kitOnline, wsState]);

  // ===== Reprise d'état au chargement de la page =====
  // Si le technicien recharge la page (ou revient dessus) en plein test,
  // l'écran doit retrouver le vrai état du test depuis le backend :
  //   draft → au repos, acquiring → en cours, completed/error → terminé.
  useEffect(() => {
    if (!testId) return undefined;
    let cancelled = false;

    (async () => {
      try {
        const [test, samples] = await Promise.all([fetchTest(testId), fetchSamples(testId)]);
        if (cancelled) return;

        setTestStatus(test.status);

        setSampleCount(samples.count ?? 0);
        const last = samples.samples?.[samples.samples.length - 1];
        if (last) {
          setLastValues({
            temperature_c: last.temperature_c,
            current_a: last.current_a,
            vib_global_mm_s: last.vibration?.global_mm_s ?? null,
          });
        }

        if (test.status === 'acquiring') {
          // REPRISE SANS REMISE À ZÉRO : le temps déjà écoulé se lit sur
          // le dernier échantillon reçu (t_s = secondes depuis le START)
          // et les mesures déjà enregistrées sont conservées. Rien ne
          // redémarre : le test continue côté backend.
          const elapsed = last?.t_s ?? 0;
          startedAtRef.current = Date.now() - elapsed * 1000;
          setElapsedS(Math.min(durationS, Math.round(elapsed)));
          setUiState(UI_STATES.ACQUIRING);
          setMessage({
            type: 'info',
            text: `Acquisition en cours — reprise : ${samples.count ?? 0} mesure(s) déjà enregistrée(s). L'acquisition n'a pas été interrompue.`,
          });
        } else if (test.status === 'completed') {
          setUiState(UI_STATES.COMPLETED);
          setMessage({ type: 'success', text: `Acquisition déjà terminée : ${samples.count ?? 0} mesures enregistrées.` });
        } else if (test.status === 'error') {
          setUiState(UI_STATES.ERROR);
          setMessage({ type: 'error', text: 'Le test s\'est terminé sur une erreur (kit perdu). Les mesures reçues sont conservées.' });
        }
      } catch {
        // Test inconnu ou backend indisponible : l'écran reste au repos,
        // le WebSocket fera remonter l'état du kit.
      }
    })();

    return () => { cancelled = true; };
  }, [testId]);

  // ===== Décompte pendant l'acquisition =====
  useEffect(() => {
    if (uiState !== UI_STATES.ACQUIRING) return undefined;
    const timer = setInterval(() => {
      if (startedAtRef.current) {
        setElapsedS(Math.min(durationS, Math.round((Date.now() - startedAtRef.current) / 1000)));
      }
    }, 250);
    return () => clearInterval(timer);
  }, [uiState, durationS]);

  // ===== Événements temps réel du backend =====
  useEffect(() => {
    if (!lastEvent) return;

    if (lastEvent.type === 'acquisition_started' && lastEvent.test_id === testId) {
      // Garde anti-remise-à-zéro : si l'écran est DÉJÀ en acquisition
      // (reprise après navigation/rechargement), on ne réinitialise RIEN.
      if (uiStateRef.current === UI_STATES.ACQUIRING) return;
      setUiState(UI_STATES.ACQUIRING);
      setDurationS(lastEvent.duration_s ?? 60);
      startedAtRef.current = Date.now();
      setElapsedS(0);
      setSampleCount(0);
      setMessage(null);
    } else if (lastEvent.type === 'sample' && lastEvent.test_id === testId) {
      setSampleCount((count) => count + 1);
      setLastValues(lastEvent);
    } else if (lastEvent.type === 'acquisition_completed' && lastEvent.test_id === testId) {
      setUiState(UI_STATES.COMPLETED);
      setMessage({ type: 'success', text: `Acquisition terminée : ${lastEvent.samples_count ?? sampleCount} mesures enregistrées.` });
    } else if (lastEvent.type === 'acquisition_stopped' && lastEvent.test_id === testId) {
      setUiState(UI_STATES.COMPLETED);
      setMessage({ type: 'info', text: `Acquisition arrêtée (QUIT) : ${lastEvent.samples_count ?? sampleCount} mesures conservées.` });
    } else if (lastEvent.type === 'acquisition_error' && lastEvent.test_id === testId) {
      setUiState(UI_STATES.ERROR);
      setMessage({
        type: 'error',
        text: 'Perte de connexion avec le kit pendant l\'acquisition. Le test a été arrêté proprement ; les mesures déjà reçues sont conservées.',
      });
    }
  }, [lastEvent, testId, sampleCount]);

  // ===== Actions =====
  const handleStart = async () => {
    setBusy(true);
    setMessage(null);
    try {
      const result = await startAcquisition(testId, kitId);
      setDurationS(result.duration_s ?? 60);
      // L'événement acquisition_started (WebSocket) bascule l'état ;
      // on force aussi ici si l'événement tarde.
      setUiState(UI_STATES.ACQUIRING);
      startedAtRef.current = Date.now();
      setElapsedS(0);
      setSampleCount(0);
    } catch (error) {
      setMessage({ type: 'error', text: `Impossible de démarrer : ${error.message}` });
    } finally {
      setBusy(false);
    }
  };

  const handleQuit = useCallback(async () => {
    setBusy(true);
    try {
      await stopAcquisition(testId);
      // L'événement acquisition_stopped (WebSocket) met à jour l'état
    } catch {
      setMessage({ type: 'error', text: 'Impossible d\'arrêter l\'acquisition.' });
    } finally {
      setBusy(false);
    }
  }, [testId]);

  // START n'est actif qu'au repos (IDLE/READY) ET kit réellement connecté ;
  // une fois l'acquisition terminée (COMPLETED/ERROR), on ne relance pas
  // depuis cet écran : les boutons permettent de consulter les résultats.
  const atRest = uiState === UI_STATES.IDLE || uiState === UI_STATES.READY;
  const canStart = kitOnline && wsState === 'open' && atRest && !busy;
  const isAcquiring = uiState === UI_STATES.ACQUIRING;
  const finished = uiState === UI_STATES.COMPLETED || uiState === UI_STATES.ERROR;
  const hasSamples = sampleCount > 0;

  // ===== Complément OBLIGATOIRE après l'acquisition (décision client) =====
  // Le kit mesure courant / températures / vibration mais PAS la tension :
  // à la fin de l'acquisition, le technicien saisit la tension
  // d'alimentation mesurée puis VALIDE LE TEST (validate-online).
  const complementTensionRequis =
    uiState === UI_STATES.COMPLETED &&
    testStatus !== null &&
    testStatus !== 'completed';

  const handleValidateKit = async () => {
    setBusy(true);
    setMessage(null);
    try {
      await validateOnline(testId);
      setTestStatus('completed');
      navigate(`/test/analyse?testId=${testId}`);
    } catch (error) {
      setBusy(false);
      setMessage({ type: 'error', text: `Validation impossible : ${error.message}` });
    }
  };

  const stateLabel = {
    [UI_STATES.IDLE]: 'En attente du kit',
    [UI_STATES.READY]: 'Prêt — kit connecté',
    [UI_STATES.ACQUIRING]: 'Acquisition en cours…',
    [UI_STATES.COMPLETED]: 'Acquisition terminée',
    [UI_STATES.ERROR]: 'Erreur — acquisition interrompue',
  }[uiState];

  const stateBadge =
    uiState === UI_STATES.ERROR ? 'badge-error'
      : isAcquiring ? 'badge-info'
        : uiState === UI_STATES.COMPLETED ? 'badge-ok'
          : uiState === UI_STATES.READY ? 'badge-ok'
            : 'badge-warn';

  return (
    <>
      <h1 className="page-title">Acquisition automatique</h1>
      {/* Fiche du test / kit */}
      <section className="card">
        <div className="kit-info">
          <div className="kit-info-item">
            <span className="muted small">Test</span>
            <strong className="mono">{testId ?? '—'}</strong>
          </div>
          <div className="kit-info-item">
            <span className="muted small">Kit</span>
            <strong>{kitId || '—'}</strong>
          </div>
          <div className="kit-info-item">
            <span className="muted small">État du kit</span>
            {kitOnline ? (
              <span className="badge badge-ok"><span className="badge-dot" aria-hidden="true" /> En ligne</span>
            ) : (
              <span className="badge badge-error"><span className="badge-dot" aria-hidden="true" /> Hors ligne</span>
            )}
          </div>
          <div className="kit-info-item">
            <span className="muted small">Mesures reçues</span>
            <strong>{sampleCount}</strong>
          </div>
          {isAcquiring && (
            <div className="kit-info-item">
              <span className="muted small">Temps écoulé</span>
              <strong>{elapsedS} s / {Math.round(durationS)} s</strong>
            </div>
          )}
        </div>
      </section>

      {/* État + boutons */}
      <section className="card">
        <div className="acq-status">
          <span className={`badge ${stateBadge} badge-lg`}>
            <span className="badge-dot" aria-hidden="true" />
            {stateLabel}
          </span>

          {isAcquiring && lastValues && (
            <span className="muted small live-values">
              T={lastValues.temperature_c != null ? `${lastValues.temperature_c} °C` : '—'}
              {' · '}I={lastValues.current_a != null ? `${lastValues.current_a} A` : '—'}
              {' · '}V={lastValues.vib_global_mm_s != null ? `${lastValues.vib_global_mm_s} mm/s` : '—'}
            </span>
          )}
        </div>

        {message && (
          <div className={`alert alert-${message.type} mt-2`} role="status">
            {message.text}
          </div>
        )}

        {/* Boutons de contrôle */}
        <div className="actions-row">
          <button className="btn btn-primary btn-lg" onClick={handleStart} disabled={!canStart} title={kitOnline ? '' : 'START n\'est actif que si le kit est connecté (§8)'}>
            {busy && uiState !== UI_STATES.ACQUIRING ? 'Démarrage…' : 'START'}
          </button>
          <button className="btn btn-danger" onClick={handleQuit} disabled={!isAcquiring || busy}>
            QUIT
          </button>
          <span className="flex-spacer" />
          {/* VIEW GRAPH : pendant et après l'acquisition */}
          <Link
            className="btn btn-outline"
            to={testId ? `/test/visualisation?testId=${testId}` : '/test/visualisation'}
            aria-disabled={!isAcquiring && !hasSamples && !finished}
          >
            View graph
          </Link>
          {/* ANALYSIS : uniquement après l'acquisition */}
          <Link
            className={`btn ${finished ? 'btn-accent' : 'btn-ghost'}`}
            to={testId ? `/test/analyse?testId=${testId}` : '/test/analyse'}
            aria-disabled={!finished}
          >
            Analysis
          </Link>
          {/* REPORT : quand les données nécessaires sont présentes */}
          <Link
            className="btn btn-outline"
            to={testId ? `/test/rapport?testId=${testId}` : '/test/rapport'}
            aria-disabled={!finished}
          >
            Report
          </Link>
        </div>

        {/* Complément OBLIGATOIRE : tension d'alimentation + VALIDER LE TEST.
            Visible à la fin d'une acquisition réussie tant que le test
            n'est pas validé (le kit ne mesure pas la tension). */}
        {complementTensionRequis && (
          <div className="mt-2">
            <h2>Complément obligatoire</h2>
            <p className="muted small">
              La tension d'alimentation se saisit sur la page
              « Test sous tension ». Vérifiez-la, puis validez le test.
            </p>
            <div className="actions-row">
              <button
                type="button"
                className="btn btn-primary btn-lg"
                onClick={handleValidateKit}
                disabled={busy}
              >
                {busy ? 'Enregistrement…' : '✓ Valider le test'}
              </button>
            </div>
          </div>
        )}
      </section>

    </>
  );
}
