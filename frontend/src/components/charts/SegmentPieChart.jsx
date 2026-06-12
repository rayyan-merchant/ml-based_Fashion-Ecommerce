import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

/**
 * SegmentPieChart - Pie chart for customer segment distribution
 * @param {Array} segments - Array of segment objects with name, count/value
 * @param {string} title - Chart title
 * @param {boolean} loading - Loading state
 */
export default function SegmentPieChart({
    segments = [],
    title = 'Customer Segments',
    loading = false
}) {
    const COLORS = [
        '#8b5cf6', // Purple
        '#3b82f6', // Blue
        '#10b981', // Green
        '#f59e0b', // Amber
        '#ef4444', // Red
        '#ec4899', // Pink
        '#06b6d4', // Cyan
        '#84cc16', // Lime
    ];

    if (loading) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse mb-4" />
                <div className="h-64 flex items-center justify-center">
                    <div className="w-48 h-48 bg-gray-100 rounded-full animate-pulse" />
                </div>
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
        value: seg.count || seg.value || seg.percentage,
        color: COLORS[index % COLORS.length]
    }));

    const totalCustomers = chartData.reduce((sum, seg) => sum + seg.value, 0);

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            const percentage = ((data.value / totalCustomers) * 100).toFixed(1);
            return (
                <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
                    <p className="font-medium text-gray-900">{data.name}</p>
                    <p className="text-sm text-gray-600">
                        {data.value.toLocaleString()} customers ({percentage}%)
                    </p>
                </div>
            );
        }
        return null;
    };

    const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
        if (percent < 0.05) return null; // Don't show label if less than 5%

        const RADIAN = Math.PI / 180;
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);

        return (
            <text
                x={x}
                y={y}
                fill="white"
                textAnchor="middle"
                dominantBaseline="central"
                className="text-xs font-medium"
            >
                {`${(percent * 100).toFixed(0)}%`}
            </text>
        );
    };

    return (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                    <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={renderCustomLabel}
                        outerRadius={100}
                        innerRadius={40}
                        fill="#8884d8"
                        dataKey="value"
                        animationBegin={0}
                        animationDuration={800}
                    >
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                </PieChart>
            </ResponsiveContainer>

            {/* Legend */}
            <div className="mt-4 grid grid-cols-2 gap-2">
                {chartData.map((seg, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                        <div
                            className="w-3 h-3 rounded-full flex-shrink-0"
                            style={{ backgroundColor: seg.color }}
                        />
                        <span className="text-gray-600 truncate">{seg.name}</span>
                        <span className="text-gray-400 ml-auto">{seg.value.toLocaleString()}</span>
                    </div>
                ))}
            </div>

            {/* Total */}
            <div className="mt-4 pt-3 border-t border-gray-100 text-center">
                <span className="text-sm text-gray-500">Total: </span>
                <span className="font-semibold text-gray-900">{totalCustomers.toLocaleString()} customers</span>
            </div>
        </div>
    );
}
