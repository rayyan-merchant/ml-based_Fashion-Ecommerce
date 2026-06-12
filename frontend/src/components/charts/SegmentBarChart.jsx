import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts';

/**
 * SegmentBarChart - Bar chart comparing segment sizes
 * @param {Array} segments - Array of segment objects
 * @param {string} title - Chart title
 * @param {boolean} loading - Loading state
 * @param {boolean} horizontal - Use horizontal bars
 */
export default function SegmentBarChart({
    segments = [],
    title = 'Segments by Size',
    loading = false,
    horizontal = false
}) {
    const COLORS = [
        '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b',
        '#ef4444', '#ec4899', '#06b6d4', '#84cc16'
    ];

    if (loading) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse mb-4" />
                <div className="h-64 bg-gray-100 rounded-lg animate-pulse" />
            </div>
        );
    }

    if (!segments || segments.length === 0) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
                <div className="h-64 flex items-center justify-center text-gray-400">
                    No segment data available
                </div>
            </div>
        );
    }

    const chartData = segments.map((seg, index) => ({
        name: seg.segment_name || seg.name,
        value: seg.count || seg.value,
        color: COLORS[index % COLORS.length]
    }));

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
                    <p className="font-medium text-gray-900">{data.name}</p>
                    <p className="text-sm text-gray-600">{data.value.toLocaleString()} customers</p>
                </div>
            );
        }
        return null;
    };

    if (horizontal) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
                <ResponsiveContainer width="100%" height={segments.length * 50 + 40}>
                    <BarChart
                        data={chartData}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={true} vertical={false} />
                        <XAxis type="number" tick={{ fontSize: 12 }} />
                        <YAxis
                            type="category"
                            dataKey="name"
                            tick={{ fontSize: 12 }}
                            width={90}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        );
    }

    return (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                        dataKey="name"
                        tick={{ fontSize: 11 }}
                        angle={-45}
                        textAnchor="end"
                        height={60}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
