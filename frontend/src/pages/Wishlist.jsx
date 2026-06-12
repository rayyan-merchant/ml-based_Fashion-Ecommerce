import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { articles } from "../api/api";
import { getImageUrl } from "../utils/getimageurl";
import { formatPrice } from "../utils/price";


export default function Wishlist() {
  const { user, wishlistItems, removeFromWishlist, moveWishlistToCart, loadWishlist } = useApp();
  const [wishlistProducts, setWishlistProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      loadWishlist(user.customer_id).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [user]);

  // Load full product details for wishlist items
  useEffect(() => {
    if (wishlistItems.length > 0) {
      const productIds = wishlistItems.map(item => item.article_id);
      
      Promise.all(
        productIds.map(id => articles.getById(id).catch(() => null))
      ).then(responses => {
        const products = responses
          .filter(res => res && res.data)
          .map((res, idx) => {
            // Find the corresponding wishlist item to get the wishlist_id
            const wishlistItem = wishlistItems.find(item => item.article_id === res.data.article_id);
            return {
              ...res.data,
              wishlist_id: wishlistItem ? wishlistItem.wishlist_id : null
            };
          });
        setWishlistProducts(products);
      });
    } else {
      setWishlistProducts([]);
    }
  }, [wishlistItems]);

  const handleRemove = async (wishlistId) => {
    const result = await removeFromWishlist(wishlistId);
    if (!result.success) {
      alert(result.error || 'Failed to remove from wishlist');
    }
  };

  const handleMoveToCart = async (wishlistId) => {
    const result = await moveWishlistToCart(wishlistId);
    if (result.success) {
      alert('Item moved to cart!');
    } else {
      alert(result.error || 'Failed to move to cart');
    }
  };

  if (loading) {
    return (
      <div className="app-container py-12 min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mb-4"></div>
          <p className="text-gray-600">Loading your wishlist...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container py-6 md:py-8">
      <h1 className="text-3xl md:text-4xl font-bold mb-8 text-gray-900">My Wishlist</h1>
      
      {wishlistProducts.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {wishlistProducts.map(product => (
            <div key={product.wishlist_id} className="relative">
              <div className="bg-white border border-gray-100 rounded-xl p-4">
                <img
                  src={getImageUrl(product.image_path)}
                  alt={product.prod_name}
                  className="w-full h-48 object-contain rounded-lg mb-4"
                  onError={(e) => e.target.src = "/images/placeholder.jpg"}
                />
                <h3 className="text-sm font-medium text-gray-800 mb-2">{product.prod_name}</h3>
                <p className="text-gray-500 text-sm mb-4">{formatPrice(product.price)}</p>
                
                <div className="space-y-2">
                  <button
                    onClick={() => handleMoveToCart(product.wishlist_id)}
                    className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
                  >
                    Move to Cart
                  </button>
                  <button
                    onClick={() => handleRemove(product.wishlist_id)}
                    className="w-full bg-gray-100 text-gray-700 py-2 rounded-lg text-sm font-medium hover:bg-gray-200"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <div className="max-w-md mx-auto">
            <svg className="mx-auto h-24 w-24 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2 mt-4">Your wishlist is empty</h2>
            <p className="text-gray-600 mb-8">Start adding items you love!</p>
            <button
              onClick={() => navigate('/products')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700"
            >
              Browse Products
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
