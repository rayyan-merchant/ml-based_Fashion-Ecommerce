import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchReviewsByProduct, postReview } from "../api/api";
import ReviewItem from "../components/ReviewItem";

const REVIEWS_PAGE_SIZE = 5;

export default function Reviews({ productId: productIdProp }) {
  const { productId: routeProductId } = useParams();
  const productId = productIdProp || routeProductId;
  const [reviews, setReviews] = useState([]);
  const [visibleCount, setVisibleCount] = useState(REVIEWS_PAGE_SIZE);
  const [text, setText] = useState("");
  const [rating, setRating] = useState(5);

  useEffect(() => {
    if (!productId) return;
    setVisibleCount(REVIEWS_PAGE_SIZE);
    fetchReviewsByProduct(productId).then(res => setReviews(res.data || []))
      .catch(err => console.error(err));
  }, [productId]);

  const handleSubmit = (e) => {
    e.preventDefault();
    postReview({ productId, customer_id: "C101", review_text: text, rating })
      .then(res => setReviews([...reviews, { review_id: Date.now(), customer_id: "C101", review_text: text, rating, created_at: new Date() }]))
      .catch(err => console.error(err));
    setText("");
  };

  const visibleReviews = reviews.slice(0, visibleCount);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-2">Reviews</h2>
      {reviews.length ? (
        <>
          <p className="mb-3 text-sm text-gray-500">
            Showing {Math.min(visibleCount, reviews.length)} of {reviews.length} reviews
          </p>
          {visibleReviews.map(r => <ReviewItem key={r.review_id} review={r} />)}
          {visibleCount < reviews.length && (
            <button
              type="button"
              onClick={() => setVisibleCount(count => count + REVIEWS_PAGE_SIZE)}
              className="rounded border px-4 py-2 text-sm hover:bg-gray-50"
            >
              Load 5 More Reviews
            </button>
          )}
        </>
      ) : <p>No reviews yet.</p>}
      <form onSubmit={handleSubmit} className="mt-4 space-y-2">
        <textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Write your review..." className="w-full border p-2 rounded"/>
        <select value={rating} onChange={e=>setRating(e.target.value)} className="border p-2 rounded">
          {[5,4,3,2,1].map(n => <option key={n} value={n}>{n}</option>)}
        </select>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Submit Review</button>
      </form>
    </div>
  );
}
