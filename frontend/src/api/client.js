/**
 * SAAQ API Client
 * Handles all communication with the FastAPI backend.
 * Same client can be used by React Native / mobile app.
 */
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }

  // Handle file downloads
  if (res.headers.get('content-type')?.includes('application/vnd')) {
    return res.blob();
  }

  return res.json();
}

export const api = {
  // Questions
  getQuestions: (version = '15Q') => request(`/questions/${version}`),

  // Intake
  submitIntake: (data) => request('/intake/submit', { method: 'POST', body: JSON.stringify(data) }),
  listIntakes: () => request('/intakes'),

  // Reports
  generateReport: (intakeId) => request('/reports/generate', { method: 'POST', body: JSON.stringify({ intake_id: intakeId }) }),
  getReport: (intakeId) => request(`/reports/${intakeId}`),
  downloadReport: (intakeId) => request(`/reports/${intakeId}/download`),
  listReports: () => request('/reports'),

  // Batch
  batchGenerate: (intakeIds) => request('/reports/batch', { method: 'POST', body: JSON.stringify({ intake_ids: intakeIds }) }),

  // Dashboard
  getDashboard: () => request('/dashboard'),

  // Health
  health: () => request('/health'),
};
