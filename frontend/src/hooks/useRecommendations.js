import { useState, useEffect, useCallback, useRef } from 'react';
import { recommendationAPI } from '../api/recommendationAPI';
import { groupProductVariants } from '../utils/productVariants';

/**
 * useRecommendations - Custom hook for fetching recommendation data
 * @param {string} customerId - Customer ID for personalized recommendations
 * @param {object} options - Configuration options
 */
export function useRecommendations(customerId, options = {}) {
    const {
        fetchPersonalized = true,
        fetchTrending = true,
        fetchAlsoBought = false,
        fetchInteractions = false,
        cacheTTL = 5 * 60 * 1000, // 5 minutes
        limit = 12
    } = options;

    const [data, setData] = useState({
        personalized: [],
        trending: [],
        alsoBought: [],
        interactions: []
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const cacheRef = useRef({});
    const lastFetchRef = useRef({});

    const isCacheValid = useCallback((key) => {
        const lastFetch = lastFetchRef.current[key];
        if (!lastFetch) return false;
        return Date.now() - lastFetch < cacheTTL;
    }, [cacheTTL]);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);

        const promises = [];
        const keys = [];

        try {
            // Trending (available for all users)
            if (fetchTrending && !isCacheValid('trending')) {
                promises.push(recommendationAPI.getTrending(limit));
                keys.push('trending');
            }

            // Personalized (logged-in users only)
            if (customerId && fetchPersonalized && !isCacheValid('personalized')) {
                promises.push(recommendationAPI.getPersonalized(customerId, limit));
                keys.push('personalized');
            }

            // Also Bought
            if (customerId && fetchAlsoBought && !isCacheValid('alsoBought')) {
                promises.push(recommendationAPI.getCustomersAlsoBought(customerId, limit));
                keys.push('alsoBought');
            }

            // Interactions
            if (customerId && fetchInteractions && !isCacheValid('interactions')) {
                promises.push(recommendationAPI.getBasedOnInteractions(customerId, limit));
                keys.push('interactions');
            }

            if (promises.length > 0) {
                const results = await Promise.allSettled(promises);

                const newData = { ...cacheRef.current };

                results.forEach((result, index) => {
                    const key = keys[index];
                    if (result.status === 'fulfilled') {
                        const responseData = result.value.data?.recommendations ||
                            result.value.data?.products ||
                            result.value.data?.similar_items ||
                            result.value.data?.trending_items ||
                            result.value.data || [];
                        const grouped = groupProductVariants(responseData);
                        newData[key] = grouped;
                        cacheRef.current[key] = grouped;
                        lastFetchRef.current[key] = Date.now();
                    } else {
                        console.warn(`Failed to fetch ${key}:`, result.reason);
                    }
                });

                setData(newData);
            } else {
                // All data is cached
                setData({ ...cacheRef.current });
            }
        } catch (err) {
            console.error('Error fetching recommendations:', err);
            setError('Failed to load recommendations');
        } finally {
            setLoading(false);
        }
    }, [customerId, fetchPersonalized, fetchTrending, fetchAlsoBought, fetchInteractions, limit, isCacheValid]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const refresh = useCallback(() => {
        // Clear cache and refetch
        cacheRef.current = {};
        lastFetchRef.current = {};
        fetchData();
    }, [fetchData]);

    return {
        personalized: data.personalized || [],
        trending: data.trending || [],
        alsoBought: data.alsoBought || [],
        interactions: data.interactions || [],
        loading,
        error,
        refresh
    };
}

/**
 * useSimilarItems - Hook for fetching similar items for a product
 */
export function useSimilarItems(productId, limit = 12) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!productId) return;

        const fetchSimilar = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await recommendationAPI.getSimilarItems(productId, limit);
                setItems(response.data?.products || response.data || []);
            } catch (err) {
                console.error('Error fetching similar items:', err);
                setError('Failed to load similar items');
            } finally {
                setLoading(false);
            }
        };

        fetchSimilar();
    }, [productId, limit]);

    return { items, loading, error };
}

/**
 * useCartRecommendations - Hook for cart-based recommendations
 */
export function useCartRecommendations(customerId, limit = 8) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!customerId) return;

        const fetchCartRecs = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await recommendationAPI.getCartBased(customerId, limit);
                setItems(response.data?.recommendations || response.data || []);
            } catch (err) {
                console.error('Error fetching cart recommendations:', err);
                setError('Failed to load cart recommendations');
            } finally {
                setLoading(false);
            }
        };

        fetchCartRecs();
    }, [customerId, limit]);

    return { items, loading, error };
}

export default useRecommendations;
