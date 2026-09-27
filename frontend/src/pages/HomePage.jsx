// ============================================================
// PAGE ACCUEIL — ÉTAPE 1-2 DU PARCOURS (demande client).
//
// Le formulaire du MOTEUR est directement sur la page d'accueil :
// informations constructeur, ID, service/environnement, etc.
//
// Deux boutons sous le formulaire (disposition demandée par le
// client : REGISTRE à gauche, TEST à droite) :
//   • TEST     → valide les informations et va au test manuel
//                (partie HORS TENSION : résistances, continuité,
//                isolement) ;
//   • REGISTRE → ouvre la page du REGISTRE NUMÉRIQUE des moteurs
//                (20 colonnes du fichier Excel). Le brouillon du
//                formulaire est conservé : le retour au formulaire
//                ne fait perdre aucune saisie.
//
// Moteur déjà connu → champs auto-remplis et modifiables (§9 du
// cahier des charges). Les informations sont enregistrées en base
// à la validation du TEST HORS TENSION (étape suivante).
// ============================================================
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { SERVICE_OPTIONS } from '../constants';
import { fetchMotor } from '../services/api';

// Conversion des champs de formulaire (camelCase) vers les champs API
// (snake_case). Le MATRICULE est l'identifiant du moteur (décision
// client : l'« ID moteur » n'est plus utilisé) — traité à part.
const MOTOR_FIELD_MAP = {
  designation: 'designation',
  brand: 'brand',
  model: 'model',
  serialNumber: 'serial_number',
  ratedPower: 'rated_power_kw',
  ratedVoltage: 'rated_voltage_v',
  ratedCurrent: 'rated_current_a',
  speed: 'rated_speed_rpm',
  cosPhi: 'cos_phi',
  coupling: 'coupling',
  service: 'service',
  diOt: 'di_ot',
};

const INITIAL_VALUES = {
  matricule: '', designation: '', brand: '', model: '',
  serialNumber: '', ratedPower: '', ratedVoltage: '', ratedCurrent: '',
  speed: '', cosPhi: '', coupling: '', service: '', diOt: '',
};

// Brouillon du formulaire conservé pendant la navigation (ex. consulter
// le REGISTRE puis revenir) : ce qui est déjà saisi n'est jamais perdu.
const DRAFT_KEY = 'ocp.motor-form-draft';

function loadDraft() {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY);
    if (!raw) return INITIAL_VALUES;
    return { ...INITIAL_VALUES, ...JSON.parse(raw) };
  } catch {
    return INITIAL_VALUES;
  }
}

/** « 12,5 » → 12.5 ; champ vide → undefined (absent du JSON). */
function toNumberOrUndefined(value) {
  const text = String(value ?? '').trim().replace(',', '.');
  if (text === '') return undefined;
  const n = Number(text);
  return Number.isFinite(n) ? n : undefined;
}

const NUMERIC_API_KEYS = new Set([
  'rated_power_kw', 'rated_voltage_v', 'rated_current_a', 'rated_speed_rpm', 'cos_phi',
]);

export default function HomePage() {
  const navigate = useNavigate();
  const [values, setValues] = useState(loadDraft);
  const [lookupState, setLookupState] = useState('idle'); // idle|searching|found|notfound
  const [message, setMessage] = useState(null); // { type: 'error'|'success'|'info', text }

  // Brouillon → sessionStorage : consulter le registre puis revenir
  // retrouve le formulaire tel que le technicien l'a laissé.
  useEffect(() => {
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify(values));
  }, [values]);

  const setValue = (field) => (event) => {
    setValues({ ...values, [field]: event.target.value });
    setMessage(null);
  };

  // ===== Recherche du moteur (auto-remplissage §9) =====
  const handleLookup = async () => {
    const matricule = values.matricule.trim();
    if (!matricule) return;

    setLookupState('searching');
    setMessage(null);
    try {
      const motor = await fetchMotor(matricule);
      // Moteur connu → les informations enregistrées remplissent la fiche
      const next = { ...values };
      for (const [formKey, apiKey] of Object.entries(MOTOR_FIELD_MAP)) {
        if (motor[apiKey] !== null && motor[apiKey] !== undefined) {
          next[formKey] = String(motor[apiKey]);
        }
      }
      setValues(next);
      setLookupState('found');
      setMessage({
        type: 'success',
        text: `Moteur ${matricule} déjà connu : informations reprises ci-dessus. Vérifiez-les, elles sont modifiables.`,
      });
    } catch {
      setLookupState('notfound');
      setMessage({
        type: 'info',
        text: `Moteur ${matricule} inconnu : la fiche sera créée lors de l'enregistrement du test.`,
      });
    }
  };

  // ===== Bouton TEST → étape suivante (test hors tension) =====
  const handleTest = (event) => {
    event.preventDefault();
    const matricule = values.matricule.trim();
    if (!matricule) {
      setMessage({ type: 'error', text: 'Le matricule est obligatoire pour démarrer un test.' });
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    // Fiche moteur : le matricule est l'identifiant du moteur
    const motor = { motor_id: matricule, matricule };
    for (const [formKey, apiKey] of Object.entries(MOTOR_FIELD_MAP)) {
      const value = String(values[formKey] ?? '').trim();
      if (value !== '') {
        motor[apiKey] = NUMERIC_API_KEYS.has(apiKey) ? toNumberOrUndefined(value) : value;
      }
    }

    // Les informations voyagent vers l'étape suivante ; elles seront
    // enregistrées en base à la validation du TEST HORS TENSION.
    // Le brouillon est purgé : la saisie est maintenant engagée dans
    // la session de diagnostic (un nouveau formulaire repart à vide).
    sessionStorage.removeItem(DRAFT_KEY);
    navigate('/test/hors-tension', { state: { motor } });
  };

  // ===== Rendu d'un champ texte =====
  const renderTextField = (field, opts = {}) => (
    <div className="form-group" key={field.id}>
      <label htmlFor={`f_${field.id}`}>
        {field.label}
        {opts.required && <span className="required-star"> *</span>}
      </label>
      <input
        id={`f_${field.id}`}
        type={opts.type ?? 'text'}
        value={values[field.id] ?? ''}
        onChange={setValue(field.id)}
        placeholder={opts.placeholder ?? '—'}
      />
    </div>
  );

  return (
    <>
      <h1 className="page-title">Diagnostic de moteurs électriques</h1>
      {message && (
        <div className={`alert alert-${message.type}`} role="status">
          {message.text}
        </div>
      )}

      <form onSubmit={handleTest} noValidate>
        <section className="card">
          <h2>Fiche moteur</h2>
          <div className="lookup-row">
            <div className="form-group lookup-input">
              <label htmlFor="f_matricule">Matricule <span className="required-star">*</span></label>
              <input
                id="f_matricule"
                type="text"
                value={values.matricule}
                onChange={setValue('matricule')}
                placeholder="Ex. : M607485"
              />
            </div>
            <button
              type="button"
              className="btn btn-outline"
              onClick={handleLookup}
              disabled={!values.matricule.trim() || lookupState === 'searching'}
            >
              {lookupState === 'searching' ? 'Recherche…' : '↺ Récupérer le moteur'}
            </button>
          </div>

          <div className="form-grid motor-grid">
            {renderTextField({ id: 'designation', label: 'Désignation / Matériel' })}
            {renderTextField({ id: 'brand', label: 'Marque' })}
            {renderTextField({ id: 'model', label: 'Modèle' })}
            {renderTextField({ id: 'serialNumber', label: 'N° de fabrication' })}
            {renderTextField({ id: 'ratedPower', label: 'Puissance nominale P (kW)', type: 'number', placeholder: 'ex. 30' })}
            {renderTextField({ id: 'ratedVoltage', label: 'Tension nominale U (V)', type: 'number', placeholder: 'ex. 400' })}
            {renderTextField({ id: 'ratedCurrent', label: 'Courant nominal In (A)', type: 'number', placeholder: 'ex. 45' })}
            {renderTextField({ id: 'speed', label: 'Vitesse nominale N (tr/min)', type: 'number', placeholder: 'ex. 1480' })}
            {renderTextField({ id: 'cosPhi', label: 'Cos φ', type: 'number', placeholder: 'ex. 0.85' })}

            <div className="form-group">
              <label htmlFor="f_coupling">Couplage</label>
              <select id="f_coupling" value={values.coupling} onChange={setValue('coupling')}>
                <option value="">—</option>
                <option value="Étoile (Y)">Étoile (Y)</option>
                <option value="Triangle (Δ)">Triangle (Δ)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="f_service">Service / Environnement</label>
              <select id="f_service" value={values.service} onChange={setValue('service')}>
                <option value="">—</option>
                {SERVICE_OPTIONS.map((service) => (
                  <option key={service} value={service}>{service}</option>
                ))}
              </select>
            </div>

            {renderTextField({ id: 'diOt', label: 'DI / OT' })}
          </div>
        </section>

        {/* ===== Boutons du parcours : REGISTRE à gauche · TEST à droite ===== */}
        <div className="home-actions home-actions-split">
          <div className="cta">
            <Link className="btn btn-accent btn-lg" to="/registre">
              Registre
            </Link>
          </div>

          <div className="cta">
            <button type="submit" className="btn btn-primary btn-lg">
              Test →
            </button>
          </div>
        </div>
      </form>
    </>
  );
}
