import React, { useEffect } from 'react';
import { useAnalytics } from '../../hooks/useForecast';
import {
    RevenueChart,
    MonthlyGrowthChart,
    StockoutHeatmap,
    LifecycleStageCard,
    AggregateChart
} from '../../components/charts';
import { TrendCard, SkeletonLoader } from '../../components/ml';

/**
 * MLAnalyticsDashboard - Comprehensive ML Analytics Dashboard
 * Features:
 * - Revenue analytics
 * - Trends visualization
 * - Monthly growth chart
 * - Stockout heatmap
 * - Lifecycle stages
 * - Aggregate views
 */
export default function MLAnalyticsDashboard() {
    const {
        revenue,
        trends,
        growth,
        stockout,
        lifecycle,
        aggregate,
        _errors,
        loading,
        error,
        fetchAll
    } = useAnalytics();

    useEffect(() => {
        fetchAll();
    }, [fetchAll]);

    // Transform data for charts
    const revenueData = revenue?.history || revenue?.data || [];
    const growthData = growth?.growth || growth?.data || [];
    const stockoutData = stockout?.stockout_risks || stockout?.products || [];
    const lifecycleData = lifecycle?.products || [];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-2xl p-6 text-white">
                <h1 className="text-2xl font-bold mb-2">ML Analytics Dashboard</h1>
                <p className="text-emerald-100">Comprehensive business intelligence powered by machine learning</p>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
                    {error}
                    <button onClick={fetchAll} className="ml-4 underline">Retry</button>
                </div>
            )}

            {_errors?.length > 0 && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
                    Some ML analytics modules are unavailable, so this page is showing the modules that responded.
                </div>
            )}

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {loading ? (
                    <>
                        <SkeletonLoader variant="stat" />
                        <SkeletonLoader variant="stat" />
                        <SkeletonLoader variant="stat" />
                        <SkeletonLoader variant="stat" />
                    </>
                ) : (
                    <>
                        <TrendCard
                            title="Total Revenue"
                            currentValue={revenue?.total_revenue || 0}
                            previousValue={revenue?.previous_revenue || 0}
                            format="currency"
                        />
                        <TrendCard
                            title="Predicted Revenue"
                            currentValue={revenue?.predicted_revenue || 0}
                            previousValue={revenue?.total_revenue || 0}
                            format="currency"
                        />
                        <div className="bg-white border border-gray-200 rounded-xl p-5">
                            <p className="text-sm text-gray-500 mb-1">Products at Risk</p>
                            <p className="text-3xl font-bold text-red-600">
                                {stockoutData.filter(p => p.risk_level === 'high' || p.risk_level >= 0.6).length}
                            </p>
                            <p className="text-xs text-gray-400 mt-2">High stockout risk</p>
                        </div>
                        <div className="bg-white border border-gray-200 rounded-xl p-5">
                            <p className="text-sm text-gray-500 mb-1">Trending Up</p>
                            <p className="text-3xl font-bold text-green-600">
                                {(trends?.trends || []).filter(t => t.direction === 'up').length}
                            </p>
                            <p className="text-xs text-gray-400 mt-2">Products with positive trend</p>
                        </div>
                    </>
                )}
            </div>

            {/* Revenue & Growth Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <RevenueChart
                    data={revenueData}
                    title="Revenue Analytics"
                    loading={loading}
                />
                <MonthlyGrowthChart
                    data={growthData}
                    title="Monthly Growth"
                    loading={loading}
                />
            </div>

            {/* Trends Section */}
            {trends?.trends && trends.trends.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-xl p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Product Trends</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                        {trends.trends.slice(0, 12).map((trend, index) => (
                            <div
                                key={trend.id || index}
                                className={`p-3 rounded-lg ${trend.direction === 'up'
                                        ? 'bg-green-50 border border-green-200'
                                        : trend.direction === 'down'
                                            ? 'bg-red-50 border border-red-200'
                                            : 'bg-gray-50 border border-gray-200'
                                    }`}
                            >
                                <p className="text-sm font-medium text-gray-900 truncate">{trend.name}</p>
                                <div className={`flex items-center gap-1 mt-1 text-sm font-semibold ${trend.direction === 'up' ? 'text-green-600' :
                                        trend.direction === 'down' ? 'text-red-600' : 'text-gray-600'
                                    }`}>
                                    {trend.direction === 'up' ? 'Up' : trend.direction === 'down' ? 'Down' : 'Stable'}
                                    {trend.change_percent !== undefined && (
                                        <span>{Math.abs(Number(trend.change_percent || 0)).toFixed(1)}%</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Stockout & Lifecycle */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <StockoutHeatmap
                    data={stockoutData}
                    title="Stockout Risk Analysis"
                    loading={loading}
                />
                <LifecycleStageCard
                    products={lifecycleData}
                    title="Product Lifecycle Stages"
                    loading={loading}
                />
            </div>

            {/* Aggregate Chart */}
            <AggregateChart
                data={{
                    weekly: aggregate?.weekly || [],
                    monthly: aggregate?.monthly || []
                }}
                title="Sales Aggregate View"
                loading={loading}
            />
        </div>
    );
}
