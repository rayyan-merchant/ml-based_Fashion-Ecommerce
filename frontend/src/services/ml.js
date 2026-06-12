import analyticsAPI from '../api/analyticsAPI';
import forecastingAPI from '../api/forecastingAPI';
import nlpAPI from '../api/nlpAPI';
import segmentationAPI from '../api/segmentationAPI';
import sentimentAPI from '../api/sentimentAPI';

export const mlService = {
  sentimentSummary: (productId) => sentimentAPI.getProductSummary(productId),
  sentimentReviews: (productId, options = {}) =>
    sentimentAPI.getProductReviews(productId, options.sortBy, options.limit, options.skip),
  wordcloud: (productId) => nlpAPI.getProductWordcloud(productId),
  complaints: ({ categoryId, limit = 10 }) => nlpAPI.getCategoryComplaints(categoryId, limit),
  forecastArticle: (articleId) => forecastingAPI.getArticleForecast(articleId),
  forecastCategory: (categoryId) => forecastingAPI.getCategoryForecast(categoryId),
  forecasts: ({ limit = 50 } = {}) => forecastingAPI.getAllForecasts(limit),
  segments: () => segmentationAPI.getSegmentOverview(),
  segmentProfiles: () => segmentationAPI.getSegmentProfiles(),
  revenue: () => analyticsAPI.getRevenue(),
  trends: () => analyticsAPI.getTrends(),
  dashboard: () => analyticsAPI.getDashboardData()
};

export default mlService;
