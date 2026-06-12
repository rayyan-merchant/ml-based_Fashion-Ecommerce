import React, { useState, useEffect } from 'react';
import { nlpAPI } from '../../api/nlpAPI';

/**
 * SimilarReviewsModal - Modal showing similar reviews from FAISS search
 * @param {string} reviewId - ID of the review to find similar ones for
 * @param {boolean} isOpen - Whether the modal is open
 * @param {function} onClose - Function to close the modal
 * @param {object} originalReview - The original review object
 */
export default function SimilarReviewsModal({
    reviewId,
    isOpen,
    onClose,
    originalReview = null
}) {
    const [similarReviews, setSimilarReviews] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isOpen && reviewId) {
            setSimilarReviews([]);
            fetchSimilarReviews();
        }
    }, [isOpen, reviewId]);

    const fetchSimilarReviews = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await nlpAPI.getSimilarReviews(reviewId, 5);
            // Handle different response formats: array, {reviews: []}, {similar_reviews: []}, or error object
            const data = response.data;
            if (data?.error) {
                setError(data.error);
                setSimilarReviews([]);
            } else if (Array.isArray(data)) {
                setSimilarReviews(normalizeSimilarReviews(data));
            } else if (Array.isArray(data?.reviews)) {
                setSimilarReviews(normalizeSimilarReviews(data.reviews));
            } else if (Array.isArray(data?.similar_reviews)) {
                setSimilarReviews(normalizeSimilarReviews(data.similar_reviews));
            } else {
                setSimilarReviews([]);
            }
        } catch (err) {
            console.error('Failed to fetch similar reviews:', err);
            setError('Failed to load similar reviews. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const normalizeSimilarReviews = (reviews) => reviews.map(review => ({
        ...review,
        similarity_score: Number(review.similarity_score ?? review.similarity ?? 0),
        sentiment: review.sentiment || review.sentiment_label,
        created_at: review.created_at || null
    }));

    if (!isOpen) return null;

    const getSentimentColor = (sentiment) => {
        switch (sentiment?.toLowerCase()) {
            case 'positive': return 'bg-green-100 text-green-800';
            case 'negative': return 'bg-red-100 text-red-800';
            default: return 'bg-yellow-100 text-yellow-800';
        }
    };

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/50 transition-opacity"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="flex min-h-full items-center justify-center p-4">
                <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
                    {/* Header */}
                    <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-50 to-purple-50">
                        <div>
                            <h2 className="text-xl font-bold text-gray-900">Similar Reviews</h2>
                            <p className="text-sm text-gray-500">Reviews with similar content and sentiment</p>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                        >
                            <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* Original Review */}
                    {originalReview && (
                        <div className="px-6 py-4 bg-blue-50 border-b border-blue-100">
                            <p className="text-xs uppercase tracking-wide text-blue-600 font-semibold mb-2">Original Review</p>
                            <p className="text-gray-800 text-sm line-clamp-3">{originalReview.review_text}</p>
                            {originalReview.sentiment && (
                                <span className={`mt-2 inline-block px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(originalReview.sentiment)}`}>
                                    {originalReview.sentiment}
                                </span>
                            )}
                        </div>
                    )}

                    {/* Content */}
                    <div className="px-6 py-4 overflow-y-auto max-h-[50vh]">
                        {loading ? (
                            <div className="space-y-4">
                                {[1, 2, 3].map((i) => (
                                    <div key={i} className="animate-pulse">
                                        <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                                        <div className="h-4 bg-gray-200 rounded w-full" />
                                        <div className="h-4 bg-gray-200 rounded w-1/2 mt-2" />
                                    </div>
                                ))}
                            </div>
                        ) : error ? (
                            <div className="text-center py-8">
                                <div className="text-red-500 mb-2">
                                    <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <p className="text-gray-600">{error}</p>
                                <button
                                    onClick={fetchSimilarReviews}
                                    className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                                >
                                    Retry
                                </button>
                            </div>
                        ) : similarReviews.length === 0 ? (
                            <div className="text-center py-8">
                                <div className="text-gray-400 mb-2">
                                    <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <p className="text-gray-500">No similar reviews found</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {similarReviews.map((review, index) => (
                                    <div
                                        key={review.review_id || index}
                                        className="p-4 bg-gray-50 rounded-xl border border-gray-100 hover:border-gray-200 transition-colors"
                                    >
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-gray-900">
                                                    {review.reviewer_name || review.customer_name || "Verified Customer"}
                                                </span>
                                                {review.similarity_score > 0 && (
                                                    <span className="text-xs text-gray-400">
                                                        {Math.round(review.similarity_score * 100)}% similar
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-1">
                                                {[...Array(5)].map((_, i) => (
                                                    <svg
                                                        key={i}
                                                        className={`w-4 h-4 ${i < (review.rating || 0) ? 'text-yellow-400' : 'text-gray-200'}`}
                                                        fill="currentColor"
                                                        viewBox="0 0 20 20"
                                                    >
                                                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                                    </svg>
                                                ))}
                                            </div>
                                        </div>
                                        <p className="text-gray-700 text-sm">{review.review_text}</p>
                                        {review.sentiment && (
                                            <span className={`mt-2 inline-block px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(review.sentiment)}`}>
                                                {review.sentiment}
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
                        <button
                            onClick={onClose}
                            className="w-full px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
