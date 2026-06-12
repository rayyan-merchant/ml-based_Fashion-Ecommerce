import { useEffect, useMemo, useState } from "react";
import { fetchAllReviews, reviews as reviewsAPI } from "../../api/api";

const REVIEWS_PAGE_SIZE = 5;

const getReviewerName = review =>
  review.reviewer_name || review.customer_name || review.user_name || review.name || "Verified Customer";

const getSentimentLabel = review => {
  if (review.sentiment_label) return review.sentiment_label;
  if (review.sentiment) return review.sentiment;
  if (Number(review.rating) >= 4) return "Positive";
  if (Number(review.rating) <= 2) return "Critical";
  return "Neutral";
};

export default function ReviewsView() {
  const [reviews, setReviews] = useState([]);
  const [ratingFilter, setRatingFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [visibleCount, setVisibleCount] = useState(REVIEWS_PAGE_SIZE);

  useEffect(() => {
    fetchAllReviews(0, 200).then(res => setReviews(res.data || []));
  }, []);

  useEffect(() => {
    setVisibleCount(REVIEWS_PAGE_SIZE);
  }, [ratingFilter, search]);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();

    return reviews.filter(review => {
      const matchesRating = ratingFilter === "all" || review.rating === Number(ratingFilter);
      const matchesSearch =
        !query ||
        getReviewerName(review).toLowerCase().includes(query) ||
        (review.review_text || "").toLowerCase().includes(query) ||
        String(review.article_id || "").includes(query) ||
        String(review.review_id || "").includes(query);

      return matchesRating && matchesSearch;
    });
  }, [reviews, ratingFilter, search]);

  const summary = useMemo(() => {
    const total = reviews.length;
    const average = total
      ? reviews.reduce((sum, review) => sum + Number(review.rating || 0), 0) / total
      : 0;
    const positive = reviews.filter(review => Number(review.rating) >= 4).length;
    const critical = reviews.filter(review => Number(review.rating) <= 2).length;

    return {
      total,
      average: average.toFixed(1),
      positive,
      critical
    };
  }, [reviews]);

  const visibleReviews = filtered.slice(0, visibleCount);

  const handleDelete = async (reviewId) => {
    if (!window.confirm("Delete this review?")) return;

    try {
      await reviewsAPI.delete(reviewId);
      setReviews(current => current.filter(review => review.review_id !== reviewId));
    } catch (error) {
      alert(error.response?.data?.detail || "Failed to delete review");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Reviews</h2>
          <p className="text-sm text-gray-500">Monitor customer names, product feedback, sentiment, and ratings.</p>
        </div>
        <div className="flex flex-col gap-3 md:flex-row">
          <input
            type="text"
            placeholder="Search reviewer, article, text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="rounded-lg border px-3 py-2"
          />
          <select
            value={ratingFilter}
            onChange={e => setRatingFilter(e.target.value)}
            className="rounded-lg border px-3 py-2"
          >
            <option value="all">All ratings</option>
            {[5, 4, 3, 2, 1].map(rating => (
              <option key={rating} value={rating}>
                {rating} stars
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <SummaryCard label="Total reviews" value={summary.total} />
        <SummaryCard label="Average rating" value={`${summary.average} / 5`} />
        <SummaryCard label="Positive reviews" value={summary.positive} />
        <SummaryCard label="Critical reviews" value={summary.critical} />
      </div>

      <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
            <tr>
              <th className="px-4 py-3">Customer</th>
              <th className="px-4 py-3">Article</th>
              <th className="px-4 py-3">Rating</th>
              <th className="px-4 py-3">Sentiment</th>
              <th className="px-4 py-3">Review</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length ? (
              visibleReviews.map(review => (
                <tr key={review.review_id} className="border-t">
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-900">{getReviewerName(review)}</p>
                    <p className="font-mono text-xs text-gray-500">Review {review.review_id}</p>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{review.article_id}</td>
                  <td className="px-4 py-3 font-semibold text-gray-900">{review.rating ?? "-"}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700">
                      {getSentimentLabel(review)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{review.review_text || "-"}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(review.review_id)}
                      className="text-sm text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                  No reviews match the selected filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {filtered.length > 0 && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            Showing {Math.min(visibleCount, filtered.length)} of {filtered.length} reviews
          </span>
          {visibleCount < filtered.length && (
            <button
              onClick={() => setVisibleCount(count => count + REVIEWS_PAGE_SIZE)}
              className="rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
            >
              Load 5 More Reviews
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function SummaryCard({ label, value }) {
  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p>
    </div>
  );
}
