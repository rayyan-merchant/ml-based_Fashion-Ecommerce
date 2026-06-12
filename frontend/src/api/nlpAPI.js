import api from './api';

export const nlpAPI = {
  getSimilarReviews: (reviewId, topK = 5) =>
    api.get(`/reviews/${reviewId}/similar`, { params: { k: topK } }),

  getSimilarProducts: (productId, topK = 8) =>
    api.get(`/products/${productId}/similar`, { params: { k: topK } }),

  getProductWordcloud: async (productId) => {
    const response = await api.get(`/products/${productId}/wordcloud/base64`);
    return {
      ...response,
      data: {
        ...response.data,
        image: response.data?.image || response.data?.wordcloud
      }
    };
  },

  getCategoryComplaints: async (categoryId, topK = 10) => {
    const response = await api.get(`/categories/${categoryId}/top-complaints`, {
      params: { top_n: topK }
    });
    const rawComplaints = response.data?.complaints || response.data?.top_complaints || [];
    const complaints = rawComplaints.map((item, index) => {
      if (typeof item === 'string') {
        return { id: index, text: item };
      }

      return {
        ...item,
        id: item.id || `${categoryId}-${index}`,
        text: item.text || item.complaint || item.issue || item.keyword || item.phrase || `Complaint ${index + 1}`,
        tfidf_score: item.tfidf_score ?? item.score
      };
    });

    return {
      ...response,
      data: {
        ...response.data,
        complaints,
        example_reviews: response.data?.example_reviews || response.data?.examples || []
      }
    };
  }
};

export default nlpAPI;
