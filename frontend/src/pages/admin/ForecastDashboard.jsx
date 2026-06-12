import { useEffect, useMemo, useState } from 'react';
import { useForecast } from '../../hooks/useForecast';
import { ForecastChart } from '../../components/charts';
import { SkeletonLoader } from '../../components/ml';
import { articles, categories as categoriesAPI } from '../../api/api';

const getVariants = product => product?.variants?.length ? product.variants : [product].filter(Boolean);
const getStyleKey = product => product?.product_code || product?.article_id;
const getRepresentativeArticleId = product =>
    getVariants(product).find(variant => variant.article_id)?.article_id || product?.article_id;

export default function ForecastDashboard() {
    const {
        articleForecast,
        categoryForecast,
        allForecasts,
        loading,
        error,
        fetchArticleForecast,
        fetchCategoryForecast,
        fetchAllForecasts,
        runPipeline
    } = useForecast();

    const [products, setProducts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [isPipelineRunning, setIsPipelineRunning] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [productsRes, categoriesRes] = await Promise.all([
                    articles.getCatalog({ skip: 0, limit: 150, sort: 'popular' }),
                    categoriesAPI.getAll(100)
                ]);
                setProducts(productsRes.data?.products || []);
                setCategories(categoriesRes.data || []);
            } catch (err) {
                console.error('Error fetching data:', err);
            }
        };
        fetchData();
        fetchAllForecasts();
    }, [fetchAllForecasts]);

    useEffect(() => {
        const articleId = getRepresentativeArticleId(selectedProduct);
        if (articleId) fetchArticleForecast(articleId);
    }, [selectedProduct, fetchArticleForecast]);

    useEffect(() => {
        if (selectedCategory) {
            fetchCategoryForecast(selectedCategory.category_id || selectedCategory.id);
        }
    }, [selectedCategory, fetchCategoryForecast]);

    const handleRunPipeline = async () => {
        setIsPipelineRunning(true);
        try {
            await runPipeline();
            alert('Pipeline completed successfully!');
        } catch (err) {
            alert('Pipeline failed: ' + err.message);
        } finally {
            setIsPipelineRunning(false);
        }
    };

    const filteredProducts = products.filter(product => {
        const query = searchQuery.toLowerCase();
        return (
            product.prod_name?.toLowerCase().includes(query) ||
            product.product_type_name?.toLowerCase().includes(query) ||
            getStyleKey(product)?.toString().includes(searchQuery) ||
            getVariants(product).some(variant => variant.article_id?.toString().includes(searchQuery))
        );
    });

    const productLookup = useMemo(() => {
        const map = new Map();
        products.forEach(product => {
            getVariants(product).forEach(variant => {
                if (variant.article_id) map.set(String(variant.article_id), product);
            });
            if (product.article_id) map.set(String(product.article_id), product);
        });
        return map;
    }, [products]);

    const forecastRows = useMemo(() => {
        return allForecasts.map(forecast => {
            const product = productLookup.get(String(forecast.article_id));
            const name = forecast.product_name || forecast.name || product?.prod_name || `Article ${forecast.article_id}`;
            return {
                ...forecast,
                displayName: name,
                category: forecast.product_type_name || product?.product_type_name || forecast.product_group_name || product?.product_group_name || "-",
                product
            };
        });
    }, [allForecasts, productLookup]);

    const forecastSummary = useMemo(() => {
        const totalDemand = forecastRows.reduce((sum, row) => sum + Number(row.predicted_sales || 0), 0);
        const rising = forecastRows.filter(row => row.trend === "up").length;
        const falling = forecastRows.filter(row => row.trend === "down").length;
        const top = forecastRows
            .slice()
            .sort((a, b) => Number(b.predicted_sales || 0) - Number(a.predicted_sales || 0))[0];

        return { totalDemand, rising, falling, top };
    }, [forecastRows]);

    const transformForecastData = (forecast) => {
        if (!forecast) return [];

        const historical = (forecast.historical || []).map(h => ({
            date: h.date,
            actual: h.value || h.sales,
            forecast: null
        }));

        const predicted = (forecast.forecast || []).map(f => ({
            date: f.date,
            actual: null,
            forecast: f.value || f.predicted_sales,
            upper_bound: f.upper_bound,
            lower_bound: f.lower_bound
        }));

        return [...historical, ...predicted];
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-600 p-6 text-white">
                <div>
                    <h1 className="mb-2 text-2xl font-bold">Time Series Forecasting</h1>
                    <p className="text-blue-100">Predict style and category demand with ML-powered forecasting.</p>
                </div>
                <button
                    onClick={handleRunPipeline}
                    disabled={isPipelineRunning}
                    className="rounded-lg bg-white px-4 py-2 font-medium text-blue-600 transition-colors hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    {isPipelineRunning ? (
                        <span className="flex items-center gap-2">
                            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            Running...
                        </span>
                    ) : (
                        'Run Pipeline'
                    )}
                </button>
            </div>

            {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
                    {error}
                </div>
            )}

            <div className="grid gap-4 md:grid-cols-4">
                <ForecastMetric label="30-day demand" value={forecastSummary.totalDemand.toLocaleString()} />
                <ForecastMetric label="Rising products" value={forecastSummary.rising} />
                <ForecastMetric label="Falling products" value={forecastSummary.falling} />
                <ForecastMetric label="Top demand" value={forecastSummary.top?.displayName || "-"} compact />
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
                <div className="rounded-xl border border-gray-200 bg-white p-4 lg:col-span-1">
                    <h2 className="mb-4 text-lg font-semibold text-gray-900">Select Style</h2>

                    <input
                        type="text"
                        placeholder="Search styles..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
                    />

                    <div className="mb-6 max-h-64 space-y-2 overflow-y-auto">
                        {filteredProducts.slice(0, 20).map((product) => {
                            const styleKey = getStyleKey(product);
                            return (
                                <button
                                    key={styleKey}
                                    onClick={() => setSelectedProduct(product)}
                                    className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${getStyleKey(selectedProduct) === styleKey
                                        ? 'border border-blue-300 bg-blue-100 text-blue-900'
                                        : 'border border-transparent hover:bg-gray-100'
                                        }`}
                                >
                                    <p className="truncate font-medium">{product.prod_name || 'Unnamed style'}</p>
                                    <p className="text-xs text-gray-500">{getVariants(product).length} variants</p>
                                </button>
                            );
                        })}
                    </div>

                    <hr className="my-4" />

                    <h2 className="mb-4 text-lg font-semibold text-gray-900">Select Category</h2>
                    <select
                        value={selectedCategory?.category_id || selectedCategory?.id || ''}
                        onChange={(e) => {
                            const cat = categories.find(c =>
                                (c.category_id || c.id)?.toString() === e.target.value
                            );
                            setSelectedCategory(cat);
                        }}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">Choose category...</option>
                        {categories.map((cat) => (
                            <option key={cat.category_id || cat.id} value={cat.category_id || cat.id}>
                                {cat.name || cat.product_group_name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="space-y-6 lg:col-span-3">
                    {selectedProduct ? (
                        <div>
                            <h3 className="mb-2 text-sm text-gray-500">
                                Forecasting style: {selectedProduct.prod_name} ({getVariants(selectedProduct).length} variants)
                            </h3>
                            <ForecastChart
                                data={transformForecastData(articleForecast)}
                                title={`Sales Forecast - ${selectedProduct.prod_name}`}
                                loading={loading}
                            />
                        </div>
                    ) : (
                        <div className="rounded-xl border border-gray-200 bg-gray-50 p-12 text-center">
                            <h3 className="mb-2 text-xl font-semibold text-gray-700">Select a Style</h3>
                            <p className="text-gray-500">Choose a grouped style to view its sales forecast.</p>
                        </div>
                    )}

                    {selectedCategory && (
                        <ForecastChart
                            data={transformForecastData(categoryForecast)}
                            title={`Category Forecast - ${selectedCategory.name || selectedCategory.product_group_name}`}
                            loading={loading}
                        />
                    )}
                </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6">
                <h2 className="mb-4 text-lg font-semibold text-gray-900">All Product Forecasts</h2>

                {loading ? (
                    <SkeletonLoader variant="table" />
                ) : forecastRows.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-gray-200">
                                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Product</th>
                                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Category</th>
                                    <th className="px-4 py-3 text-right font-semibold text-gray-700">Predicted Sales</th>
                                    <th className="px-4 py-3 text-center font-semibold text-gray-700">Trend</th>
                                    <th className="px-4 py-3 text-right font-semibold text-gray-700">Confidence</th>
                                    <th className="px-4 py-3 text-right font-semibold text-gray-700">Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {forecastRows.slice(0, 20).map((forecast, index) => (
                                    <tr key={forecast.article_id || index} className="border-b border-gray-100 hover:bg-gray-50">
                                        <td className="px-4 py-3">
                                            <p className="font-medium text-gray-900">{forecast.displayName}</p>
                                            <p className="font-mono text-xs text-gray-500">Article {forecast.article_id}</p>
                                        </td>
                                        <td className="px-4 py-3 text-gray-600">
                                            {forecast.category}
                                        </td>
                                        <td className="px-4 py-3 text-right font-medium">
                                            {forecast.predicted_sales?.toLocaleString() || '-'}
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${forecast.trend === 'up' ? 'bg-green-100 text-green-700' :
                                                forecast.trend === 'down' ? 'bg-red-100 text-red-700' :
                                                    'bg-gray-100 text-gray-700'
                                                }`}>
                                                {forecast.trend === 'up' ? 'Up' :
                                                    forecast.trend === 'down' ? 'Down' :
                                                        'Stable'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-right text-gray-600">
                                            {forecast.confidence ? `${(Number(forecast.confidence) * 100).toFixed(0)}%` : '-'}
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <button
                                                onClick={() => forecast.product && setSelectedProduct(forecast.product)}
                                                disabled={!forecast.product}
                                                className="rounded-lg border px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40"
                                            >
                                                Open style
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="py-8 text-center text-gray-500">No forecast data available.</p>
                )}
            </div>
        </div>
    );
}

function ForecastMetric({ label, value, compact = false }) {
    return (
        <div className="rounded-xl border bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
            <p className={`mt-2 font-semibold text-gray-950 ${compact ? "truncate text-lg" : "text-3xl"}`}>{value}</p>
        </div>
    );
}
