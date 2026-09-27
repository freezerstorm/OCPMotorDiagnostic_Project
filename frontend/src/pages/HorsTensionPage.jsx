// ============================================================
// PAGE TEST HORS TENSION — ÉTAPES 3-4 DU PARCOURS (§5 du cahier).
//
// Test ENTIÈREMENT MANUEL : aucune connexion au kit n'est nécessaire.
//
//   1. Résistance des enroulements (R12, R23, R31)
//   2. Continuité des enroulements (appréciation globale Oui / Non)
//   3. Mesure d'isolement (tension de test + 6 mesures)
//
// Le bouton « VALIDER LE TEST » crée la session de diagnostic
// (moteur + mesures hors tension) puis la marque « hors tension
// validé » : l'étape suivante est le TEST SOUS TENSION.
// ============================================================
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { INSULATION_TEST_VOLTAGES } from '../constants';
import { createTest, validateOffline } from '../services/api';

const INSULATION_FIELDS = [
  { id: 'ph1_ph2', label: 'Ph1–Ph2', api: 'ph1_ph2_mohm' },
  { id: 'ph2_ph3', label: 'Ph2–Ph3', api: 'ph2_ph3_mohm' },
  { id: 'ph3_ph1', label: 'Ph3–Ph1', api: 'ph3_ph1_mohm' },
  { id: 'ph1_ground', label: 'Ph1–Masse', api: 'ph1_ground_mohm' },
  { id: 'ph2_ground', label: 'Ph2–Masse', api: 'ph2_ground_mohm' },
  { id: 'ph3_ground', label: 'Ph3–Masse', api: 'ph3_ground_mohm' },
];

const WINDING_FIELDS = [
  { id: 'r12', label: 'R12', api: 'r12_ohm' },
  { id: 'r23', label: 'R23', api: 'r23_ohm' },
  { id: 'r31', label: 'R31', api: 'r31_ohm' },
];

const INITIAL_VALUES = {
  refMeterResistance: '', refMeterInsulation: '',
  ...Object.fromEntries([...INSULATION_FIELDS, ...WINDING_FIELDS].map((f) => [f.id, ''])),
  insulationTestVoltage: '',
  continuity: '', // '' | 'oui' | 'non'
};

/** « 12,5 » → 12.5 ; champ vide → undefined (absent du JSON). */
function toNumberOrUndefined(value) {
  const text = String(value ?? '').trim().replace(',', '.');
  if (text === '') return undefined;
  const n = Number(text);
  return Number.isFinite(n) ? n : undefined;
}

export default function HorsTensionPage() {
  const navigate = useNavigate();
  const location = useLocation();
  // Moteur enregistré à l'étape précédente (page d'accueil)
  const motor = location.state?.motor ?? null;

  const [values, setValues] = useState(INITIAL_VALUES);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const setValue = (field) => (event) => {
    setValues({ ...values, [field]: event.target.value });
    setMessage(null);
  };

  // ===== VALIDER LE TEST (§5.4) =====
  const handleValidate = async (event) => {
    event.preventDefault();
    if (!motor) {
      setMessage({
        type: 'error',
        text: 'Aucun moteur enregistré : revenez à l’accueil pour saisir la fiche moteur.',
      });
      return;
    }

    // Mesures : on n'envoie que les champs remplis
    const winding = {};
    for (const field of WINDING_FIELDS) {
      const v = toNumberOrUndefined(values[field.id]);
      if (v !== undefined) winding[field.api] = v;
    }
    // Continuité : appréciation GLOBALE (un seul champ Oui/Non, §5.2)
    if (values.continuity === 'oui') winding.continuity_ok = true;
    if (values.continuity === 'non') winding.continuity_ok = false;
    if (values.refMeterResistance.trim() !== '') {
      winding.ref_meter_resistance = values.refMeterResistance.trim();
    }

    const insulation = {};
    for (const field of INSULATION_FIELDS) {
      const v = toNumberOrUndefined(values[field.id]);
      if (v !== undefined) insulation[field.api] = v;
    }
    // Tension de test d'isolement : OBLIGATOIRE dès qu'une mesure
    // d'isolement est saisie (la règle « 1 kΩ par volt » en dépend).
    const testVoltage = values.insulationTestVoltage === ''
      ? undefined
      : Number(values.insulationTestVoltage);
    if (Object.keys(insulation).length > 0 && testVoltage === undefined) {
      setMessage({
        type: 'error',
        text: 'La tension de test d’isolement est obligatoire lorsque des mesures d’isolement sont saisies (500 / 1000 / 2500 / 5000 V).',
      });
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    if (testVoltage !== undefined) insulation.test_voltage_v = testVoltage;
    if (values.refMeterInsulation.trim() !== '') {
      insulation.ref_meter_insulation = values.refMeterInsulation.trim();
    }

    setSaving(true);
    setMessage(null);
    try {
      // 1. Création de la session (le moteur inconnu est créé à ce moment)
      const test = await createTest({
        mode: 'manual',
        motor,
        measurements: { insulation, winding },
      });
      // 2. VALIDER LE TEST : la session passe à « hors tension validé »
      await validateOffline(test.test_id);
      // 3. Étape suivante : test sous tension
      navigate(`/test/sous-tension?testId=${test.test_id}`);
    } catch (error) {
      setSaving(false);
      setMessage({ type: 'error', text: `Validation impossible : ${error.message}` });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // ===== Rendu d'un champ texte =====
  const renderTextField = (field, opts = {}) => (
    <div className="form-group" key={field.id}>
      <label htmlFor={`ht_${field.id}`}>
        {field.label}
        {opts.required && <span className="required-star"> *</span>}
      </label>
      <input
        id={`ht_${field.id}`}
        type={opts.type ?? 'text'}
        value={values[field.id] ?? ''}
        onChange={setValue(field.id)}
        placeholder={opts.placeholder ?? '—'}
      />
    </div>
  );

  // ===== Pas de moteur → on ne peut pas tester =====
  if (!motor) {
    return (
      <section className="card">
        <h2>Aucun moteur enregistré</h2>
        <Link className="btn btn-primary" to="/">← Retour à l'accueil</Link>
      </section>
    );
  }

  return (
    <>
      <h1 className="page-title">Test hors tension</h1>
      <p className="page-subtitle">
        Moteur <strong>{motor.motor_id}</strong>
        {motor.designation ? ` — ${motor.designation}` : ''}
        {motor.service ? ` · ${motor.service}` : ''} — test manuel, sans le kit.
      </p>

      {message && (
        <div className={`alert alert-${message.type}`} role="status">
          {message.text}
        </div>
      )}

      <form onSubmit={handleValidate} noValidate>
        {/* ===== 5.1 Résistance des enroulements ===== */}
        <section className="card">
          <h2>1. Résistance des enroulements</h2>
          <div className="form-grid">
            {renderTextField({ id: 'r12', label: 'R12 (Ω)', type: 'number', placeholder: 'ex. 0,152' })}
            {renderTextField({ id: 'r23', label: 'R23 (Ω)', type: 'number', placeholder: 'ex. 0,152' })}
            {renderTextField({ id: 'r31', label: 'R31 (Ω)', type: 'number', placeholder: 'ex. 0,152' })}
            {renderTextField({ id: 'refMeterResistance', label: 'Réf. appareil de mesure (facultatif)', placeholder: 'ex. CA 6240' })}
          </div>
        </section>

        {/* ===== 5.2 Continuité des enroulements ===== */}
        <section className="card">
          <h2>2. Continuité des enroulements</h2>
          <div className="radio-row" role="radiogroup" aria-label="Continuité des enroulements">
            <label className="radio-option">
              <input
                type="radio"
                name="continuity"
                value="oui"
                checked={values.continuity === 'oui'}
                onChange={setValue('continuity')}
              />
              {' '}Oui
            </label>
            <label className="radio-option">
              <input
                type="radio"
                name="continuity"
                value="non"
                checked={values.continuity === 'non'}
                onChange={setValue('continuity')}
              />
              {' '}Non
            </label>
          </div>
        </section>

        {/* ===== 5.3 Mesure d'isolement ===== */}
        <section className="card">
          <h2>3. Mesure d'isolement</h2>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="ht_insulationTestVoltage">
                Tension de test d'isolement <span className="required-star">*</span>
              </label>
              <select
                id="ht_insulationTestVoltage"
                value={values.insulationTestVoltage}
                onChange={setValue('insulationTestVoltage')}
              >
                <option value="">— choisir —</option>
                {INSULATION_TEST_VOLTAGES.map((v) => (
                  <option key={v} value={String(v)}>{v} V</option>
                ))}
              </select>
            </div>
            {renderTextField({ id: 'refMeterInsulation', label: 'Réf. appareil de mesure (facultatif)', placeholder: 'ex. 16060086' })}
            {INSULATION_FIELDS.map((field) =>
              renderTextField({ id: field.id, label: `${field.label} (MΩ)`, type: 'number', placeholder: 'ex. 145' }),
            )}
          </div>
        </section>

        {/* ===== 5.4 VALIDER LE TEST ===== */}
        <div className="home-actions">
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>
            {saving ? 'Enregistrement…' : '✓ Valider le test'}
          </button>
          <Link className="btn btn-ghost" to="/">Annuler</Link>
        </div>
      </form>
    </>
  );
}
