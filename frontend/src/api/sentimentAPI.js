import api from './api';

export const sentimentAPI = {
  getProductSummary: (productId) => api.get(`/sentiment/product/${productId}/summary`),

  getProductReviews: (productId, sortBy = 'newest', limit = 20, skip = 0) =>
    api.get(`/sentiment/product/${productId}/reviews`, {
      params: { order: sortBy, limit, skip }
    }),

  getDistribution: (productId) => api.get(`/sentiment/product/${productId}/distribution`),

  predict: (text, model = 'svm') => api.post('/sentiment/predict', { text, model })
};

export default sentimentAPI;
