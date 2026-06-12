import { mlApi } from './api';

export const segmentationAPI = {
  getCustomerSegment: (customerId) => mlApi.get(`/segmentation/customer/${customerId}`),

  getSegmentOverview: () => mlApi.get('/segmentation/overview'),

  getSegmentProfiles: () => mlApi.get('/segmentation/profiles'),

  getSegmentDefinitions: () => mlApi.get('/segmentation/definitions'),

  getCustomersBySegment: (segmentId, limit = 50) =>
    mlApi.get(`/segmentation/segment/${segmentId}/customers`, { params: { limit } })
};

export default segmentationAPI;
