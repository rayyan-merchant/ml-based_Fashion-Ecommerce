import { useState, useEffect, useCallback } from 'react';
import { sentimentAPI } from '../api/sentimentAPI';

/**
 * useSentiment - Custom hook for sentiment analysis data
 * @param {string} productId - Product ID
 */
export function useSentiment(productId) {
    const [summary, setSummary] = useState(null);
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [sortOrder, setSortOrder] = useState('newest');

    // Fetch sentiment summary
    const fetchSummary = useCallback(async () => {
        if (!productId) return;

        try {
            const response = await sentimentAPI.getProductSummary(productId);
            setSummary(response.data);
        } catch (err) {
            console.error('Error fetching sentiment summary:', err);
            // Don't set error for summary, just log it
        }
    }, [productId]);

    // Fetch reviews with sorting
    const fetchReviews = useCallback(async (order = sortOrder) => {
        if (!productId) return;

        setLoading(true);
        setError(null);

        try {
            const response = await sentimentAPI.getProductReviews(productId, order);
            setReviews(response.data?.reviews || response.data || []);
        } catch (err) {
            console.error('Error fetching reviews:', err);
            setError('Failed to load reviews');
        } finally {
            setLoading(false);
        }
    }, [productId, sortOrder]);

    // Initial fetch
    useEffect(() => {
        if (productId) {
            fetchSummary();
            fetchReviews();
        }
    }, [productId, fetchSummary, fetchReviews]);

    // Change sort order
    const changeSort = useCallback((order) => {
        setSortOrder(order);
        fetchReviews(order);
    }, [fetchReviews]);

    return {
        summary,
        reviews,
        loading,
        error,
        sortOrder,
        changeSort,
        refresh: () => {
            fetchSummary();
            fetchReviews();
        }
    };
}

/**
 * useSentimentSummary - Simplified hook for just the summary
 */
export function useSentimentSummary(productId) {
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!productId) return;

        const fetchSummary = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await sentimentAPI.getProductSummary(productId);
                setSummary(response.data);
            } catch (err) {
                console.error('Error fetching sentiment summary:', err);
                setError('Failed to load sentiment data');
            } finally {
                setLoading(false);
            }
        };

        fetchSummary();
    }, [productId]);

    return { summary, loading, error };
}

export default useSentiment;
