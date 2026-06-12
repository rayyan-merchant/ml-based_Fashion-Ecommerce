import { mlApi } from './api';

export const forecastingAPI = {
  getArticleForecast: (articleId, horizon = 30) =>
    mlApi.get(`/forecasting/article/${articleId}`, { params: { horizon } }),

  getCategoryForecast: (categoryId, horizon = 30) =>
    mlApi.get(`/forecasting/category/${categoryId}`, { params: { horizon } }),

  getAllForecasts: (limit = 50) =>
    mlApi.get('/forecasting/all', { params: { limit } }),

  runPipeline: () => mlApi.post('/forecasting/pipeline/run')
};

export default forecastingAPI;
