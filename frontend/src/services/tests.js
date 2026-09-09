// Appels API liés aux diagnostics (tests).
import { api } from './apiClient';

export function listRecentTests(limit = 6) {
  return api.get(`/tests/recent?limit=${limit}`);
}

export function listAllTests() {
  return api.get('/tests');
}

export function getTest(id) {
  return api.get(`/tests/${id}`);
}

export function createTest({ mode, motor, kitId }) {
  return api.post('/tests', {
    mode,
    motor,
    kit_id: kitId || null,
  });
}

export function updateTestStatus(id, status) {
  return api.patch(`/tests/${id}/status?status=${status}`, {});
}
