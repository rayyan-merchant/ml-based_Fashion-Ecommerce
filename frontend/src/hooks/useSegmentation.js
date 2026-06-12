import { useState, useEffect, useCallback } from 'react';
import { segmentationAPI } from '../api/segmentationAPI';

/**
 * useSegmentation - Custom hook for segmentation data
 * @param {string} customerId - Customer ID for individual segment
 */
export function useSegmentation(customerId = null) {
    const [customerSegment, setCustomerSegment] = useState(null);
    const [overview, setOverview] = useState(null);
    const [profiles, setProfiles] = useState([]);
    const [definitions, setDefinitions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch customer segment
    const fetchCustomerSegment = useCallback(async () => {
        if (!customerId) return;

        try {
            const response = await segmentationAPI.getCustomerSegment(customerId);
            setCustomerSegment(response.data);
        } catch (err) {
            console.error('Error fetching customer segment:', err);
        }
    }, [customerId]);

    // Fetch overview data
    const fetchOverview = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await segmentationAPI.getSegmentOverview();
            setOverview(response.data);
        } catch (err) {
            console.error('Error fetching segment overview:', err);
            setError('Failed to load segment overview');
        } finally {
            setLoading(false);
        }
    }, []);

    // Fetch profiles
    const fetchProfiles = useCallback(async () => {
        try {
            const response = await segmentationAPI.getSegmentProfiles();
            setProfiles(response.data?.profiles || response.data || []);
        } catch (err) {
            console.error('Error fetching segment profiles:', err);
        }
    }, []);

    // Fetch definitions from the live segmentation endpoint.
    const fetchDefinitions = useCallback(async () => {
        try {
            const response = await segmentationAPI.getSegmentDefinitions();
            const defs = response.data?.definitions || response.data || [];
            setDefinitions(defs);
        } catch (err) {
            console.error('Error fetching segment definitions:', err);
        }
    }, []);

    // Fetch all data for admin dashboard
    const fetchAll = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            await Promise.all([
                fetchOverview(),
                fetchProfiles(),
                fetchDefinitions()
            ]);
        } catch (err) {
            setError('Failed to load segmentation data');
        } finally {
            setLoading(false);
        }
    }, [fetchOverview, fetchProfiles, fetchDefinitions]);

    // Auto-fetch customer segment if ID provided
    useEffect(() => {
        if (customerId) {
            fetchCustomerSegment();
        }
    }, [customerId, fetchCustomerSegment]);

    return {
        customerSegment,
        overview,
        profiles,
        definitions,
        loading,
        error,
        fetchCustomerSegment,
        fetchOverview,
        fetchProfiles,
        fetchDefinitions,
        fetchAll
    };
}

/**
 * useCustomerSegment - Simplified hook for just customer segment
 */
export function useCustomerSegment(customerId) {
    const [segment, setSegment] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!customerId) return;

        const fetchSegment = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await segmentationAPI.getCustomerSegment(customerId);
                setSegment(response.data);
            } catch (err) {
                console.error('Error fetching customer segment:', err);
                setError('Failed to load segment data');
            } finally {
                setLoading(false);
            }
        };

        fetchSegment();
    }, [customerId]);

    return { segment, loading, error };
}

export default useSegmentation;
