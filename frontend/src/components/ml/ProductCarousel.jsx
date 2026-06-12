import React, { useRef } from 'react';
import ProductCard from '../ProductCard';

/**
 * ProductCarousel - Horizontal scrolling product carousel for recommendations
 * @param {Array} products - Array of product objects
 * @param {string} title - Section title
 * @param {string} icon - Emoji or icon for the title
 * @param {boolean} loading - Loading state
 * @param {function} onProductClick - Callback when a product is clicked
 */
export default function ProductCarousel({
    products = [],
    title = 'Recommended Products',
    icon = null,
    loading = false,
    onProductClick = null
}) {
    const scrollRef = useRef(null);

    const scroll = (direction) => {
        if (scrollRef.current) {
            const scrollAmount = 300;
            scrollRef.current.scrollBy({
                left: direction === 'left' ? -scrollAmount : scrollAmount,
                behavior: 'smooth'
            });
        }
    };

    if (loading) {
        return (
            <div className="w-full">
                <div className="flex items-center gap-2 mb-4">
                    {icon && <span className="text-2xl">{icon}</span>}
                    <h2 className="text-xl font-bold text-gray-900">{title}</h2>
                </div>
                <div className="flex gap-4 overflow-hidden">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="flex-shrink-0 w-64 h-80 bg-gray-100 rounded-xl animate-pulse" />
                    ))}
                </div>
            </div>
        );
    }

    if (!products || products.length === 0) {
        return null;
    }

    return (
        <div className="w-full">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    {icon && <span className="text-2xl">{icon}</span>}
                    <h2 className="text-xl font-bold text-gray-900">{title}</h2>
                    <span className="text-sm text-gray-400">({products.length} items)</span>
                </div>

                {/* Navigation Arrows */}
                <div className="flex gap-2">
                    <button
                        onClick={() => scroll('left')}
                        className="p-2 bg-white border border-gray-200 rounded-full hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm"
                    >
                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                    </button>
                    <button
                        onClick={() => scroll('right')}
                        className="p-2 bg-white border border-gray-200 rounded-full hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm"
                    >
                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                    </button>
                </div>
            </div>

            {/* Carousel with Gradient Fades */}
            <div className="relative">
                {/* Left Gradient */}
                <div className="absolute left-0 top-0 bottom-0 w-12 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none"></div>
                
                <div
                    ref={scrollRef}
                    className="flex gap-4 overflow-x-auto scrollbar-hide pb-4 px-2"
                    style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                >
                    {products.map((product, index) => (
                        <div
                            key={product.product_code || product.article_id || product.id || index}
                            className="flex-shrink-0 w-56"
                            onClick={() => onProductClick && onProductClick(product)}
                        >
                            <ProductCard product={product} />
                        </div>
                    ))}
                </div>

                {/* Right Gradient */}
                <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none"></div>
            </div>
            <style jsx>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
        </div>
    );
}
