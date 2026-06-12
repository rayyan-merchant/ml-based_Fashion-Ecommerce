import React from 'react';
import { formatPrice } from '../../utils/price';

/**
 * SegmentBadge - Displays customer segment with colored badge
 * @param {string} segmentName - Name of the segment
 * @param {string} description - Segment description
 * @param {string} segmentId - Segment identifier for color mapping
 * @param {boolean} showDescription - Whether to show description
 * @param {string} size - 'sm' | 'md' | 'lg'
 */
export default function SegmentBadge({
    segmentName = 'Unknown Segment',
    description = '',
    segmentId = '',
    showDescription = true,
    size = 'md'
}) {
    // Color mapping based on common segment types
    const getSegmentStyle = (name) => {
        const lowerName = name.toLowerCase();

        if (lowerName.includes('high-value') || lowerName.includes('premium') || lowerName.includes('vip')) {
            return {
                bg: 'bg-gradient-to-r from-amber-400 to-yellow-500',
                text: 'text-amber-900',
                icon: '👑',
                border: 'border-amber-300'
            };
        }
        if (lowerName.includes('loyal') || lowerName.includes('champion')) {
            return {
                bg: 'bg-gradient-to-r from-purple-500 to-pink-500',
                text: 'text-white',
                icon: '💎',
                border: 'border-purple-300'
            };
        }
        if (lowerName.includes('new') || lowerName.includes('recent')) {
            return {
                bg: 'bg-gradient-to-r from-green-400 to-emerald-500',
                text: 'text-white',
                icon: '🌱',
                border: 'border-green-300'
            };
        }
        if (lowerName.includes('bargain') || lowerName.includes('discount')) {
            return {
                bg: 'bg-gradient-to-r from-orange-400 to-red-500',
                text: 'text-white',
                icon: '🏷️',
                border: 'border-orange-300'
            };
        }
        if (lowerName.includes('window') || lowerName.includes('browser')) {
            return {
                bg: 'bg-gradient-to-r from-blue-400 to-cyan-500',
                text: 'text-white',
                icon: '👀',
                border: 'border-blue-300'
            };
        }
        if (lowerName.includes('dormant') || lowerName.includes('at-risk') || lowerName.includes('churned')) {
            return {
                bg: 'bg-gradient-to-r from-gray-400 to-gray-500',
                text: 'text-white',
                icon: '💤',
                border: 'border-gray-300'
            };
        }

        // Default style
        return {
            bg: 'bg-gradient-to-r from-blue-500 to-indigo-500',
            text: 'text-white',
            icon: '⭐',
            border: 'border-blue-300'
        };
    };

    const style = getSegmentStyle(segmentName);

    const sizes = {
        sm: {
            container: 'px-3 py-1.5',
            text: 'text-sm',
            icon: 'text-base',
            desc: 'text-xs'
        },
        md: {
            container: 'px-4 py-2',
            text: 'text-base',
            icon: 'text-lg',
            desc: 'text-sm'
        },
        lg: {
            container: 'px-5 py-3',
            text: 'text-lg',
            icon: 'text-xl',
            desc: 'text-base'
        }
    };

    const sizeStyle = sizes[size] || sizes.md;

    return (
        <div className={`inline-flex items-center gap-2 ${style.bg} ${sizeStyle.container} rounded-full shadow-lg border ${style.border}`}>
            <span className={sizeStyle.icon}>{style.icon}</span>
            <div>
                <span className={`font-semibold ${style.text} ${sizeStyle.text}`}>
                    {segmentName}
                </span>
                {showDescription && description && (
                    <p className={`${style.text} opacity-90 ${sizeStyle.desc} mt-0.5`}>
                        {description}
                    </p>
                )}
            </div>
        </div>
    );
}

/**
 * SegmentCard - Larger card display for segment info
 */
export function SegmentCard({
    segmentName = 'Unknown Segment',
    description = '',
    characteristics = [],
    rfmData = null
}) {
    const getSegmentStyle = (name) => {
        const lowerName = name.toLowerCase();

        if (lowerName.includes('high-value') || lowerName.includes('premium')) {
            return { gradient: 'from-amber-500 to-yellow-600', icon: '👑' };
        }
        if (lowerName.includes('loyal')) {
            return { gradient: 'from-purple-500 to-pink-600', icon: '💎' };
        }
        if (lowerName.includes('new')) {
            return { gradient: 'from-green-500 to-emerald-600', icon: '🌱' };
        }
        if (lowerName.includes('bargain')) {
            return { gradient: 'from-orange-500 to-red-600', icon: '🏷️' };
        }
        return { gradient: 'from-blue-500 to-indigo-600', icon: '⭐' };
    };

    const style = getSegmentStyle(segmentName);

    return (
        <div className={`bg-gradient-to-br ${style.gradient} rounded-2xl p-6 text-white shadow-xl`}>
            <div className="flex items-center gap-3 mb-4">
                <span className="text-4xl">{style.icon}</span>
                <div>
                    <h3 className="text-2xl font-bold">{segmentName}</h3>
                    {description && <p className="text-white/80">{description}</p>}
                </div>
            </div>

            {characteristics.length > 0 && (
                <div className="mt-4">
                    <p className="text-sm text-white/70 uppercase tracking-wide mb-2">Characteristics</p>
                    <ul className="space-y-1">
                        {characteristics.map((char, index) => (
                            <li key={index} className="flex items-center gap-2 text-sm">
                                <span className="w-1.5 h-1.5 bg-white rounded-full" />
                                {char}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {rfmData && (
                <div className="mt-4 grid grid-cols-3 gap-3">
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <p className="text-xs text-white/70 uppercase">Recency</p>
                        <p className="text-xl font-bold">{rfmData.recency || '-'}</p>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <p className="text-xs text-white/70 uppercase">Frequency</p>
                        <p className="text-xl font-bold">{rfmData.frequency || '-'}</p>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3 text-center">
                        <p className="text-xs text-white/70 uppercase">Monetary</p>
                        <p className="text-xl font-bold">{rfmData.monetary ? formatPrice(rfmData.monetary) : '-'}</p>
                    </div>
                </div>
            )}
        </div>
    );
}
