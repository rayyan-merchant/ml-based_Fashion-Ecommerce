import { customers } from '../api/api';
import segmentationAPI from '../api/segmentationAPI';

export const customersService = {
  list: ({ skip = 0, limit = 100 } = {}) => customers.getAll(skip, limit),
  get: (customerId) => customers.getById(customerId),
  create: (payload) => customers.create(payload),
  update: (customerId, payload) => customers.update(customerId, payload),
  remove: (customerId) => customers.delete(customerId),
  orders: (customerId, { skip = 0, limit = 100 } = {}) => customers.getOrders(customerId, skip, limit),
  events: (customerId, { skip = 0, limit = 100 } = {}) => customers.getEvents(customerId, skip, limit),
  segment: (customerId) => segmentationAPI.getCustomerSegment(customerId)
};

export default customersService;
