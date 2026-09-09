// Petit utilitaire pour faire passer des paramètres entre pages
// (mode du diagnostic, kit_id, test en cours) en attendant une vraie
// gestion d'état (Context React) aux étapes suivantes.
//
// On utilise sessionStorage : les données survivent aux rechargements
// mais pas à la fermeture de l'onglet.

const KEY_MODE = 'ocp.test_mode';
const KEY_KIT = 'ocp.kit_id';
const KEY_TEST_ID = 'ocp.current_test_id';

export function setPendingMode(mode) { sessionStorage.setItem(KEY_MODE, mode); }
export function getPendingMode() { return sessionStorage.getItem(KEY_MODE) || 'manual'; }
export function clearPendingMode() { sessionStorage.removeItem(KEY_MODE); }

export function setPendingKitId(id) { id ? sessionStorage.setItem(KEY_KIT, id) : sessionStorage.removeItem(KEY_KIT); }
export function getPendingKitId() { return sessionStorage.getItem(KEY_KIT); }

export function setCurrentTestId(id) { id ? sessionStorage.setItem(KEY_TEST_ID, String(id)) : sessionStorage.removeItem(KEY_TEST_ID); }
export function getCurrentTestId() { const v = sessionStorage.getItem(KEY_TEST_ID); return v ? Number(v) : null; }
