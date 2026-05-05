/**
 * SAAQ API Client v2 — with auth headers
 */
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

function getToken() {
  try {
    const auth = localStorage.getItem('saaq_auth')
    if (auth) return JSON.parse(auth).access_token
  } catch {}
  return null
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`
  const token = getToken()
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(url, { headers, ...options })

  if (res.status === 401) {
    localStorage.removeItem('saaq_auth')
    window.dispatchEvent(new Event('saaq_logout'))
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `API error: ${res.status}`)
  }

  if (res.headers.get('content-type')?.includes('application/vnd')) return res.blob()
  return res.json()
}

export const api = {
  // auth
  signup: (data) => request('/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request('/auth/me'),

  // grants
  grantFreeReport: (email, productType) => request('/admin/grant-free', { method: 'POST', body: JSON.stringify({ email, product_type: productType }) }),
  checkGrant: () => request('/check-grant'),
  redeemGrant: (grantId) => request('/redeem-grant', { method: 'POST', body: JSON.stringify({ grant_id: grantId }) }),

  // pricing (public)
  getPricing: () => request('/pricing'),

  // checkout
  createCheckout: (productType) => request('/checkout', { method: 'POST', body: JSON.stringify({ product_type: productType }) }),
  verifyPayment: (sessionId) => request('/checkout/verify', { method: 'POST', body: JSON.stringify({ session_id: sessionId }) }),

  // questions
  getQuestions: (version = '15Q') => request(`/questions/${version}`),

  // intake
  submitIntake: (data) => request('/intake/submit', { method: 'POST', body: JSON.stringify(data) }),
  listIntakes: () => request('/intakes'),
  myIntakes: () => request('/my/intakes'),

  // reports
  generateReport: (intakeId) => request('/reports/generate', { method: 'POST', body: JSON.stringify({ intake_id: intakeId }) }),
  getReport: (intakeId) => request(`/reports/${intakeId}`),
  downloadReport: (intakeId) => request(`/reports/${intakeId}/download`),
  listReports: () => request('/reports'),
  myReports: () => request('/my/reports'),

  // batch
  batchGenerate: (intakeIds) => request('/reports/batch', { method: 'POST', body: JSON.stringify({ intake_ids: intakeIds }) }),

  // admin
  adminDashboard: () => request('/admin/dashboard'),
  adminSettings: () => request('/admin/settings'),
  updatePrice: (key, amount, label) => request('/admin/settings/price', { method: 'POST', body: JSON.stringify({ key, amount, label }) }),
  adminUsers: () => request('/admin/users'),
  grantAdmin: (email) => request('/admin/grant-admin', { method: 'POST', body: JSON.stringify({ email }) }),
  revokeAdmin: (email) => request('/admin/revoke-admin', { method: 'POST', body: JSON.stringify({ email }) }),
  adminPayments: () => request('/admin/payments'),

  // legacy dashboard
  getDashboard: () => request('/dashboard'),
  health: () => request('/health'),
}
