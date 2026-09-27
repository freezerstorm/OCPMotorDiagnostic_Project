// ============================================================
// PAGE TEST SOUS TENSION — ÉTAPES 5-6 DU PARCOURS (§6 du cahier).
//
// Au début de la page, le technicien choisit (boutons aux
// extrémités de la page, demande client) :
//
//   [ MANUEL ] à gauche    → saisie des mesures (courant à vide,
//                            températures des 2 paliers, vibration)
//                            puis « VALIDER LE TEST ».
//
//   [ CONTINUER AVEC LE KIT ] à droite → la session passe en mode
//                            « auto » et l'acquisition du kit s'ouvre
//                            (60 s). Le retour se fait ici pour
//                            VALIDER LE TEST.
//
// Le bouton REPORT n'existe PAS ici : le rapport est accessible
// uniquement depuis l'ANALYSE (§8 et §18 du cahier des charges).
// ============================================================
import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { TEST_STATUSES } from '../constants';
import { fetchTest, updateTest, validateOnline } from '../services/api';

const INITIAL_VALUES = {
  supplyVoltage: '',
  current_a: '',
  temp_bearing_de: '',
  temp_bearing_nde: '',
  refMeterCl: '',
  refMeterTemperature: '',
  vibration_mm_s: '',
};

/** « 12,5 » → 12.5 ; champ vide → undefined (absent du JSON). */
function toNumberOrUndefined(value) {
  const text = String(value ?? '').trim().replace(',', '.');
  if (text === '') return undefined;
  const n = Number(text);
  return Number.isFinite(n) ? n : undefined;
}

export default function SousTensionPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const testId = searchParams.get('testId');

  const [test, setTest] = useState(null);
  const [loadState, setLoadState] = useState('loading'); // loading|ok|error
  const [mode, setMode] = useState(null); // null | 'manual' | 'kit'
  const [values, setValues] = useState(INITIAL_VALUES);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    if (!testId) {
      setLoadState('error');
      return;
    }
    fetchTest(testId)
      .then((data) => {
        setTest(data);
        // Saisie préservée : une tension déjà enregistrée reprend sa place
        setValues((v) => ({
          ...v,
          supplyVoltage: data.measurements?.values?.supply_voltage_v ?? '',
        }));
        setLoadState('ok');
      })
      .catch(() => setLoadState('error'));
  }, [testId]);

  const setValue = (field) => (event) => {
    setValues({ ...values, [field]: event.target.value });
    setMessage(null);
  };

  // ===== Mode KIT : session passe en « auto » → page de connexion =====
  const handleKit = async () => {
    // Tension d'alimentation OBLIGATOIRE avant le kit (le kit ne la
    // mesure pas) : elle est saisie sur cette page et enregistrée ici.
    const supply = toNumberOrUndefined(values.supplyVoltage);
    if (supply === undefined) {
      setMessage({
        type: 'error',
        text: "Tension d'alimentation obligatoire : saisissez la tension mesurée (V) avant de continuer avec le kit.",
      });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await updateTest(testId, { measurements: { values: { supply_voltage_v: supply } } });
      await updateTest(testId, { mode: 'auto' });
      // Le parcours passe par la page de CONNEXION (kit détecté affiché +
      // bouton « Connecter le kit »), puis « Aller à l'acquisition ».
      navigate(`/test/automatique/connexion?testId=${testId}`);
    } catch (error) {
      setBusy(false);
      setMessage({ type: 'error', text: `Impossible de passer en mode kit : ${error.message}` });
    }
  };

  // ===== Mode MANUEL : saisie puis VALIDER LE TEST =====
  const handleValidateManual = async (event) => {
    event.preventDefault();

    // Tension d'alimentation OBLIGATOIRE (décision client 26/09/2026)
    const supply = toNumberOrUndefined(values.supplyVoltage);
    if (supply === undefined) {
      setMessage({
        type: 'error',
        text: "Tension d'alimentation obligatoire : saisissez la tension mesurée (V) avant de valider le test.",
      });
      return;
    }

    const singleValues = {};
    singleValues.supply_voltage_v = supply;
    const current = toNumberOrUndefined(values.current_a);
    if (current !== undefined) singleValues.current_a = current;
    const tempDe = toNumberOrUndefined(values.temp_bearing_de);
    if (tempDe !== undefined) singleValues.temp_bearing_de_c = tempDe;
    const tempNde = toNumberOrUndefined(values.temp_bearing_nde);
    if (tempNde !== undefined) singleValues.temp_bearing_nde_c = tempNde;
    const vibration = toNumberOrUndefined(values.vibration_mm_s);
    if (vibration !== undefined) singleValues.vibration_mm_s = vibration;
    if (values.refMeterCl.trim() !== '') {
      singleValues.ref_meter_cl = values.refMeterCl.trim();
    }
    if (values.refMeterTemperature.trim() !== '') {
      singleValues.ref_meter_temperature = values.refMeterTemperature.trim();
    }

    setBusy(true);
    setMessage(null);
    try {
      // 1. Enregistrement des mesures saisies
      await updateTest(testId, { measurements: { values: singleValues } });
      // 2. VALIDER LE TEST : la session passe à « terminé »
      await validateOnline(testId);
      // 3. Étape suivante : ANALYSE (le rapport part de là — §18)
      navigate(`/test/analyse?testId=${testId}&justSaved=1`);
    } catch (error) {
      setBusy(false);
      setMessage({ type: 'error', text: `Validation impossible : ${error.message}` });
    }
  };

  const renderTextField = (field, opts = {}) => (
    <div className="form-group" key={field.id}>
      <label htmlFor={`st_${field.id}`}>{field.label}</label>
      <input
        id={`st_${field.id}`}
        type={opts.type ?? 'text'}
        value={values[field.id] ?? ''}
        onChange={setValue(field.id)}
        placeholder={opts.placeholder ?? '—'}
      />
    </div>
  );

  // ===== États d'attente / d'erreur =====
  if (loadState === 'loading') {
    return <p className="muted small">Chargement de la session…</p>;
  }
  if (loadState === 'error' || !test) {
    return (
      <section className="card">
        <h2>Session introuvable</h2>
        <Link className="btn btn-primary" to="/">← Retour à l'accueil</Link>
      </section>
    );
  }

  const motor = test.motor ?? {};
  const alreadyValidated = test.status === TEST_STATUSES.COMPLETED;

  return (
    <>
      <h1 className="page-title">Test sous tension</h1>
      <p className="page-subtitle">
        Session {test.test_id} — moteur <strong>{motor.motor_id}</strong>
        {motor.designation ? ` — ${motor.designation}` : ''} (test hors tension validé ✓).
      </p>

      {message && (
        <div className={`alert alert-${message.type}`} role="status">
          {message.text}
        </div>
      )}

      {alreadyValidated ? (
        <section className="card">
          <h2>Test sous tension déjà validé</h2>
          <Link className="btn btn-primary btn-lg" to={`/test/analyse?testId=${testId}`}>
            Analyse →
          </Link>
        </section>
      ) : (
        <>
          {/* Tension d'alimentation : saisie UNE SEULE FOIS sur cette page,
              AVANT le choix du mode — OBLIGATOIRE (décision client). Le kit
              ne la mesure pas ; elle est enregistrée à la validation
              manuelle ou au passage en mode kit. */}
          <section className="card">
            <div className="form-group">
              <label htmlFor="st_supplyVoltage">
                Tension d'alimentation (V) <span className="required-star">*</span>
              </label>
              <input
                id="st_supplyVoltage"
                type="number"
                value={values.supplyVoltage}
                onChange={setValue('supplyVoltage')}
                placeholder="ex. 397"
              />
            </div>
          </section>

          {mode === null && (
            /* ===== Choix du mode (§6) — MANUEL à gauche · KIT à droite ===== */
            <section className="card">
              <h2>Comment réaliser le test sous tension ?</h2>
              <div className="home-actions home-actions-split">
                <div className="cta">
                  <button
                    type="button"
                    className="btn btn-primary btn-lg"
                    onClick={() => setMode('manual')}
                    disabled={busy}
                  >
                    Manuel
                  </button>
                </div>
                <div className="cta">
                  <button
                    type="button"
                    className="btn btn-accent btn-lg"
                    onClick={handleKit}
                    disabled={busy}
                  >
                    {busy ? '…' : 'Continuer avec le kit'}
                  </button>
                </div>
              </div>
            </section>
          )}

          {test.mode === 'auto' && mode === null && (
            /* Retour après acquisition kit : la tension est déjà saisie
               ci-dessus — il reste à VALIDER LE TEST. */
            <section className="card">
              <h2>Acquisition du kit terminée</h2>
              <p className="muted small">
                Vérifiez la tension d'alimentation saisie ci-dessus, puis validez le test.
              </p>
              <div className="home-actions">
                <button
                  type="button"
                  className="btn btn-primary btn-lg"
                  onClick={handleValidateManual}
                  disabled={busy}
                >
                  {busy ? 'Enregistrement…' : '✓ Valider le test'}
                </button>
              </div>
            </section>
          )}

          {mode === 'manual' && (
            <form onSubmit={handleValidateManual} noValidate>
              <section className="card">
                <h2>Mesures du test sous tension (saisie manuelle)</h2>
                <div className="form-grid">
                  {renderTextField({ id: 'current_a', label: 'Courant à vide I0 (A)', type: 'number', placeholder: 'ex. 41' })}
                  {renderTextField({ id: 'refMeterCl', label: 'Réf. appareil tension/courant (facultatif)', placeholder: 'ex. UT 208' })}
                  {renderTextField({ id: 'temp_bearing_de', label: 'Température palier côté accouplement (°C)', type: 'number', placeholder: 'ex. 48,5' })}
                  {renderTextField({ id: 'temp_bearing_nde', label: 'Température palier C.O.A (°C)', type: 'number', placeholder: 'ex. 51,2' })}
                  {renderTextField({ id: 'refMeterTemperature', label: 'Réf. appareil température (facultatif)', placeholder: 'ex. TKTL 10' })}
                  {renderTextField({ id: 'vibration_mm_s', label: 'Vibration (mm/s)', type: 'number', placeholder: 'ex. 1,6' })}
                </div>
              </section>

              <div className="home-actions">
                <button type="submit" className="btn btn-primary btn-lg" disabled={busy}>
                  {busy ? 'Enregistrement…' : '✓ Valider le test'}
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => setMode(null)} disabled={busy}>
                  ← Changer de mode
                </button>
              </div>
            </form>
          )}
        </>
      )}
    </>
  );
}
