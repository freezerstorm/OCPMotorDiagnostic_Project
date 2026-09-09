// Appels API liés aux moteurs.
import { api } from './apiClient';

export function listRecentMotors(limit = 50) {
  return api.get(`/motors?limit=${limit}`);
}

export function findMotor({ motorId, serialNumber } = {}) {
  const params = new URLSearchParams();
  if (motorId) params.set('motor_id', motorId);
  if (serialNumber) params.set('serial_number', serialNumber);
  return api.get(`/motors/find?${params.toString()}`);
}

export function upsertMotor(motor) {
  return api.post('/motors', motor);
}
