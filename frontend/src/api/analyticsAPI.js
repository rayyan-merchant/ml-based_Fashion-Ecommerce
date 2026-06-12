import { mlApi } from './api';

export const analyticsAPI = {
  getRevenue: () => mlApi.get('/analytics/revenue'),

  getTrends: (limit = 50) => mlApi.get('/analytics/trends', { params: { limit } }),

  getMonthlyGrowth: () => mlApi.get('/analytics/growth/monthly'),

  getStockoutRisk: (limit = 50) =>
    mlApi.get('/analytics/stockout-risk', { params: { limit } }),

  getProductLifecycle: (limit = 50) =>
    mlApi.get('/analytics/lifecycle', { params: { limit } }),

  getAggregatedData: (period = 'weekly') =>
    mlApi.get('/analytics/aggregate', { params: { period } }),

  getDashboardData: async () => {
    const requests = {
      revenue: analyticsAPI.getRevenue(),
      trends: analyticsAPI.getTrends(),
      growth: analyticsAPI.getMonthlyGrowth(),
      stockout: analyticsAPI.getStockoutRisk(),
      lifecycle: analyticsAPI.getProductLifecycle(),
      aggregate: analyticsAPI.getAggregatedData()
    };

    const entries = await Promise.allSettled(Object.entries(requests).map(async ([key, request]) => {
      const response = await request;
      return [key, response.data];
    }));

    const data = {};
    const errors = [];
    entries.forEach(result => {
      if (result.status === 'fulfilled') {
        const [key, value] = result.value;
        data[key] = value;
      } else {
        errors.push(result.reason?.response?.data?.detail || result.reason?.message || 'Unknown analytics error');
      }
    });

    return { data: { ...data, _errors: errors } };
  }
};

export default analyticsAPI;
