import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import CartItem from "../components/CartItem";
import { useApp } from "../context/AppContext";
import { getImageUrl } from "../utils/getimageurl";
import { formatPrice, naturalPrice } from "../utils/price";

export default function Cart() {
  const { user, cartItems, removeFromCart, updateCartItem, loadCart } = useApp();
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      loadCart(user.customer_id)
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [user]);

  const handleRemove = async (cartId) => {
    const result = await removeFromCart(cartId);
    if (!result.success) {
      alert(result.error || 'Failed to remove item');
    }
  };

  const handleUpdateQuantity = async (cartId, newQuantity) => {
    if (newQuantity < 1) {
      handleRemove(cartId);
      return;
    }

    const result = await updateCartItem(cartId, newQuantity);
    if (!result.success) {
      alert(result.error || 'Failed to update quantity');
    }
  };

  // Calculate totals from cart items
  const subtotal = cartItems.reduce((sum, item) => {
    const price = naturalPrice(item.price || 0);
    const quantity = item.quantity || 0;
    return sum + (price * quantity);
  }, 0);

  const tax = subtotal * 0.1; // 10% tax
  const freeShippingThreshold = 25000;
  const shipping = subtotal > freeShippingThreshold ? 0 : 350;
  const total = subtotal + tax + shipping;

  const handleCheckout = () => {
    if (cartItems.length > 0) {
      navigate('/checkout');
    }
  };

  if (loading) {
    return (
      <div className="app-container py-12 min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mb-4"></div>
          <p className="text-gray-600">Loading your cart...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container py-8 md:py-12 min-h-[60vh]">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Shopping Cart</h1>

      {cartItems.length === 0 ? (
        <div className="text-center py-16">
          <div className="max-w-md mx-auto">
            <svg
              className="mx-auto h-24 w-24 text-gray-300 mb-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
              />
            </svg>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">Your cart is empty</h2>
            <p className="text-gray-600 mb-8">Looks like you haven't added anything to your cart yet.</p>
            <button
              onClick={() => navigate('/products')}
              className="btn-soft px-6 py-3 text-base"
            >
              Continue Shopping
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {/* Cart Items */}
          <div className="md:col-span-2 space-y-4">
            {cartItems.map(item => (
              <CartItem
                key={item.cart_id}
                item={{
                  order_item_id: item.cart_id,
                  article_id: item.article_id,
                  prod_name: item.article_name || item.name,
                  unit_price: item.price,
                  quantity: item.quantity,
                  image: getImageUrl(item.image_path)
                }}
                onRemove={() => handleRemove(item.cart_id)}
                onUpdateQuantity={(id, qty) => handleUpdateQuantity(item.cart_id, qty)}
              />
            ))}
          </div>

          {/* Order Summary */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 sticky top-4">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Order Summary</h2>

              <div className="space-y-4 mb-6">
                <div className="flex justify-between text-gray-600">
                  <span>Subtotal</span>
                  <span>{formatPrice(subtotal)}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Tax</span>
                  <span>{formatPrice(tax)}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Shipping</span>
                  <span className={shipping === 0 ? "text-green-600" : ""}>
                    {shipping === 0 ? "Free" : formatPrice(shipping)}
                  </span>
                </div>
                {subtotal < freeShippingThreshold && (
                  <p className="text-sm text-gray-500">
                    Add {formatPrice(freeShippingThreshold - subtotal)} more for free shipping!
                  </p>
                )}
                <div className="border-t border-gray-200 pt-4">
                  <div className="flex justify-between text-lg font-semibold text-gray-900">
                    <span>Total</span>
                    <span>{formatPrice(total)}</span>
                  </div>
                </div>
              </div>

              <button
                onClick={handleCheckout}
                className="w-full bg-gray-900 text-white py-3 px-6 rounded-lg font-medium hover:bg-gray-800 transition-colors duration-200 mb-4"
              >
                Proceed to Checkout
              </button>

              <button
                onClick={() => navigate('/products')}
                className="w-full bg-gray-100 text-gray-900 py-3 px-6 rounded-lg font-medium hover:bg-gray-200 transition-colors duration-200"
              >
                Continue Shopping
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
