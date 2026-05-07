import axios from 'axios';

const BASE = '/api';

export const api = {
  triggerIngestion: (limit = 20) =>
    axios.post(`${BASE}/ingestion/trigger`, { limit }),

  recomputeScores: () =>
    axios.post(`${BASE}/scores/recompute`),

  getRecommendations: (params = {}) =>
    axios.get(`${BASE}/recommendations`, { params }),

  getRecommendationDetail: (id) =>
    axios.get(`${BASE}/recommendations/${id}`),

  getSummary: (window_days = 90) =>
    axios.get(`${BASE}/reports/summary`, { params: { window_days } }),

  getHitRateByMonth: (window_days = 90) =>
    axios.get(`${BASE}/reports/hit-rate-by-month`, { params: { window_days } }),

  getTopRecommendations: (limit = 5, window_days = 90) =>
    axios.get(`${BASE}/reports/top`, { params: { limit, window_days } }),

  getWorstRecommendations: (limit = 5, window_days = 90) =>
    axios.get(`${BASE}/reports/worst`, { params: { limit, window_days } }),

  getFullReport: (window_days = 90) =>
    axios.get(`${BASE}/reports/full`, { params: { window_days } }),
};
