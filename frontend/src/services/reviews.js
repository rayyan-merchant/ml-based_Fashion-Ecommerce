import { reviews } from '../api/api';
import sentimentAPI from '../api/sentimentAPI';
import nlpAPI from '../api/nlpAPI';

export const reviewsService = {
  list: ({ skip = 0, limit = 100 } = {}) => reviews.getAll(skip, limit),
  get: (reviewId) => reviews.getById(reviewId),
  byProduct: (productId, { skip = 0, limit = 5, sortBy = 'newest' } = {}) =>
    sentimentAPI.getProductReviews(productId, sortBy, limit, skip),
  create: (payload) => reviews.create(payload),
  update: (reviewId, payload) => reviews.update(reviewId, payload),
  remove: (reviewId) => reviews.delete(reviewId),
  stats: (productId) => reviews.getArticleStats(productId),
  similar: (reviewId, limit = 5) => nlpAPI.getSimilarReviews(reviewId, limit)
};

export default reviewsService;
