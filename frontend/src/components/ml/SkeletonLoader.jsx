import React from 'react';

/**
 * SkeletonLoader - Reusable skeleton loading components
 * @param {string} variant - 'card' | 'chart' | 'text' | 'bar' | 'table' | 'avatar'
 * @param {number} count - Number of skeleton items
 * @param {string} className - Additional CSS classes
 */
export default function SkeletonLoader({
    variant = 'card',
    count = 1,
    className = ''
}) {
    const renderSkeleton = () => {
        switch (variant) {
            case 'card':
                return (
                    <div className={`bg-white border border-gray-200 rounded-xl p-4 ${className}`}>
                        <div className="h-40 bg-gray-200 rounded-lg animate-pulse mb-4" />
                        <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse mb-2" />
                        <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse" />
                    </div>
                );

            case 'chart':
                return (
                    <div className={`bg-white border border-gray-200 rounded-xl p-6 ${className}`}>
                        <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse mb-4" />
                        <div className="h-64 bg-gray-100 rounded-lg animate-pulse flex items-end justify-around p-4">
                            {[40, 65, 45, 75, 55, 80, 60].map((h, i) => (
                                <div
                                    key={i}
                                    className="w-8 bg-gray-200 rounded-t animate-pulse"
                                    style={{ height: `${h}%` }}
                                />
                            ))}
                        </div>
                    </div>
                );

            case 'text':
                return (
                    <div className={`space-y-2 ${className}`}>
                        <div className="h-4 bg-gray-200 rounded w-full animate-pulse" />
                        <div className="h-4 bg-gray-200 rounded w-5/6 animate-pulse" />
                        <div className="h-4 bg-gray-200 rounded w-4/6 animate-pulse" />
                    </div>
                );

            case 'bar':
                return (
                    <div className={`space-y-3 ${className}`}>
                        {Array.from({ length: 3 }).map((_, i) => (
                            <div key={i} className="flex items-center gap-3">
                                <div className="h-3 bg-gray-200 rounded-full flex-1 animate-pulse" />
                                <div className="h-4 bg-gray-200 rounded w-12 animate-pulse" />
                            </div>
                        ))}
                    </div>
                );

            case 'table':
                return (
                    <div className={`bg-white border border-gray-200 rounded-xl overflow-hidden ${className}`}>
                        <div className="h-12 bg-gray-100 border-b border-gray-200 animate-pulse" />
                        {Array.from({ length: 5 }).map((_, i) => (
                            <div key={i} className="h-14 border-b border-gray-100 flex items-center px-4 gap-4">
                                <div className="h-4 bg-gray-200 rounded w-1/4 animate-pulse" />
                                <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse" />
                                <div className="h-4 bg-gray-200 rounded w-1/5 animate-pulse" />
                                <div className="h-4 bg-gray-200 rounded w-1/6 animate-pulse" />
                            </div>
                        ))}
                    </div>
                );

            case 'avatar':
                return (
                    <div className={`flex items-center gap-3 ${className}`}>
                        <div className="w-10 h-10 bg-gray-200 rounded-full animate-pulse" />
                        <div className="space-y-1.5">
                            <div className="h-4 bg-gray-200 rounded w-24 animate-pulse" />
                            <div className="h-3 bg-gray-200 rounded w-16 animate-pulse" />
                        </div>
                    </div>
                );

            case 'stat':
                return (
                    <div className={`bg-white border border-gray-200 rounded-xl p-5 ${className}`}>
                        <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse mb-2" />
                        <div className="h-8 bg-gray-200 rounded w-2/3 animate-pulse mb-2" />
                        <div className="h-3 bg-gray-200 rounded w-1/3 animate-pulse" />
                    </div>
                );

            default:
                return (
                    <div className={`h-20 bg-gray-200 rounded-xl animate-pulse ${className}`} />
                );
        }
    };

    if (count === 1) {
        return renderSkeleton();
    }

    return (
        <div className="space-y-4">
            {Array.from({ length: count }).map((_, index) => (
                <React.Fragment key={index}>
                    {renderSkeleton()}
                </React.Fragment>
            ))}
        </div>
    );
}

/**
 * SkeletonGrid - Grid of skeleton cards
 */
export function SkeletonGrid({ columns = 4, rows = 2, gap = 6 }) {
    return (
        <div className={`grid grid-cols-2 md:grid-cols-${columns} gap-${gap}`}>
            {Array.from({ length: columns * rows }).map((_, i) => (
                <SkeletonLoader key={i} variant="card" />
            ))}
        </div>
    );
}
