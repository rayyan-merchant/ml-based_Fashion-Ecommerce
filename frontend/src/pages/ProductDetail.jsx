import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { articles, reviews as reviewsAPI } from "../api/api";
import { sentimentAPI } from "../api/sentimentAPI";
import { nlpAPI } from "../api/nlpAPI";
import { recommendationAPI } from "../api/recommendationAPI";
import { useApp } from "../context/AppContext";
import ReviewItem from "../components/ReviewItem";
import ProductCard from "../components/ProductCard";
import { getImageUrl } from "../utils/getimageurl";
import { getColorSwatch, groupProductVariants } from "../utils/productVariants";
import { formatPrice } from "../utils/price";
import {
  SentimentBars,
  WordcloudImage,
  SimilarReviewsModal,
  ProductCarousel,
  ComplaintList,
  SkeletonLoader
} from "../components/ml";

const REVIEWS_PAGE_SIZE = 5;

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, addToCart, addToWishlist, isAuthenticated } = useApp();
  const [product, setProduct] = useState(null);
  const [variants, setVariants] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [embeddingSimilarProducts, setEmbeddingSimilarProducts] = useState([]);
  const [customerRecommendedProducts, setCustomerRecommendedProducts] = useState([]);
  const [sentimentSummary, setSentimentSummary] = useState(null);
  const [wordcloudData, setWordcloudData] = useState(null);
  const [complaints, setComplaints] = useState([]);
  const [sortOrder, setSortOrder] = useState('newest');
  const [visibleReviewCount, setVisibleReviewCount] = useState(REVIEWS_PAGE_SIZE);
  const [selectedReviewId, setSelectedReviewId] = useState(null);
  const [similarReviewsModalOpen, setSimilarReviewsModalOpen] = useState(false);
  const [selectedReview, setSelectedReview] = useState(null);

  const [newReview, setNewReview] = useState({
    rating: 5,
    review_text: ""
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [isAddingToCart, setIsAddingToCart] = useState(false);
  const [isAddingToWishlist, setIsAddingToWishlist] = useState(false);
  const [loading, setLoading] = useState({
    product: true,
    reviews: true,
    sentiment: true,
    wordcloud: true,
    similar: true,
    customerRecommendations: false,
    complaints: true
  });

  const normalizeReviews = (data) => {
    const rawReviews = data?.reviews || data || [];
    if (!Array.isArray(rawReviews)) return [];

    return rawReviews.map((review) => ({
      ...review,
      sentiment: review.sentiment || review.sentiment_label,
      created_at: review.created_at || new Date().toISOString()
    }));
  };

  useEffect(() => {
    // Reset states when ID changes
    setProduct(null);
    setVariants([]);
    setReviews([]);
    setSimilarProducts([]);
    setEmbeddingSimilarProducts([]);
    setCustomerRecommendedProducts([]);
    setSentimentSummary(null);
    setWordcloudData(null);
    setComplaints([]);
    setError(null);
    setSortOrder('newest');
    setVisibleReviewCount(REVIEWS_PAGE_SIZE);

    // Fetch product data
    const fetchProductData = async () => {
      try {
        setLoading(prev => ({ ...prev, product: true }));

        // Fetch product
        const [productRes, variantsRes] = await Promise.all([
          articles.getById(id),
          articles.getVariants(id).catch(() => ({ data: { variants: [] } }))
        ]);
        setProduct(productRes.data);
        setVariants(variantsRes.data?.variants || []);

        // Fetch ML data in parallel
        await Promise.allSettled([
          fetchSentimentData(),
          fetchWordcloud(),
          fetchSimilarProducts(),
          fetchComplaints(productRes.data.product_group_name)
        ]);

      } catch (err) {
        console.error("Error fetching product data:", err);
        setError("Failed to load product. Please try again.");
      } finally {
        setLoading(prev => ({ ...prev, product: false }));
      }
    };

    // Fetch reviews with current sort order
    const fetchReviews = async () => {
      setLoading(prev => ({ ...prev, reviews: true }));
      try {
        const reviewsRes = await sentimentAPI.getProductReviews(id, sortOrder, 100);
        setReviews(normalizeReviews(reviewsRes.data));
      } catch (err) {
        // Fallback to regular reviews API
        try {
          const reviewsRes = await reviewsAPI.getByArticle(id);
          setReviews(normalizeReviews(reviewsRes.data));
        } catch (e) {
          setReviews([]);
        }
      } finally {
        setLoading(prev => ({ ...prev, reviews: false }));
      }
    };

    // Fetch sentiment summary
    const fetchSentimentData = async () => {
      setLoading(prev => ({ ...prev, sentiment: true }));
      try {
        const response = await sentimentAPI.getProductSummary(id);
        setSentimentSummary(response.data);
      } catch (err) {
        console.log("Sentiment data not available");
      } finally {
        setLoading(prev => ({ ...prev, sentiment: false }));
      }
    };

    // Fetch wordcloud
    const fetchWordcloud = async () => {
      setLoading(prev => ({ ...prev, wordcloud: true }));
      try {
        const response = await nlpAPI.getProductWordcloud(id);
        setWordcloudData(response.data);
      } catch (err) {
        console.log("Wordcloud not available");
      } finally {
        setLoading(prev => ({ ...prev, wordcloud: false }));
      }
    };

    // Fetch similar products (embedding-based + recommendation-based)
    const fetchSimilarProducts = async () => {
      setLoading(prev => ({ ...prev, similar: true }));
      try {
        const [embeddingRes, recRes] = await Promise.allSettled([
          nlpAPI.getSimilarProducts(id, 8),
          recommendationAPI.getSimilarItems(id, 8)
        ]);

        if (embeddingRes.status === 'fulfilled') {
          setEmbeddingSimilarProducts(groupProductVariants(embeddingRes.value.data?.products || embeddingRes.value.data || []));
        }
        if (recRes.status === 'fulfilled') {
          setSimilarProducts(groupProductVariants(recRes.value.data?.products || recRes.value.data || []));
        }
      } catch (err) {
        // Fallback to regular products
        const allProductsRes = await articles.getCatalog({ limit: 8 });
        setSimilarProducts(allProductsRes.data?.products || []);
      } finally {
        setLoading(prev => ({ ...prev, similar: false }));
      }
    };

    // Fetch category complaints
    const fetchComplaints = async (categoryName) => {
      setLoading(prev => ({ ...prev, complaints: true }));
      try {
        // Try to get category ID from name
        const response = await nlpAPI.getCategoryComplaints(categoryName);
        setComplaints(response.data?.complaints || response.data || []);
      } catch (err) {
        console.log("Complaints not available");
      } finally {
        setLoading(prev => ({ ...prev, complaints: false }));
      }
    };

    if (id) {
      fetchProductData();
      fetchReviews();
    }
  }, [id]);

  useEffect(() => {
    if (!id || !isAuthenticated || !user?.customer_id) {
      setCustomerRecommendedProducts([]);
      return;
    }

    let cancelled = false;

    const fetchCustomerRecommendations = async () => {
      setLoading(prev => ({ ...prev, customerRecommendations: true }));
      try {
        const response = await recommendationAPI.getBasedOnInteractions(user.customer_id, 12);
        const rawRecommendations = response.data?.recommendations || response.data || [];
        const filtered = rawRecommendations.filter((item) => {
          const itemId = item.article_id || item.product_id || item.id;
          return String(itemId) !== String(id);
        });

        if (!cancelled) {
          setCustomerRecommendedProducts(groupProductVariants(filtered).slice(0, 8));
        }
      } catch (err) {
        console.error("Failed to load personalized product-page recommendations:", err);
        if (!cancelled) {
          setCustomerRecommendedProducts([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(prev => ({ ...prev, customerRecommendations: false }));
        }
      }
    };

    fetchCustomerRecommendations();

    return () => {
      cancelled = true;
    };
  }, [id, isAuthenticated, user?.customer_id]);

  // Refetch reviews when sort order changes
  useEffect(() => {
    if (!id) return;

    const fetchSortedReviews = async () => {
      setLoading(prev => ({ ...prev, reviews: true }));
      setVisibleReviewCount(REVIEWS_PAGE_SIZE);
      try {
        const response = await sentimentAPI.getProductReviews(id, sortOrder, 100);
        setReviews(normalizeReviews(response.data));
      } catch (err) {
        console.log("Could not fetch sorted reviews");
      } finally {
        setLoading(prev => ({ ...prev, reviews: false }));
      }
    };

    fetchSortedReviews();
  }, [sortOrder, id]);

  const handleReviewSubmit = async (e) => {
    e.preventDefault();

    if (!isAuthenticated) {
      alert('Please login to write a review');
      navigate('/login');
      return;
    }

    if (!newReview.review_text) return;

    setIsSubmitting(true);
    try {
      const reviewData = {
        customer_id: user.customer_id,
        article_id: id,
        rating: newReview.rating,
        review_text: newReview.review_text
      };

      await reviewsAPI.create(reviewData);

      // Reload reviews
      const reviewsRes = await sentimentAPI.getProductReviews(id, sortOrder, 100);
      setReviews(normalizeReviews(reviewsRes.data));
      setVisibleReviewCount(REVIEWS_PAGE_SIZE);

      // Reset form
      setNewReview({
        rating: 5,
        review_text: ""
      });

      alert('Review submitted successfully!');
    } catch (err) {
      console.error("Failed to submit review:", err);
      alert('Failed to submit review. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openSimilarReviewsModal = (review) => {
    setSelectedReviewId(review.review_id);
    setSelectedReview(review);
    setSimilarReviewsModalOpen(true);
  };

  const visibleReviews = reviews.slice(0, visibleReviewCount);
  const hasMoreReviews = visibleReviewCount < reviews.length;

  if (error) {
    return (
      <div className="app-container py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h2 className="text-xl font-bold text-red-800 mb-2">Error</h2>
          <p className="text-red-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (loading.product && !product) {
    return (
      <div className="app-container py-12">
        <div className="flex justify-center items-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
            <p className="text-gray-600">Loading product details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!product) return null;
  const saleDiscount = Number(product.sale_discount_pct || 0);
  const salePrice = saleDiscount > 0 ? Number(product.price || 0) * (100 - saleDiscount) / 100 : Number(product.price || 0);

  return (
    <div className="app-container py-6 md:py-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        {/* Product Image */}
        <div className="w-full">
          <div className="w-full aspect-square max-h-[70vh] bg-gray-100 rounded-xl overflow-hidden flex items-center justify-center relative">
            <img
              src={getImageUrl(product.image_path)}
              alt={product.prod_name}
              className="absolute inset-0 w-full h-full object-contain"
              onError={(e) => {
                e.target.src = getImageUrl("");
              }}
            />
            {saleDiscount > 0 && (
              <span className="absolute left-4 top-4 rounded-full bg-[var(--clr-danger)] px-4 py-2 text-sm font-semibold text-white shadow">
                {saleDiscount}% OFF
              </span>
            )}
          </div>
        </div>

        {/* Product Details */}
        <div className="w-full">
          <h1 className="text-3xl md:text-4xl font-bold mb-4 text-gray-900">{product.prod_name}</h1>
          {saleDiscount > 0 ? (
            <div className="mb-4">
              <p className="text-2xl font-semibold text-[var(--clr-danger)]">{formatPrice(salePrice)}</p>
              <p className="text-sm text-gray-500 line-through">{formatPrice(product.price)}</p>
            </div>
          ) : (
            <p className="text-2xl font-semibold text-gray-900 mb-4">{formatPrice(product.price)}</p>
          )}
          <p className="mb-2 text-gray-600">Stock: <span className="font-medium">{product.stock}</span></p>
          <p className="mb-2 text-gray-600">Category: <span className="font-medium">{product.product_group_name}</span></p>
          <p className="mb-2 text-gray-600">Color: <span className="font-medium">{product.colour_group_name}</span></p>
          <p className="mb-6 text-gray-600">Type: <span className="font-medium">{product.product_type_name}</span></p>

          {variants.length > 1 && (
            <div className="mb-6">
              <p className="mb-3 text-sm font-medium text-gray-700">Available Colors</p>
              <div className="flex flex-wrap gap-3">
                {variants.map((variant) => {
                  const isActive = String(variant.article_id) === String(product.article_id);
                  return (
                    <button
                      key={variant.article_id}
                      type="button"
                      onClick={() => navigate(`/products/${variant.article_id}`)}
                      className={`flex items-center gap-2 rounded-full border px-3 py-2 text-sm transition ${
                        isActive
                          ? "border-[var(--clr-primary)] bg-[var(--clr-primary-soft)] text-[var(--clr-primary-dark)]"
                          : "border-gray-200 bg-white text-gray-700 hover:border-[var(--clr-primary)]"
                      }`}
                      title={variant.colour_group_name}
                    >
                      <span
                        className="h-4 w-4 rounded-full border border-white shadow ring-1 ring-gray-200"
                        style={{ background: getColorSwatch(variant.colour_group_name) }}
                      />
                      {variant.colour_group_name || "Color"}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 mb-8">
            <button
              onClick={async () => {
                if (!isAuthenticated) {
                  alert('Please login to add items to cart');
                  navigate('/login');
                  return;
                }
                setIsAddingToCart(true);
                const result = await addToCart(product.article_id, 1);
                setIsAddingToCart(false);
                if (result.success) {
                  alert('Added to cart!');
                } else {
                  alert(result.error || 'Failed to add to cart');
                }
              }}
              disabled={isAddingToCart}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAddingToCart ? 'Adding to Cart...' : 'Add to Cart'}
            </button>
            <button
              onClick={async () => {
                if (!isAuthenticated) {
                  alert('Please login to add items to wishlist');
                  navigate('/login');
                  return;
                }
                setIsAddingToWishlist(true);
                const result = await addToWishlist(product.article_id);
                setIsAddingToWishlist(false);
                if (result.success) {
                  alert('Added to wishlist!');
                } else {
                  alert(result.error || 'Failed to add to wishlist');
                }
              }}
              disabled={isAddingToWishlist}
              className="bg-gray-200 text-black px-6 py-3 rounded-lg font-medium hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAddingToWishlist ? 'Adding to Wishlist...' : 'Add to Wishlist'}
            </button>
            <button
              onClick={async () => {
                if (!isAuthenticated) {
                  alert('Please login to purchase');
                  navigate('/login');
                  return;
                }
                setIsAddingToCart(true);
                const result = await addToCart(product.article_id, 1);
                setIsAddingToCart(false);
                if (result.success) {
                  navigate('/cart');
                } else {
                  alert(result.error || 'Failed to add to cart');
                }
              }}
              disabled={isAddingToCart}
              className="bg-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAddingToCart ? 'Adding to Cart...' : 'Buy Now'}
            </button>
          </div>

          {/* Product Description */}
          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-semibold mb-2">Description</h3>
            <p className="text-gray-600">{product.detail_desc || "No description available for this product."}</p>
          </div>
        </div>
      </div>

      {/* Sentiment Summary Bar */}
      {(sentimentSummary || loading.sentiment) && (
        <div className="mb-8 bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Sentiment</h3>
          {loading.sentiment ? (
            <SkeletonLoader variant="bar" />
          ) : (
            <SentimentBars
              positive={sentimentSummary?.positive || 0}
              neutral={sentimentSummary?.neutral || 0}
              negative={sentimentSummary?.negative || 0}
              totalReviews={sentimentSummary?.total_reviews || 0}
              size="lg"
            />
          )}
        </div>
      )}

      {/* Reviews Section */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Reviews</h2>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Sort by:</label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="newest">Newest First</option>
              <option value="positive">Most Positive</option>
              <option value="negative">Most Negative</option>
              <option value="neutral">Neutral</option>
            </select>
          </div>
        </div>

        {/* Review Submission Form */}
        <div className="border rounded-lg p-6 mb-8">
          <h3 className="text-xl font-semibold mb-4">Write a Review</h3>
          <form onSubmit={handleReviewSubmit}>
            <div className="mb-4">
              <label htmlFor="rating" className="block text-sm font-medium text-gray-700 mb-1">
                Rating
              </label>
              <select
                id="rating"
                value={newReview.rating}
                onChange={(e) => setNewReview({ ...newReview, rating: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {[1, 2, 3, 4, 5].map(num => (
                  <option key={num} value={num}>{num} Star{num > 1 ? 's' : ''}</option>
                ))}
              </select>
            </div>

            <div className="mb-4">
              <label htmlFor="review_text" className="block text-sm font-medium text-gray-700 mb-1">
                Review
              </label>
              <textarea
                id="review_text"
                value={newReview.review_text}
                onChange={(e) => setNewReview({ ...newReview, review_text: e.target.value })}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                placeholder="Share your experience with this product..."
              ></textarea>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-blue-600 text-white px-6 py-2 rounded-md font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {isSubmitting ? "Submitting..." : "Submit Review"}
            </button>
          </form>
        </div>

        {/* Existing Reviews */}
        {loading.reviews ? (
          <SkeletonLoader variant="text" count={3} />
        ) : reviews.length > 0 ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">
              Showing {Math.min(visibleReviewCount, reviews.length)} of {reviews.length} reviews
            </p>
            {visibleReviews.map(review => (
              <div key={review.review_id} className="border rounded-lg p-4">
                <ReviewItem review={review} />
                {/* Sentiment Badge */}
                {review.sentiment && (
                  <span className={`mt-2 inline-block px-2 py-1 rounded-full text-xs font-medium ${review.sentiment === 'positive' ? 'bg-green-100 text-green-700' :
                    review.sentiment === 'negative' ? 'bg-red-100 text-red-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                    {review.sentiment}
                  </span>
                )}
                {/* Similar Reviews Button */}
                <button
                  onClick={() => openSimilarReviewsModal(review)}
                  className="mt-3 inline-flex items-center rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100"
                >
                  Similar Reviews
                </button>
              </div>
            ))}
            {hasMoreReviews && (
              <div className="pt-2 text-center">
                <button
                  onClick={() => setVisibleReviewCount(count => count + REVIEWS_PAGE_SIZE)}
                  className="rounded-lg border border-gray-300 px-5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Load 5 More Reviews
                </button>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-600">No reviews yet. Be the first to review this product!</p>
        )}
      </div>

      {/* Similar Reviews Modal */}
      <SimilarReviewsModal
        reviewId={selectedReviewId}
        isOpen={similarReviewsModalOpen}
        onClose={() => setSimilarReviewsModalOpen(false)}
        originalReview={selectedReview}
      />

      {/* Wordcloud Section */}
      {(wordcloudData?.image || loading.wordcloud) && (
        <div className="mt-12">
          <WordcloudImage
            base64Data={wordcloudData?.image}
            productName={product.prod_name}
            loading={loading.wordcloud}
          />
        </div>
      )}

      {/* Customer-Personalized Recommendations */}
      {(customerRecommendedProducts.length > 0 || loading.customerRecommendations) && (
        <div className="mt-12">
          <ProductCarousel
            products={customerRecommendedProducts}
            title="Recommended For You"
            loading={loading.customerRecommendations}
          />
        </div>
      )}

      {/* Similar Products (Embedding-Based) */}
      {embeddingSimilarProducts.length > 0 && (
        <div className="mt-12">
          <ProductCarousel
            products={embeddingSimilarProducts}
            title="Similar Products"
          />
        </div>
      )}

      {/* You May Also Like (Recommendation-Based) */}
      {similarProducts.length > 0 && (
        <div className="mt-12">
          <h2 className="text-2xl font-bold mb-6 text-gray-900 flex items-center gap-2">
            You May Also Like
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {similarProducts.map(product => (
              <ProductCard key={product.product_code || product.article_id} product={product} />
            ))}
          </div>
        </div>
      )}

      {/* Top Complaints in Category */}
      {complaints.length > 0 && (
        <div className="mt-12">
          <ComplaintList
            complaints={complaints}
            categoryName={product.product_group_name}
          />
        </div>
      )}
    </div>
  );
}
