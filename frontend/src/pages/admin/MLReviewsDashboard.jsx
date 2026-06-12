import { useEffect, useState } from 'react';
import { sentimentAPI } from '../../api/sentimentAPI';
import { nlpAPI } from '../../api/nlpAPI';
import { articles } from '../../api/api';
import { SentimentBars, WordcloudImage, SkeletonLoader } from '../../components/ml';

const getVariants = product => product?.variants?.length ? product.variants : [product].filter(Boolean);
const getStyleKey = product => product?.product_code || product?.article_id;
const getRepresentativeArticleId = product =>
    getVariants(product).find(variant => variant.article_id)?.article_id || product?.article_id;

export default function MLReviewsDashboard() {
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [products, setProducts] = useState([]);
    const [sentimentData, setSentimentData] = useState(null);
    const [wordcloudData, setWordcloudData] = useState(null);
    const [loading, setLoading] = useState({
        products: false,
        sentiment: false,
        wordcloud: false
    });
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            setLoading(prev => ({ ...prev, products: true }));
            try {
                const productsRes = await articles.getCatalog({ skip: 0, limit: 100, sort: 'popular' });
                setProducts(productsRes.data?.products || []);
            } catch (err) {
                console.error('Error fetching data:', err);
            } finally {
                setLoading(prev => ({ ...prev, products: false }));
            }
        };
        fetchData();
    }, []);

    useEffect(() => {
        const articleId = getRepresentativeArticleId(selectedProduct);
        if (!articleId) return;

        const fetchProductData = async () => {
            setLoading(prev => ({ ...prev, sentiment: true, wordcloud: true }));

            try {
                const [sentimentRes, wordcloudRes] = await Promise.allSettled([
                    sentimentAPI.getProductSummary(articleId),
                    nlpAPI.getProductWordcloud(articleId)
                ]);

                setSentimentData(sentimentRes.status === 'fulfilled' ? sentimentRes.value.data : null);
                setWordcloudData(wordcloudRes.status === 'fulfilled' ? wordcloudRes.value.data : null);
            } catch (err) {
                console.error('Error fetching product data:', err);
            } finally {
                setLoading(prev => ({ ...prev, sentiment: false, wordcloud: false }));
            }
        };

        fetchProductData();
    }, [selectedProduct]);

    const filteredProducts = products.filter(product => {
        const query = searchQuery.toLowerCase();
        return (
            product.prod_name?.toLowerCase().includes(query) ||
            product.product_type_name?.toLowerCase().includes(query) ||
            getStyleKey(product)?.toString().includes(searchQuery) ||
            getVariants(product).some(variant => variant.article_id?.toString().includes(searchQuery))
        );
    });

    return (
        <div className="space-y-6">
            <div className="rounded-2xl bg-gradient-to-r from-purple-600 to-pink-600 p-6 text-white">
                <h1 className="mb-2 text-2xl font-bold">Reviews & NLP Dashboard</h1>
                <p className="text-purple-100">Analyze grouped style sentiment, review wordclouds, and category complaints.</p>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                <div className="rounded-xl border border-gray-200 bg-white p-4 lg:col-span-1">
                    <h2 className="mb-4 text-lg font-semibold text-gray-900">Select Style</h2>

                    <input
                        type="text"
                        placeholder="Search styles..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-purple-500"
                    />

                    <div className="max-h-96 space-y-2 overflow-y-auto">
                        {loading.products ? (
                            <SkeletonLoader variant="text" count={5} />
                        ) : filteredProducts.length ? (
                            filteredProducts.slice(0, 20).map((product) => {
                                const styleKey = getStyleKey(product);
                                return (
                                    <button
                                        key={styleKey}
                                        onClick={() => setSelectedProduct(product)}
                                        className={`w-full rounded-lg px-3 py-2 text-left transition-colors ${getStyleKey(selectedProduct) === styleKey
                                            ? 'border border-purple-300 bg-purple-100 text-purple-900'
                                            : 'border border-transparent hover:bg-gray-100'
                                            }`}
                                    >
                                        <p className="truncate text-sm font-medium">{product.prod_name || 'Unnamed style'}</p>
                                        <p className="text-xs text-gray-500">
                                            Style {styleKey} - {getVariants(product).length} variants
                                        </p>
                                    </button>
                                );
                            })
                        ) : (
                            <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">No grouped styles found.</p>
                        )}
                    </div>
                </div>

                <div className="space-y-6 lg:col-span-2">
                    {selectedProduct ? (
                        <>
                            <div className="rounded-xl border border-gray-200 bg-white p-6">
                                <h3 className="mb-2 text-xl font-bold text-gray-900">{selectedProduct.prod_name}</h3>
                                <p className="text-sm text-gray-500">
                                    Category: {selectedProduct.product_group_name || selectedProduct.product_type_name || 'Unassigned'} |
                                    Style: {getStyleKey(selectedProduct)} |
                                    Representative article: {getRepresentativeArticleId(selectedProduct)}
                                </p>
                            </div>

                            <div className="rounded-xl border border-gray-200 bg-white p-6">
                                <h3 className="mb-4 text-lg font-semibold text-gray-900">Sentiment Analysis</h3>
                                {loading.sentiment ? (
                                    <SkeletonLoader variant="bar" />
                                ) : sentimentData ? (
                                    <SentimentBars
                                        positive={sentimentData.positive || 0}
                                        neutral={sentimentData.neutral || 0}
                                        negative={sentimentData.negative || 0}
                                        totalReviews={sentimentData.total_reviews || 0}
                                        size="lg"
                                    />
                                ) : (
                                    <p className="text-gray-500">No sentiment data available for this style.</p>
                                )}
                            </div>

                            <WordcloudImage
                                base64Data={wordcloudData?.image}
                                productName={selectedProduct.prod_name}
                                loading={loading.wordcloud}
                            />
                        </>
                    ) : (
                        <div className="rounded-xl border border-gray-200 bg-gray-50 p-12 text-center">
                            <h3 className="mb-2 text-xl font-semibold text-gray-700">Select a Style</h3>
                            <p className="text-gray-500">Choose a grouped style from the left to view sentiment analysis and wordcloud.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
