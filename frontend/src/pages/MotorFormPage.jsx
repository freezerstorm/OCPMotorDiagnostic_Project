import { useEffect, useState } from 'react';
import { SectionIntro } from '../components';
import { createTest } from '../services/tests';
import { findMotor } from '../services/motors';
import { getPendingKitId, getPendingMode, setCurrentTestId } from '../state/session';

// Champs du formulaire. Le schéma est repris du CDC (point 9) sans ajouter
// de champs inutiles. Les champs de mesure manuelle (isolement + résistances)
// seront ajoutés à l'étape 5.
const INITIAL = {
  motor_id: '', serial_number: '', designation: '', brand: '', model: '',
  manufacturer_number: '', rated_power_kw: '', rated_voltage_v: '',
  rated_current_a: '', rated_speed_rpm: '', cos_phi: '', coupling: '',
  service: '', di_ot: '',
};

export function MotorFormPage({ navigate }) {
  const mode = getPendingMode();
  const kitId = getPendingKitId();
  const [form, setForm] = useState(INITIAL);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [lookupStatus, setLookupStatus] = useState('');

  // Auto-remplissage quand l'utilisateur saisit un motor_id connu
  useEffect(() => {
    if (!form.motor_id || form.motor_id.length < 2) return;
    const t = setTimeout(async () => {
      try {
        const found = await findMotor({ motorId: form.motor_id });
        if (found) {
          setForm((f) => ({ ...INITIAL, ...cleanForForm(found) }));
          setLookupStatus(`Moteur ${found.motor_id} retrouvé dans l'historique — champs pré-remplis.`);
        } else {
          setLookupStatus('');
        }
      } catch (_) { /* silence */ }
    }, 400);
    return () => clearTimeout(t);
  }, [form.motor_id]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const toNum = (v) => (v === '' || v === null || v === undefined ? null : Number(v));

  const onSubmit = async () => {
    setSubmitting(true); setError(null);
    try {
      const motorPayload = {
        motor_id: form.motor_id || null,
        serial_number: form.serial_number || null,
        designation: form.designation || null,
        brand: form.brand || null,
        model: form.model || null,
        manufacturer_number: form.manufacturer_number || null,
        rated_power_kw: toNum(form.rated_power_kw),
        rated_voltage_v: toNum(form.rated_voltage_v),
        rated_current_a: toNum(form.rated_current_a),
        rated_speed_rpm: toNum(form.rated_speed_rpm),
        cos_phi: toNum(form.cos_phi),
        coupling: form.coupling || null,
        service: form.service || null,
        di_ot: form.di_ot || null,
      };
      const test = await createTest({ mode, motor: motorPayload, kitId });
      setCurrentTestId(test.id);
      if (mode === 'auto') {
        navigate('acquisition');
      } else {
        // Mode manuel : direction directe vers la saisie des mesures (étape 5).
        // Pour l'instant, on envoie vers Analysis qui sera complété à l'étape 11.
        navigate('analysis');
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <SectionIntro
        eyebrow={`MODE : ${mode === 'auto' ? 'AUTOMATIQUE' : 'MANUEL'} · FICHE MOTEUR`}
        title="Identifier le moteur"
        text="Une seule fiche de diagnostic est utilisée pour les deux modes. Si l'ID moteur existe déjà, les champs connus sont pré-remplis automatiquement."
      />

      {mode === 'auto' && (
        <div className="info-banner">Kit connecté : <strong>{kitId || '—'}</strong>. Les mesures de température, courant et vibration seront acquises automatiquement (~60 s).</div>
      )}

      {lookupStatus && <div className="info-banner ok">{lookupStatus}</div>}
      {error && <div className="info-banner bad">Erreur : {error}</div>}

      <div className="form-card">
        <div className="form-section">
          <h3>Identification</h3>
          <div className="form-grid">
            <LabelInput label="ID moteur *" value={form.motor_id} onChange={set('motor_id')} placeholder="ex: MTR-2024-0142" />
            <LabelInput label="Matricule" value={form.serial_number} onChange={set('serial_number')} placeholder="ex: 7845-21-9" />
            <LabelInput label="Désignation" value={form.designation} onChange={set('designation')} placeholder="ex: Moteur pompe de relevage" />
            <LabelInput label="Marque" value={form.brand} onChange={set('brand')} placeholder="Leroy-Somer" />
            <LabelInput label="Modèle" value={form.model} onChange={set('model')} placeholder="LS200L" />
            <LabelInput label="N° de fabrication" value={form.manufacturer_number} onChange={set('manufacturer_number')} />
            <LabelInput label="Service / Département" value={form.service} onChange={set('service')} placeholder="Phosphore-Safi" />
            <LabelInput label="DI / OT" value={form.di_ot} onChange={set('di_ot')} placeholder="DI-2024-071" />
          </div>
        </div>

        <div className="form-section">
          <h3>Plaque signalétique (données de référence)</h3>
          <div className="form-grid">
            <LabelInput label="Puissance nominale (kW)" type="number" value={form.rated_power_kw} onChange={set('rated_power_kw')} />
            <LabelInput label="Tension nominale (V)" type="number" value={form.rated_voltage_v} onChange={set('rated_voltage_v')} />
            <LabelInput label="Courant nominal In (A)" type="number" value={form.rated_current_a} onChange={set('rated_current_a')} />
            <LabelInput label="Vitesse (tr/min)" type="number" value={form.rated_speed_rpm} onChange={set('rated_speed_rpm')} />
            <LabelInput label="cos φ" type="number" step="0.01" value={form.cos_phi} onChange={set('cos_phi')} />
            <LabelInput label="Couplage" value={form.coupling} onChange={set('coupling')} placeholder="Étoile / Triangle / Δ / Y" />
          </div>
        </div>

        <div className="form-actions">
          <button className="button secondary" onClick={() => navigate('home')}>Annuler</button>
          <button className="button primary" onClick={onSubmit} disabled={submitting || !form.motor_id}>
            {submitting ? 'Création…' : 'Continuer'} <span>→</span>
          </button>
        </div>
      </div>
    </>
  );
}

function LabelInput({ label, value, onChange, type = 'text', placeholder, step }) {
  return (
    <label>
      {label}
      <input type={type} step={step} value={value ?? ''} onChange={onChange} placeholder={placeholder} />
    </label>
  );
}

function cleanForForm(motor) {
  // Les nombres de l'API sont des nombres ; on les convertit en string pour <input value>.
  const out = { ...motor };
  ['rated_power_kw', 'rated_voltage_v', 'rated_current_a', 'rated_speed_rpm', 'cos_phi'].forEach((k) => {
    if (out[k] != null) out[k] = String(out[k]);
  });
  return out;
}
