import { useEffect, useState } from "react";
import { articles, fetchOrders } from "../../api/api";
import recommendationAPI from "../../api/recommendationAPI";
import segmentationAPI from "../../api/segmentationAPI";
import { formatPrice } from "../../utils/price";

export default function AnalyticsView() {
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [segments, setSegments] = useState([]);
  const [trendingProducts, setTrendingProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      fetchOrders(0, 500),
      articles.getCatalog({ skip: 0, limit: 200, sort: "popular" }),
      segmentationAPI.getSegmentOverview(),
      recommendationAPI.getTrending(6)
    ]).then(([ordersRes, productsRes, segmentsRes, trendingRes]) => {
      if (ordersRes.status === "fulfilled") setOrders(ordersRes.value.data || []);
      if (productsRes.status === "fulfilled") setProducts(productsRes.value.data?.products || []);
      if (segmentsRes.status === "fulfilled") {
        setSegments(segmentsRes.value.data?.segments || segmentsRes.value.data || []);
      }
      if (trendingRes.status === "fulfilled") {
        setTrendingProducts(trendingRes.value.data?.products || trendingRes.value.data?.trending_items || []);
      }

      const failed = [ordersRes, productsRes, segmentsRes, trendingRes].find(result => result.status === "rejected");
      if (failed) {
        setError("Some analytics modules could not be loaded from the backend.");
      }
    }).finally(() => setLoading(false));
  }, []);

  const monthlyRevenue = aggregateMonthlyRevenue(orders);
  const topStockStyles = [...products]
    .sort((a, b) => Number(b.stock ?? b.total_stock ?? 0) - Number(a.stock ?? a.total_stock ?? 0))
    .slice(0, 10);
  const topSellingStyles = [...products]
    .sort((a, b) => Number(b.popularity_score || b.total_sold || 0) - Number(a.popularity_score || a.total_sold || 0))
    .slice(0, 10);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-900">Analytics & ML Insights</h2>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
          {error}
        </div>
      )}

      <section className="bg-white border rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sales Analytics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <AnalyticsCard title="Monthly Revenue">
            <ChartList data={monthlyRevenue} labelKey="month" valueKey="total" formatter={formatPrice} loading={loading} />
          </AnalyticsCard>
          <AnalyticsCard title="Top Inventory Styles">
            <ChartList
              data={topStockStyles.map(p => ({
                label: `${p.prod_name || "Style"} (${p.variant_count || p.variants?.length || 1} variants)`,
                value: p.stock ?? p.total_stock ?? 0
              }))}
              loading={loading}
            />
          </AnalyticsCard>
        </div>
      </section>

      <section className="bg-white border rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Segmentation</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {loading ? (
            [1, 2, 3, 4].map(item => (
              <div key={item} className="h-24 rounded-lg bg-gray-100 animate-pulse" />
            ))
          ) : segments.length ? (
            segments.slice(0, 8).map(segment => (
              <div key={segment.segment_id || segment.id || segment.segment_label} className="rounded-lg p-4 bg-[var(--clr-primary-soft)] text-[var(--clr-primary-dark)]">
                <p className="text-sm font-medium">{segment.segment_label || segment.segment_name || segment.name}</p>
                <p className="text-2xl font-semibold mt-2">{segment.count || segment.customer_count || 0}</p>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-500 col-span-full">No segmentation data returned by the ML service.</p>
          )}
        </div>
      </section>

      <section className="bg-white border rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendation Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-800 mb-2">Trending Now</h4>
            <ul className="text-sm text-gray-600 list-disc pl-5 space-y-1">
              {loading ? (
                <li>Loading recommendation engine output...</li>
              ) : trendingProducts.length ? (
                trendingProducts.map(product => (
                  <li key={product.article_id || product.product_id || product.id}>
                    {product.prod_name || product.name || `Article ${product.article_id || product.product_id}`}
                  </li>
                ))
              ) : (
                <li>No trending recommendations returned.</li>
              )}
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-800 mb-2">Highest Selling Styles</h4>
            <ul className="text-sm text-gray-600 list-disc pl-5 space-y-1">
              {topSellingStyles.slice(0, 6).map(product => (
                <li key={product.product_code || product.article_id}>
                  {product.prod_name || "Style"}: {product.popularity_score || product.total_sold || 0} sold
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

function aggregateMonthlyRevenue(orders) {
  const map = {};
  orders.forEach(order => {
    if (!order.order_date) return;
    const date = new Date(order.order_date);
    if (Number.isNaN(date.getTime())) return;
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    map[key] = (map[key] || 0) + Number(order.total_amount || 0);
  });
  return Object.entries(map)
    .sort(([a], [b]) => (a < b ? -1 : 1))
    .map(([month, total]) => ({ month, total }))
    .slice(-6);
}

function AnalyticsCard({ title, children }) {
  return (
    <div className="border rounded-lg p-4">
      <h4 className="font-medium text-gray-800 mb-3">{title}</h4>
      {children}
    </div>
  );
}

function ChartList({ data, labelKey = "label", valueKey = "value", formatter = (value) => value, loading = false }) {
  if (loading) return <p className="text-sm text-gray-500">Loading...</p>;
  if (!data.length) return <p className="text-sm text-gray-500">No data available.</p>;
  return (
    <div className="space-y-2">
      {data.map(item => (
        <div key={item[labelKey]} className="flex items-center justify-between text-sm">
          <span className="text-gray-600">{item[labelKey]}</span>
          <span className="font-semibold text-gray-900">{formatter(item[valueKey])}</span>
        </div>
      ))}
    </div>
  );
}
