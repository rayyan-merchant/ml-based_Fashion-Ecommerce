import React, { useState } from 'react';

/**
 * WordcloudImage - Renders a base64 wordcloud image
 * @param {string} base64Data - Base64 encoded image data
 * @param {string} alt - Alt text for the image
 * @param {string} productName - Product name for display
 * @param {boolean} loading - Loading state
 * @param {string} error - Error message if any
 */
export default function WordcloudImage({
    base64Data,
    alt = 'Product Wordcloud',
    productName = '',
    loading = false,
    error = null
}) {
    const [isExpanded, setIsExpanded] = useState(false);

    if (loading) {
        return (
            <div className="bg-gray-100 rounded-xl p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
                <div className="aspect-video bg-gray-200 rounded-lg" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-red-800 mb-2">Unable to Load Wordcloud</h3>
                <p className="text-red-600 text-sm">{error}</p>
            </div>
        );
    }

    if (!base64Data) {
        return (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center">
                <div className="text-gray-400 mb-2">
                    <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                    </svg>
                </div>
                <p className="text-gray-500 text-sm">No wordcloud available for this product</p>
            </div>
        );
    }

    const imageSrc = base64Data.startsWith('data:')
        ? base64Data
        : `data:image/png;base64,${base64Data}`;

    return (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                <div>
                    <h3 className="font-semibold text-gray-900">Review Wordcloud</h3>
                    {productName && (
                        <p className="text-sm text-gray-500">{productName}</p>
                    )}
                </div>
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title={isExpanded ? 'Collapse' : 'Expand'}
                >
                    <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        {isExpanded ? (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M6 18L18 6M6 6l12 12" />
                        ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                        )}
                    </svg>
                </button>
            </div>

            {/* Image */}
            <div className={`p-4 ${isExpanded ? 'fixed inset-0 z-50 bg-black/80 flex items-center justify-center' : ''}`}>
                {isExpanded && (
                    <button
                        onClick={() => setIsExpanded(false)}
                        className="absolute top-4 right-4 p-2 bg-white rounded-full shadow-lg"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                )}
                <img
                    src={imageSrc}
                    alt={alt}
                    className={`rounded-lg ${isExpanded ? 'max-w-4xl max-h-[80vh] object-contain' : 'w-full'}`}
                />
            </div>

            {/* Caption */}
            {!isExpanded && (
                <div className="px-4 py-2 bg-gray-50 text-xs text-gray-500">
                    Words sized by frequency in customer reviews
                </div>
            )}
        </div>
    );
}
