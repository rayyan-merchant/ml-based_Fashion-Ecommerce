import React from 'react';

/**
 * LifecycleStageCard - Product lifecycle stage visualization
 * Stages: Introduction, Growth, Maturity, Decline
 * @param {Array} products - Array of products with lifecycle stages
 * @param {string} title - Card title
 * @param {boolean} loading - Loading state
 */
export default function LifecycleStageCard({
    products = [],
    title = 'Product Lifecycle Stages',
    loading = false
}) {
    const stages = [
        {
            name: 'Introduction',
            icon: '🌱',
            color: 'bg-blue-500',
            lightColor: 'bg-blue-100',
            textColor: 'text-blue-700',
            description: 'New products entering market'
        },
        {
            name: 'Growth',
            icon: '📈',
            color: 'bg-green-500',
            lightColor: 'bg-green-100',
            textColor: 'text-green-700',
            description: 'Rapidly increasing sales'
        },
        {
            name: 'Maturity',
            icon: '⭐',
            color: 'bg-amber-500',
            lightColor: 'bg-amber-100',
            textColor: 'text-amber-700',
            description: 'Peak market penetration'
        },
        {
            name: 'Decline',
            icon: '📉',
            color: 'bg-red-500',
            lightColor: 'bg-red-100',
            textColor: 'text-red-700',
            description: 'Decreasing demand'
        }
    ];

    if (loading) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse mb-6" />
                <div className="grid grid-cols-4 gap-4">
                    {stages.map((_, i) => (
                        <div key={i} className="h-32 bg-gray-100 rounded-xl animate-pulse" />
                    ))}
                </div>
            </div>
        );
    }

    // Group products by stage
    const stageGroups = stages.map(stage => ({
        ...stage,
        products: products.filter(p =>
            p.stage?.toLowerCase() === stage.name.toLowerCase() ||
            p.lifecycle_stage?.toLowerCase() === stage.name.toLowerCase()
        )
    }));

    const totalProducts = products.length;

    return (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">{title}</h3>

            {/* Stage Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {stageGroups.map((stage, index) => (
                    <div
                        key={stage.name}
                        className={`${stage.lightColor} rounded-xl p-4 relative overflow-hidden`}
                    >
                        {/* Background decoration */}
                        <div className={`absolute -right-4 -top-4 w-20 h-20 ${stage.color} opacity-10 rounded-full`} />

                        {/* Content */}
                        <div className="relative">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-2xl">{stage.icon}</span>
                                <h4 className={`font-semibold ${stage.textColor}`}>{stage.name}</h4>
                            </div>

                            <p className="text-3xl font-bold text-gray-900 mb-1">
                                {stage.products.length}
                            </p>

                            <p className="text-xs text-gray-500">
                                {totalProducts > 0
                                    ? `${((stage.products.length / totalProducts) * 100).toFixed(0)}% of products`
                                    : 'No products'
                                }
                            </p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Flow Arrow */}
            <div className="mt-6 flex items-center justify-center gap-2 text-gray-300">
                {stages.map((stage, index) => (
                    <React.Fragment key={stage.name}>
                        <div className={`w-8 h-1 ${stage.color} rounded`} />
                        {index < stages.length - 1 && (
                            <svg className="w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                        )}
                    </React.Fragment>
                ))}
            </div>

            {/* Product List by Stage (if data available) */}
            {products.length > 0 && (
                <div className="mt-6 pt-4 border-t border-gray-100">
                    <details className="group">
                        <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700 flex items-center gap-2">
                            <svg className="w-4 h-4 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                            View products by stage
                        </summary>
                        <div className="mt-4 space-y-4">
                            {stageGroups.filter(s => s.products.length > 0).map(stage => (
                                <div key={stage.name}>
                                    <p className={`text-sm font-medium ${stage.textColor} mb-2`}>
                                        {stage.icon} {stage.name} ({stage.products.length})
                                    </p>
                                    <div className="flex flex-wrap gap-2">
                                        {stage.products.slice(0, 5).map((product, i) => (
                                            <span
                                                key={product.product_id || i}
                                                className={`text-xs px-2 py-1 rounded-full ${stage.lightColor} ${stage.textColor}`}
                                            >
                                                {product.name || product.product_name}
                                            </span>
                                        ))}
                                        {stage.products.length > 5 && (
                                            <span className="text-xs text-gray-400">
                                                +{stage.products.length - 5} more
                                            </span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </details>
                </div>
            )}
        </div>
    );
}
