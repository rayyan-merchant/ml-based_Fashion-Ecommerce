import recommendationAPI from '../api/recommendationAPI';

export const recommendationsService = {
  personal: ({ userId, limit = 8 }) => recommendationAPI.getPersonalized(userId, limit),
  trending: ({ limit = 12 } = {}) => recommendationAPI.getTrending(limit),
  similar: ({ productId, limit = 8 }) => recommendationAPI.getSimilarItems(productId, limit),
  alsoBought: ({ userId, limit = 8 }) => recommendationAPI.getCustomersAlsoBought(userId, limit),
  basedOnInteractions: ({ userId, limit = 8 }) => recommendationAPI.getBasedOnInteractions(userId, limit),
  cartCrossSell: ({ userId, limit = 8 }) => recommendationAPI.getCartBased(userId, limit)
};

export default recommendationsService;
