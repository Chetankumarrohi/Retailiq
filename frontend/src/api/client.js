const API_BASE = (import.meta.env && import.meta.env.VITE_API_BASE_URL) ? import.meta.env.VITE_API_BASE_URL : '/api';

async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

function buildQuery(params = {}) {
  const q = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== null && val !== '' && val !== 'all') {
      q.set(key, val);
    }
  }
  const str = q.toString();
  return str ? `?${str}` : '';
}

export const api = {
  // Health
  getHealth: () => apiFetch('/health'),

  // Metadata
  getStores: () => apiFetch('/stores'),
  getDepartments: (storeId) =>
    apiFetch(`/departments${buildQuery({ store_id: storeId })}`),

  // Dashboard
  getSummary: (storeId, deptId) =>
    apiFetch(`/dashboard/summary${buildQuery({ store_id: storeId, dept_id: deptId })}`),

  getSalesTrend: (params = {}) =>
    apiFetch(`/dashboard/sales-trend${buildQuery(params)}`),

  getStoreRanking: (limit = 15, deptId) =>
    apiFetch(`/dashboard/store-ranking${buildQuery({ limit, dept_id: deptId })}`),

  getDeptRanking: (limit = 15, storeId) =>
    apiFetch(`/dashboard/department-ranking${buildQuery({ limit, store_id: storeId })}`),

  getPromoEffectiveness: (storeId, deptId) =>
    apiFetch(`/dashboard/promotion-effectiveness${buildQuery({ store_id: storeId, dept_id: deptId })}`),

  getHolidayAnalysis: (storeId, deptId) =>
    apiFetch(`/dashboard/holiday-analysis${buildQuery({ store_id: storeId, dept_id: deptId })}`),

  getStoreTypes: (deptId) =>
    apiFetch(`/dashboard/store-types${buildQuery({ dept_id: deptId })}`),

  // Forecast
  postForecast: (storeId, deptId, horizonWeeks = 4) =>
    apiFetch('/forecast', {
      method: 'POST',
      body: JSON.stringify({ store_id: storeId, dept_id: deptId, horizon_weeks: horizonWeeks }),
    }),

  // Assistant
  postChat: (message) =>
    apiFetch('/assistant/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
};
