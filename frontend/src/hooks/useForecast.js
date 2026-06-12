import { useState, useEffect, useCallback } from 'react';
import { forecastingAPI } from '../api/forecastingAPI';
import { analyticsAPI } from '../api/analyticsAPI';

/**
 * useForecast - Custom hook for forecast data
 * @param {string} articleId - Optional article ID for specific forecast
 * @param {string} categoryId - Optional category ID for category forecast
 */
export function useForecast(articleId = null, categoryId = null) {
    const [articleForecast, setArticleForecast] = useState(null);
    const [categoryForecast, setCategoryForecast] = useState(null);
    const [allForecasts, setAllForecasts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch article forecast
    const fetchArticleForecast = useCallback(async (id) => {
        if (!id) return;

        setLoading(true);
        setError(null);

        try {
            const response = await forecastingAPI.getArticleForecast(id);
            setArticleForecast(response.data);
        } catch (err) {
            console.error('Error fetching article forecast:', err);
            setError('Failed to load article forecast');
        } finally {
            setLoading(false);
        }
    }, []);

    // Fetch category forecast
    const fetchCategoryForecast = useCallback(async (id) => {
        if (!id) return;

        setLoading(true);
        setError(null);

        try {
            const response = await forecastingAPI.getCategoryForecast(id);
            setCategoryForecast(response.data);
        } catch (err) {
            console.error('Error fetching category forecast:', err);
            setError('Failed to load category forecast');
        } finally {
            setLoading(false);
        }
    }, []);

    // Fetch all forecasts
    const fetchAllForecasts = useCallback(async (limit = 100) => {
        setLoading(true);
        setError(null);

        try {
            const response = await forecastingAPI.getAllForecasts(limit);
            setAllForecasts(response.data?.forecasts || response.data || []);
        } catch (err) {
            console.error('Error fetching all forecasts:', err);
            setError('Failed to load forecasts');
        } finally {
            setLoading(false);
        }
    }, []);

    // Run pipeline
    const runPipeline = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            await forecastingAPI.runPipeline();
            // Refresh data after pipeline
            await fetchAllForecasts();
        } catch (err) {
            console.error('Error running pipeline:', err);
            setError('Failed to run pipeline');
        } finally {
            setLoading(false);
        }
    }, [fetchAllForecasts]);

    // Auto-fetch if IDs provided
    useEffect(() => {
        if (articleId) {
            fetchArticleForecast(articleId);
        }
    }, [articleId, fetchArticleForecast]);

    useEffect(() => {
        if (categoryId) {
            fetchCategoryForecast(categoryId);
        }
    }, [categoryId, fetchCategoryForecast]);

    return {
        articleForecast,
        categoryForecast,
        allForecasts,
        loading,
        error,
        fetchArticleForecast,
        fetchCategoryForecast,
        fetchAllForecasts,
        runPipeline
    };
}

/**
 * useAnalytics - Custom hook for analytics data
 */
export function useAnalytics() {
    const [data, setData] = useState({
        revenue: null,
        trends: null,
        growth: null,
        stockout: null,
        lifecycle: null,
        aggregate: null
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchAll = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const result = await analyticsAPI.getDashboardData();
            setData(result.data || result);
        } catch (err) {
            console.error('Error fetching analytics:', err);
            setError('Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchRevenue = useCallback(async () => {
        try {
            const response = await analyticsAPI.getRevenue();
            setData(prev => ({ ...prev, revenue: response.data }));
        } catch (err) {
            console.error('Error fetching revenue:', err);
        }
    }, []);

    const fetchTrends = useCallback(async () => {
        try {
            const response = await analyticsAPI.getTrends();
            setData(prev => ({ ...prev, trends: response.data }));
        } catch (err) {
            console.error('Error fetching trends:', err);
        }
    }, []);

    const fetchStockout = useCallback(async () => {
        try {
            const response = await analyticsAPI.getStockoutRisk();
            setData(prev => ({ ...prev, stockout: response.data }));
        } catch (err) {
            console.error('Error fetching stockout:', err);
        }
    }, []);

    const fetchAggregate = useCallback(async (period = 'weekly') => {
        try {
            const response = await analyticsAPI.getAggregatedData(period);
            setData(prev => ({ ...prev, aggregate: response.data }));
        } catch (err) {
            console.error('Error fetching aggregate:', err);
        }
    }, []);

    return {
        ...data,
        loading,
        error,
        fetchAll,
        fetchRevenue,
        fetchTrends,
        fetchStockout,
        fetchAggregate
    };
}

export default useForecast;
