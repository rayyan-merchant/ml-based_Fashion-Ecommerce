import { cart, wishlist } from '../api/api';

export const cartService = {
  get: () => cart.get(),
  add: ({ articleId, quantity = 1 }) => cart.add(articleId, quantity),
  update: (cartId, payload) => cart.update(cartId, payload),
  remove: (cartId) => cart.remove(cartId),
  clear: (customerId) => cart.clear(customerId),
  wishlist: {
    get: () => wishlist.get(),
    add: (articleId) => wishlist.add(articleId),
    remove: (wishlistId) => wishlist.remove(wishlistId),
    moveToCart: (wishlistId) => wishlist.moveToCart(wishlistId)
  }
};

export default cartService;
