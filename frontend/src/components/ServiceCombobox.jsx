// ============================================================
// COMBOBOX « SERVICE » — UN SEUL champ pour choisir OU créer.
//
// Demande client (28/09/2026) :
//   - liste déroulante AVEC recherche (le technicien tape « KL » et
//     voit KL01 / KL02 / KL03 / KLB / KLR) ;
//   - si la désignation tapée n'existe pas : il peut l'utiliser pour
//     le moteur actuel ET l'ajouter à la liste (« ➕ Ajouter ») —
//     la création est PERSISTÉE en base par le parent (onAdd) ;
//   - pas de deuxième champ : la sélection et la création vivent ici.
//
// Le champ reste un simple texte : une valeur libre saisie sans
// « Ajouter » est utilisée telle quelle pour le moteur (données
// historiques acceptées), elle ne rentre juste pas au catalogue.
// ============================================================
import { useRef, useState } from 'react';

export default function ServiceCombobox({ id, label, value, onChange, options, onAdd }) {
  const [open, setOpen] = useState(false);
  // query = null → le champ affiche la valeur retenue (value) ;
  // pendant la saisie, query porte le texte en cours.
  const [query, setQuery] = useState(null);
  const [highlight, setHighlight] = useState(0);
  const closeTimer = useRef(null);

  const text = query ?? value ?? '';
  const needle = text.trim().toLowerCase();
  const matches =
    needle === ''
      ? options
      : options.filter((name) => name.toLowerCase().includes(needle));
  const exact = options.some((name) => name.toLowerCase() === needle);
  const canAdd = needle !== '' && !exact;

  const pick = (name) => {
    onChange(name);
    setQuery(null);
    setOpen(false);
  };

  const add = async () => {
    const name = text.trim();
    if (!name) return;
    setOpen(false);
    setQuery(null);
    await onAdd(name); // le parent crée le service en base (et affiche les erreurs)
    onChange(name); // utilisée pour le moteur actuel
  };

  const handleKeyDown = (event) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setOpen(true);
      setHighlight((h) => Math.min(h + 1, Math.max(matches.length - 1, 0)));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (event.key === 'Enter' && open) {
      // Entrée CHOISIT dans la liste (elle ne soumet pas le formulaire
      // tant que la liste est ouverte).
      event.preventDefault();
      if (canAdd && highlight >= matches.length) {
        add();
      } else if (matches[highlight]) {
        pick(matches[highlight]);
      }
    } else if (event.key === 'Escape') {
      setOpen(false);
      setQuery(null);
    }
  };

  return (
    <div className="form-group combobox">
      <label htmlFor={`f_${id}`}>{label}</label>
      <input
        id={`f_${id}`}
        type="text"
        autoComplete="off"
        value={text}
        placeholder="Rechercher ou saisir un service…"
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
          setHighlight(0);
        }}
        onFocus={() => {
          clearTimeout(closeTimer.current);
          setOpen(true);
          setHighlight(0);
        }}
        onBlur={() => {
          closeTimer.current = setTimeout(() => {
            setOpen(false);
            setQuery(null);
          }, 120);
        }}
        onKeyDown={handleKeyDown}
      />
      {open && (
        <ul className="combobox-menu" role="listbox" aria-label={label}>
          {matches.map((name, i) => (
            <li key={name}>
              <button
                type="button"
                className={i === highlight ? 'combobox-item is-active' : 'combobox-item'}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => pick(name)}
              >
                {name}
              </button>
            </li>
          ))}
          {matches.length === 0 && !canAdd && (
            <li className="combobox-empty">Aucun service correspondant.</li>
          )}
          {canAdd && (
            <li>
              <button
                type="button"
                className="combobox-item combobox-add"
                onMouseDown={(event) => event.preventDefault()}
                onClick={add}
              >
                ➕ Ajouter « {text.trim()} » à la liste
              </button>
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
