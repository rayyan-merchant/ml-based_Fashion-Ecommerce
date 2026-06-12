import api from './api';

const extractRecommendationItems = (data) => (
  data?.recommendations ||
  data?.trending_items ||
  data?.similar_items ||
  data?.products ||
  (Array.isArray(data) ? data : [])
);

const enrichWithProductDetails = async (items) => {
  const normalized = extractRecommendationItems(items);
  const results = await Promise.allSettled(
    normalized.map(async (item) => {
      const articleId = item.article_id || item.product_id || item.id;
      if (!articleId || item.prod_name || item.name) return item;

      const response = await api.get(`/articles/${articleId}`);
      return {
        ...item,
        ...response.data,
        recommendation_score: item.score ?? item.similarity
      };
    })
  );

  return results.map((result, index) => (
    result.status === 'fulfilled'
      ? result.value
      : {
        ...normalized[index],
        prod_name: `Article ${normalized[index]?.article_id || normalized[index]?.product_id || ''}`.trim()
      }
  ));
};

const withEnrichedItems = async (response, targetKey) => ({
  data: {
    ...response.data,
    [targetKey]: await enrichWithProductDetails(response.data)
  }
});

export const recommendationAPI = {
  getPersonalized: async (customerId, limit = 12) => {
    const response = await api.get(`/hybrid-recommendations/personalized/${customerId}`, {
      params: { limit }
    });
    return withEnrichedItems(response, 'recommendations');
  },

  getCustomersAlsoBought: async (customerId, limit = 12) => {
    const response = await api.get(`/hybrid-recommendations/customers-also-bought/${customerId}`, {
      params: { limit }
    });
    return withEnrichedItems(response, 'recommendations');
  },

  getBasedOnInteractions: async (customerId, limit = 12) => {
    const response = await api.get(`/hybrid-recommendations/based-on-interactions/${customerId}`, {
      params: { limit }
    });
    return withEnrichedItems(response, 'recommendations');
  },

  getTrending: async (limit = 12) => {
    const response = await api.get('/hybrid-recommendations/trending', {
      params: { limit }
    });
    return withEnrichedItems(response, 'products');
  },

  getSimilarItems: async (productId, limit = 12) => {
    const response = await api.get(`/hybrid-recommendations/you-may-also-like-product/${productId}`, {
      params: { limit }
    });
    return withEnrichedItems(response, 'products');
  },

  getPopularInCategory: async (categoryId, limit = 12) => {
    const response = await api.get('/hybrid-recommendations/trending', {
      params: { limit, category_id: categoryId }
    });
    return withEnrichedItems(response, 'products');
  },

  getCartBased: async (customerId, limit = 8) => {
    const response = await api.get(`/hybrid-recommendations/based-on-interactions/${customerId}`, {
      params: { limit }
    });
    return withEnrichedItems(response, 'recommendations');
  }
};

export default recommendationAPI;
