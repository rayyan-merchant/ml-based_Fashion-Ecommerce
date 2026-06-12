import React, { useState } from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';
import { formatPrice } from '../../utils/price';

/**
 * AggregateChart - Weekly/Monthly toggle bar chart
 * @param {Object} data - Object with weekly and monthly arrays
 * @param {string} title - Chart title
 * @param {boolean} loading - Loading state
 */
export default function AggregateChart({
    data = { weekly: [], monthly: [] },
    title = 'Sales Aggregate',
    loading = false
}) {
    const [period, setPeriod] = useState('weekly');

    if (loading) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="flex justify-between items-center mb-4">
                    <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse" />
                    <div className="h-8 bg-gray-200 rounded w-32 animate-pulse" />
                </div>
                <div className="h-64 bg-gray-100 rounded-lg animate-pulse" />
            </div>
        );
    }

    const chartData = (period === 'weekly' ? (data.weekly || []) : (data.monthly || []))
        .map(item => ({
            ...item,
            label: item.week || item.month || item.date,
            value: item.value ?? item.revenue ?? item.sales ?? 0
        }));

    if (chartData.length === 0) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
                    <div className="flex bg-gray-100 rounded-lg p-1">
                        <button
                            onClick={() => setPeriod('weekly')}
                            className={`px-3 py-1 text-sm rounded-md transition-colors ${period === 'weekly' ? 'bg-white shadow text-gray-900' : 'text-gray-500'
                                }`}
                        >
                            Weekly
                        </button>
                        <button
                            onClick={() => setPeriod('monthly')}
                            className={`px-3 py-1 text-sm rounded-md transition-colors ${period === 'monthly' ? 'bg-white shadow text-gray-900' : 'text-gray-500'
                                }`}
                        >
                            Monthly
                        </button>
                    </div>
                </div>
                <div className="h-64 flex items-center justify-center text-gray-400">
                    No data available for {period} view
                </div>
            </div>
        );
    }

    const total = chartData.reduce((sum, d) => sum + (d.value || d.sales || 0), 0);

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
                    <p className="font-medium text-gray-900 mb-1">{label}</p>
                    <p className="text-sm text-blue-600">
                        Total: {formatPrice(payload[0].value)}
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex justify-between items-center mb-4">
                <div>
                    <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
                    <p className="text-sm text-gray-500">
                        Total: <span className="font-medium text-gray-900">{formatPrice(total)}</span>
                    </p>
                </div>

                {/* Period Toggle */}
                <div className="flex bg-gray-100 rounded-lg p-1">
                    <button
                        onClick={() => setPeriod('weekly')}
                        className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${period === 'weekly'
                                ? 'bg-white shadow text-gray-900'
                                : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        Weekly
                    </button>
                    <button
                        onClick={() => setPeriod('monthly')}
                        className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${period === 'monthly'
                                ? 'bg-white shadow text-gray-900'
                                : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        Monthly
                    </button>
                </div>
            </div>

            <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                    <XAxis
                        dataKey="label"
                        tick={{ fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                    />
                    <YAxis
                        tick={{ fontSize: 11 }}
                        tickFormatter={(value) => `Rs ${Math.round(value / 1000).toLocaleString("en-PK")}k`}
                        axisLine={false}
                        tickLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar
                        dataKey="value"
                        fill="#3b82f6"
                        radius={[4, 4, 0, 0]}
                        maxBarSize={50}
                    />
                </BarChart>
            </ResponsiveContainer>

            {/* Summary Stats */}
            <div className="mt-4 pt-3 border-t border-gray-100 grid grid-cols-3 gap-4 text-center text-sm">
                <div>
                    <p className="text-gray-500">Average</p>
                    <p className="font-semibold text-gray-900">
                        {formatPrice(total / chartData.length)}
                    </p>
                </div>
                <div>
                    <p className="text-gray-500">Peak</p>
                    <p className="font-semibold text-green-600">
                        {formatPrice(Math.max(...chartData.map(d => d.value || d.sales || 0)))}
                    </p>
                </div>
                <div>
                    <p className="text-gray-500">Periods</p>
                    <p className="font-semibold text-gray-900">{chartData.length}</p>
                </div>
            </div>
        </div>
    );
}
