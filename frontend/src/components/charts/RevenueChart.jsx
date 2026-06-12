import React from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';
import { formatPrice } from '../../utils/price';

/**
 * RevenueChart - Revenue prediction visualization with gradient area
 * @param {Array} data - Revenue data array
 * @param {string} title - Chart title
 * @param {boolean} loading - Loading state
 */
export default function RevenueChart({
    data = [],
    title = 'Revenue Analytics',
    loading = false
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
                    No revenue data available
                </div>
            </div>
        );
    }

    // Calculate totals
    const totalRevenue = data.reduce((sum, d) => sum + (d.revenue || d.value || 0), 0);
    const avgRevenue = totalRevenue / data.length;

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
                    <p className="font-medium text-gray-900 mb-1">{label}</p>
                    <p className="text-sm text-green-600">
                        Revenue: {formatPrice(payload[0].value)}
                    </p>
                    {payload[0].payload.predicted && (
                        <p className="text-xs text-gray-400 mt-1">Predicted</p>
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
                <div className="text-right">
                    <p className="text-2xl font-bold text-green-600">{formatPrice(totalRevenue)}</p>
                    <p className="text-sm text-gray-500">Total Revenue</p>
                </div>
            </div>

            <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => {
                            if (!value) return '';
                            const date = new Date(value);
                            return date.toLocaleDateString('en-US', { month: 'short' });
                        }}
                    />
                    <YAxis
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => `Rs ${Math.round(value / 1000).toLocaleString("en-PK")}k`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Area
                        type="monotone"
                        dataKey="revenue"
                        stroke="#10b981"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#revenueGradient)"
                    />
                </AreaChart>
            </ResponsiveContainer>

            {/* Stats Row */}
            <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-3 gap-4 text-center">
                <div>
                    <p className="text-sm text-gray-500">Average</p>
                    <p className="font-semibold text-gray-900">{formatPrice(avgRevenue)}</p>
                </div>
                <div>
                    <p className="text-sm text-gray-500">Highest</p>
                    <p className="font-semibold text-green-600">
                        {formatPrice(Math.max(...data.map(d => d.revenue || d.value || 0)))}
                    </p>
                </div>
                <div>
                    <p className="text-sm text-gray-500">Lowest</p>
                    <p className="font-semibold text-red-600">
                        {formatPrice(Math.min(...data.map(d => d.revenue || d.value || 0)))}
                    </p>
                </div>
            </div>
        </div>
    );
}
