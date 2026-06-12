import { adminAuth, articles, categories, customers, events, orders, reviews } from '../api/api';
import analyticsAPI from '../api/analyticsAPI';
import forecastingAPI from '../api/forecastingAPI';
import recommendationAPI from '../api/recommendationAPI';
import segmentationAPI from '../api/segmentationAPI';

export const adminService = {
  dashboard: () => analyticsAPI.getDashboardData(),
  admins: () => adminAuth.listAdmins(),
  logs: (limit = 100) => adminAuth.getLogs(limit),
  products: ({ skip = 0, limit = 200 } = {}) => articles.getAll(skip, limit),
  categories: () => categories.getAll(),
  orders: ({ skip = 0, limit = 200 } = {}) => orders.getAll(skip, limit),
  customers: ({ skip = 0, limit = 200 } = {}) => customers.getAll(skip, limit),
  reviews: ({ skip = 0, limit = 200 } = {}) => reviews.getAll(skip, limit),
  events: ({ skip = 0, limit = 200 } = {}) => events.getAll(skip, limit),
  recommendations: {
    trending: (limit = 12) => recommendationAPI.getTrending(limit)
  },
  ml: {
    forecasts: (limit = 50) => forecastingAPI.getAllForecasts(limit),
    segments: () => segmentationAPI.getSegmentOverview()
  }
};

export default adminService;
