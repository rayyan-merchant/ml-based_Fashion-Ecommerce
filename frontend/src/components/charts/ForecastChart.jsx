import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Area,
    ComposedChart
} from 'recharts';

/**
 * ForecastChart - Line chart with historical + forecast lines
 * @param {Array} data - Chart data with date, actual, forecast fields
 * @param {string} title - Chart title
 * @param {boolean} loading - Loading state
 * @param {boolean} showConfidenceInterval - Show prediction interval
 */
export default function ForecastChart({
    data = [],
    title = 'Sales Forecast',
    loading = false,
    showConfidenceInterval = true
}) {
    if (loading) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse mb-4" />
                <div className="h-72 bg-gray-100 rounded-lg animate-pulse" />
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
                <div className="h-72 flex items-center justify-center text-gray-400">
                    No forecast data available
                </div>
            </div>
        );
    }

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
                    <p className="font-medium text-gray-900 mb-1">{label}</p>
                    {payload.map((entry, index) => (
                        <p key={index} style={{ color: entry.color }} className="text-sm">
                            {entry.name}: {entry.value?.toLocaleString()}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => {
                            const date = new Date(value);
                            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                        }}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />

                    {/* Confidence Interval Area */}
                    {showConfidenceInterval && (
                        <Area
                            type="monotone"
                            dataKey="upper_bound"
                            stackId="1"
                            stroke="none"
                            fill="#3b82f6"
                            fillOpacity={0.1}
                        />
                    )}

                    {/* Historical Line */}
                    <Line
                        type="monotone"
                        dataKey="actual"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                        name="Actual"
                    />

                    {/* Forecast Line */}
                    <Line
                        type="monotone"
                        dataKey="forecast"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        dot={{ r: 3 }}
                        activeDot={{ r: 5 }}
                        name="Forecast"
                    />
                </ComposedChart>
            </ResponsiveContainer>

            {/* Legend explanation */}
            <div className="mt-4 flex items-center justify-center gap-6 text-sm text-gray-500">
                <div className="flex items-center gap-2">
                    <div className="w-4 h-0.5 bg-green-500" />
                    <span>Historical</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-0.5 bg-blue-500 border-dashed" style={{ borderTop: '2px dashed #3b82f6' }} />
                    <span>Forecast</span>
                </div>
                {showConfidenceInterval && (
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-3 bg-blue-100 rounded" />
                        <span>Confidence Interval</span>
                    </div>
                )}
            </div>
        </div>
    );
}
