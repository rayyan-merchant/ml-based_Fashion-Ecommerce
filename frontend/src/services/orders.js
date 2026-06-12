import { orders } from '../api/api';

export const ordersService = {
  list: ({ skip = 0, limit = 100 } = {}) => orders.getAll(skip, limit),
  mine: () => orders.getMyOrders(),
  get: (orderId) => orders.getDetails(orderId),
  place: ({ shippingAddress }) => orders.create(shippingAddress),
  updateStatus: (orderId, status) => orders.updateStatus(orderId, status),
  updateAddress: (orderId, address) => orders.updateAddress(orderId, address),
  dailySales: ({ skip = 0, limit = 50 } = {}) => orders.getDailySales(skip, limit)
};

export default ordersService;
