import React from 'react';
import { formatPrice } from '../../utils/price';

/**
 * TrendIndicator - Trend arrows with color coding
 * @param {string} direction - 'up' | 'down' | 'stable'
 * @param {number} value - Percentage change value
 * @param {string} label - Label text
 * @param {string} size - 'sm' | 'md' | 'lg'
 */
export default function TrendIndicator({
    direction = 'stable',
    value = 0,
    label = '',
    size = 'md'
}) {
    const getDirectionStyle = () => {
        switch (direction) {
            case 'up':
                return {
                    bg: 'bg-green-100',
                    text: 'text-green-700',
                    icon: (
                        <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                        </svg>
                    )
                };
            case 'down':
                return {
                    bg: 'bg-red-100',
                    text: 'text-red-700',
                    icon: (
                        <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                        </svg>
                    )
                };
            default:
                return {
                    bg: 'bg-gray-100',
                    text: 'text-gray-700',
                    icon: (
                        <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
                        </svg>
                    )
                };
        }
    };

    const sizes = {
        sm: { icon: 'w-4 h-4', text: 'text-sm', value: 'text-base' },
        md: { icon: 'w-5 h-5', text: 'text-base', value: 'text-lg' },
        lg: { icon: 'w-6 h-6', text: 'text-lg', value: 'text-xl' }
    };

    const style = getDirectionStyle();
    const sizeStyle = sizes[size] || sizes.md;

    return (
        <div className={`inline-flex items-center gap-2 ${style.bg} px-3 py-1.5 rounded-full`}>
            <div className={`${sizeStyle.icon} ${style.text}`}>
                {style.icon}
            </div>
            <span className={`font-semibold ${style.text} ${sizeStyle.value}`}>
                {value > 0 ? '+' : ''}{value}%
            </span>
            {label && (
                <span className={`text-gray-500 ${sizeStyle.text}`}>{label}</span>
            )}
        </div>
    );
}

/**
 * TrendCard - Card with trend information
 */
export function TrendCard({
    title = '',
    currentValue = 0,
    previousValue = 0,
    format = 'number',
    prefix = '',
    suffix = ''
}) {
    const change = previousValue !== 0
        ? ((currentValue - previousValue) / previousValue * 100).toFixed(1)
        : 0;

    const direction = change > 0 ? 'up' : change < 0 ? 'down' : 'stable';

    const formatValue = (val) => {
        if (format === 'currency') return formatPrice(val);
        if (format === 'percent') return `${val}%`;
        return val.toLocaleString();
    };

    return (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
            <p className="text-sm text-gray-500 mb-1">{title}</p>
            <div className="flex items-end justify-between">
                <p className="text-3xl font-bold text-gray-900">
                    {prefix}{formatValue(currentValue)}{suffix}
                </p>
                <TrendIndicator direction={direction} value={parseFloat(change)} size="sm" />
            </div>
            <p className="text-xs text-gray-400 mt-2">
                vs. previous: {prefix}{formatValue(previousValue)}{suffix}
            </p>
        </div>
    );
}
