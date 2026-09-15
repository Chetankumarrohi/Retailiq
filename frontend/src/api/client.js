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

export const api = {
  // Health
  getHealth: () => apiFetch('/health'),

  // Metadata
  getStores: () => apiFetch('/stores'),
  getDepartments: (storeId) => apiFetch(`/departments${storeId ? `?store_id=${storeId}` : ''}`),

  // Dashboard
  getSummary: () => apiFetch('/dashboard/summary'),
  getSalesTrend: (params = {}) => {
    const q = new URLSearchParams();
    if (params.granularity) q.set('granularity', params.granularity);
    if (params.store_id) q.set('store_id', params.store_id);
    if (params.dept_id) q.set('dept_id', params.dept_id);
    return apiFetch(`/dashboard/sales-trend?${q.toString()}`);
  },
  getStoreRanking: (limit = 15) => apiFetch(`/dashboard/store-ranking?limit=${limit}`),
  getDeptRanking: (limit = 15, storeId) =>
    apiFetch(`/dashboard/department-ranking?limit=${limit}${storeId ? `&store_id=${storeId}` : ''}`),
  getPromoEffectiveness: (storeId) =>
    apiFetch(`/dashboard/promotion-effectiveness${storeId ? `?store_id=${storeId}` : ''}`),
  getHolidayAnalysis: (storeId) =>
    apiFetch(`/dashboard/holiday-analysis${storeId ? `?store_id=${storeId}` : ''}`),
  getStoreTypes: () => apiFetch('/dashboard/store-types'),

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
