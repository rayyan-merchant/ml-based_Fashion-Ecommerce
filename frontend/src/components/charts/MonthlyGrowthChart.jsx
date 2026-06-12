import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';
import { formatPrice } from '../../utils/price';

/**
 * MonthlyGrowthChart - Line chart with month-over-month comparison
 * @param {Array} data - Growth data with month, value, growth_rate fields
 * @param {string} title - Chart title
 * @param {boolean} loading - Loading state
 */
export default function MonthlyGrowthChart({
    data = [],
    title = 'Monthly Growth',
    loading = false
}) {
    if (loading) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse mb-4" />
                <div className="h-64 bg-gray-100 rounded-lg animate-pulse" />
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
                <div className="h-64 flex items-center justify-center text-gray-400">
                    No growth data available
                </div>
            </div>
        );
    }

    // Calculate average growth
    const avgGrowth = data.reduce((sum, d) => sum + (d.growth_rate || 0), 0) / data.length;

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const growthRate = payload[0].payload.growth_rate;
            return (
                <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
                    <p className="font-medium text-gray-900 mb-1">{label}</p>
                    <p className="text-sm text-gray-600">
                        Revenue: {formatPrice(payload[0].value)}
                    </p>
                    {growthRate !== undefined && (
                        <p className={`text-sm font-medium ${growthRate >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            Growth: {growthRate >= 0 ? '+' : ''}{growthRate.toFixed(1)}%
                        </p>
                    )}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${avgGrowth >= 0
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                    Avg: {avgGrowth >= 0 ? '+' : ''}{avgGrowth.toFixed(1)}%
                </div>
            </div>

            <ResponsiveContainer width="100%" height={260}>
                <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                        dataKey="month"
                        tick={{ fontSize: 12 }}
                    />
                    <YAxis
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => `Rs ${Math.round(value / 1000).toLocaleString("en-PK")}k`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <ReferenceLine y={0} stroke="#e5e7eb" />
                    <Line
                        type="monotone"
                        dataKey="revenue"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={(props) => {
                            const { cx, cy, payload } = props;
                            const isPositive = (payload.growth_rate || 0) >= 0;
                            return (
                                <circle
                                    cx={cx}
                                    cy={cy}
                                    r={5}
                                    fill={isPositive ? '#10b981' : '#ef4444'}
                                    stroke="white"
                                    strokeWidth={2}
                                />
                            );
                        }}
                        activeDot={{ r: 7 }}
                    />
                </LineChart>
            </ResponsiveContainer>

            {/* Growth indicators row */}
            <div className="mt-4 pt-3 border-t border-gray-100 flex gap-2 overflow-x-auto">
                {data.slice(-6).map((item, index) => {
                    const growth = item.growth_rate || 0;
                    const isPositive = growth >= 0;
                    return (
                        <div
                            key={index}
                            className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium ${isPositive ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                                }`}
                        >
                            {item.month}: {isPositive ? '+' : ''}{growth.toFixed(1)}%
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
