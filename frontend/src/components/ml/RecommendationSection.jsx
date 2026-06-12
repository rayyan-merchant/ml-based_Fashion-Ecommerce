import React from 'react';
import ProductCard from '../ProductCard';
import ProductCarousel from './ProductCarousel';

/**
 * RecommendationSection - Wrapper for recommendation displays
 * Handles loading states, empty states, and layout options
 * @param {string} title - Section title
 * @param {string} icon - Emoji or icon
 * @param {Array} products - Array of product objects
 * @param {boolean} loading - Loading state
 * @param {string} error - Error message if any
 * @param {string} layout - 'carousel' | 'grid'
 * @param {number} columns - Grid columns (for grid layout)
 * @param {function} onRetry - Retry function on error
 */
export default function RecommendationSection({
    title = 'Recommendations',
    icon = null,
    products = [],
    loading = false,
    error = null,
    layout = 'carousel',
    columns = 4,
    onRetry = null
}) {
    // Error state
    if (error) {
        return (
            <div className="w-full py-8">
                <div className="flex items-center gap-2 mb-4">
                    {icon && <span className="text-2xl">{icon}</span>}
                    <h2 className="text-xl font-bold text-gray-900">{title}</h2>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
                    <p className="text-red-600 mb-4">{error}</p>
                    {onRetry && (
                        <button
                            onClick={onRetry}
                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                        >
                            Try Again
                        </button>
                    )}
                </div>
            </div>
        );
    }

    // Loading state
    if (loading) {
        return (
            <div className="w-full py-8">
                <div className="flex items-center gap-2 mb-4">
                    {icon && <span className="text-2xl">{icon}</span>}
                    <h2 className="text-xl font-bold text-gray-900">{title}</h2>
                </div>
                {layout === 'carousel' ? (
                    <div className="flex gap-4 overflow-hidden">
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="flex-shrink-0 w-56">
                                <div className="bg-gray-100 rounded-xl h-72 animate-pulse" />
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className={`grid grid-cols-2 md:grid-cols-${columns} gap-6`}>
                        {Array.from({ length: columns }).map((_, i) => (
                            <div key={i} className="bg-gray-100 rounded-xl h-72 animate-pulse" />
                        ))}
                    </div>
                )}
            </div>
        );
    }

    // Empty state
    if (!products || products.length === 0) {
        return null; // Don't render empty sections
    }

    // Carousel layout
    if (layout === 'carousel') {
        return (
            <div className="w-full py-8">
                <ProductCarousel
                    products={products}
                    title={title}
                    icon={icon}
                />
            </div>
        );
    }

    // Grid layout
    return (
        <div className="w-full py-8">
            <div className="flex items-center gap-2 mb-6">
                {icon && <span className="text-2xl">{icon}</span>}
                <h2 className="text-xl font-bold text-gray-900">{title}</h2>
                <span className="text-sm text-gray-400">({products.length} items)</span>
            </div>
            <div className={`grid grid-cols-2 md:grid-cols-3 lg:grid-cols-${columns} gap-6`}>
                {products.map((product, index) => (
                    <ProductCard
                        key={product.product_code || product.article_id || product.id || index}
                        product={product}
                    />
                ))}
            </div>
        </div>
    );
}
