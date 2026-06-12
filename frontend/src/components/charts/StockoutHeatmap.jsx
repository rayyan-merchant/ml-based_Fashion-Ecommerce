import React from 'react';

/**
 * StockoutHeatmap - Grid heatmap showing stockout risk levels
 * @param {Array} data - Array of products with risk levels
 * @param {string} title - Chart title
 * @param {boolean} loading - Loading state
 */
export default function StockoutHeatmap({
    data = [],
    title = 'Stockout Risk Analysis',
    loading = false
}) {
    if (loading) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse mb-4" />
                <div className="grid grid-cols-5 gap-2">
                    {Array.from({ length: 20 }).map((_, i) => (
                        <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
                    ))}
                </div>
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
                <div className="h-48 flex items-center justify-center text-gray-400">
                    No stockout data available
                </div>
            </div>
        );
    }

    const getRiskStyle = (riskLevel) => {
        // riskLevel can be a string ('high', 'medium', 'low') or a number (0-1)
        if (typeof riskLevel === 'string') {
            switch (riskLevel.toLowerCase()) {
                case 'critical':
                case 'high':
                    return { bg: 'bg-red-500', text: 'text-white', label: 'High Risk' };
                case 'medium':
                case 'warning':
                    return { bg: 'bg-orange-400', text: 'text-white', label: 'Medium Risk' };
                case 'low':
                    return { bg: 'bg-yellow-300', text: 'text-yellow-900', label: 'Low Risk' };
                default:
                    return { bg: 'bg-green-400', text: 'text-white', label: 'Safe' };
            }
        }

        // Numeric risk level (0-1)
        if (riskLevel >= 0.8) return { bg: 'bg-red-500', text: 'text-white', label: 'Critical' };
        if (riskLevel >= 0.6) return { bg: 'bg-orange-500', text: 'text-white', label: 'High' };
        if (riskLevel >= 0.4) return { bg: 'bg-yellow-400', text: 'text-yellow-900', label: 'Medium' };
        if (riskLevel >= 0.2) return { bg: 'bg-lime-400', text: 'text-lime-900', label: 'Low' };
        return { bg: 'bg-green-400', text: 'text-white', label: 'Safe' };
    };

    // Sort by risk level (highest first)
    const sortedData = [...data].sort((a, b) => {
        const scoreA = typeof a.risk_level === 'number' ? a.risk_level :
            a.risk_level === 'high' ? 1 : a.risk_level === 'medium' ? 0.5 : 0;
        const scoreB = typeof b.risk_level === 'number' ? b.risk_level :
            b.risk_level === 'high' ? 1 : b.risk_level === 'medium' ? 0.5 : 0;
        return scoreB - scoreA;
    });

    // Count by risk level
    const riskCounts = {
        high: sortedData.filter(d => ['high', 'critical'].includes(String(d.risk_level).toLowerCase()) || d.risk_level >= 0.6).length,
        medium: sortedData.filter(d => d.risk_level === 'medium' || (d.risk_level >= 0.3 && d.risk_level < 0.6)).length,
        low: sortedData.filter(d => d.risk_level === 'low' || d.risk_level === 'safe' || d.risk_level < 0.3).length
    };

    return (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
                <div className="flex gap-3 text-sm">
                    <span className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-red-500" />
                        <span className="text-gray-600">{riskCounts.high} High</span>
                    </span>
                    <span className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-orange-400" />
                        <span className="text-gray-600">{riskCounts.medium} Medium</span>
                    </span>
                    <span className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-green-400" />
                        <span className="text-gray-600">{riskCounts.low} Low</span>
                    </span>
                </div>
            </div>

            {/* Heatmap Grid */}
            <div className="grid grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2">
                {sortedData.slice(0, 24).map((item, index) => {
                    const style = getRiskStyle(item.risk_level);
                    return (
                        <div
                            key={item.product_id || index}
                            className={`${style.bg} ${style.text} rounded-lg p-3 cursor-pointer hover:opacity-90 transition-opacity group relative`}
                        >
                            <p className="font-medium text-xs truncate">{item.name || item.product_name}</p>
                            {item.days_until_stockout !== undefined && (
                                <p className="text-xs opacity-80 mt-1">
                                    {item.days_until_stockout} days
                                </p>
                            )}

                            {/* Tooltip */}
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                                <p className="font-medium">{item.name || item.product_name}</p>
                                <p>Risk: {style.label}</p>
                                {item.days_until_stockout !== undefined && (
                                    <p>Stockout in: {item.days_until_stockout} days</p>
                                )}
                                {item.current_stock !== undefined && (
                                    <p>Current Stock: {item.current_stock}</p>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* View More */}
            {data.length > 24 && (
                <p className="text-center text-sm text-gray-500 mt-4">
                    Showing top 24 of {data.length} products at risk
                </p>
            )}

            {/* Legend */}
            <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-2">Risk Level Scale:</p>
                <div className="flex h-3 rounded-full overflow-hidden">
                    <div className="flex-1 bg-green-400" title="Safe" />
                    <div className="flex-1 bg-lime-400" title="Low Risk" />
                    <div className="flex-1 bg-yellow-400" title="Medium Risk" />
                    <div className="flex-1 bg-orange-400" title="High Risk" />
                    <div className="flex-1 bg-red-500" title="Critical" />
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>Safe</span>
                    <span>Critical</span>
                </div>
            </div>
        </div>
    );
}
