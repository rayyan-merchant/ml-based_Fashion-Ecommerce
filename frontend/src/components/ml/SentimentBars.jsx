import React from 'react';

/**
 * SentimentBars - Displays sentiment distribution as colored horizontal bars
 * @param {number} positive - Percentage of positive reviews (0-100)
 * @param {number} neutral - Percentage of neutral reviews (0-100)
 * @param {number} negative - Percentage of negative reviews (0-100)
 * @param {number} totalReviews - Total number of reviews
 * @param {boolean} showLabels - Whether to show percentage labels
 * @param {string} size - 'sm' | 'md' | 'lg'
 */
export default function SentimentBars({
    positive = 0,
    neutral = 0,
    negative = 0,
    totalReviews = 0,
    showLabels = true,
    size = 'md'
}) {
    const heights = {
        sm: 'h-2',
        md: 'h-3',
        lg: 'h-4'
    };

    const barHeight = heights[size] || heights.md;

    const sentiments = [
        { label: 'Positive', value: positive, color: 'bg-green-500', textColor: 'text-green-600' },
        { label: 'Neutral', value: neutral, color: 'bg-yellow-500', textColor: 'text-yellow-600' },
        { label: 'Negative', value: negative, color: 'bg-red-500', textColor: 'text-red-600' },
    ];

    return (
        <div className="w-full">
            {/* Summary Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-green-600">{positive}%</span>
                    <span className="text-gray-500 text-sm">positive</span>
                </div>
                {totalReviews > 0 && (
                    <span className="text-sm text-gray-400">{totalReviews} reviews</span>
                )}
            </div>

            {/* Stacked Bar */}
            <div className={`w-full ${barHeight} rounded-full overflow-hidden flex bg-gray-200`}>
                {sentiments.map((sentiment) => (
                    sentiment.value > 0 && (
                        <div
                            key={sentiment.label}
                            className={`${sentiment.color} transition-all duration-300`}
                            style={{ width: `${sentiment.value}%` }}
                            title={`${sentiment.label}: ${sentiment.value}%`}
                        />
                    )
                ))}
            </div>

            {/* Labels */}
            {showLabels && (
                <div className="flex justify-between mt-2 text-xs">
                    {sentiments.map((sentiment) => (
                        <div key={sentiment.label} className="flex items-center gap-1">
                            <div className={`w-2 h-2 rounded-full ${sentiment.color}`} />
                            <span className={sentiment.textColor}>
                                {sentiment.label} ({sentiment.value}%)
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
