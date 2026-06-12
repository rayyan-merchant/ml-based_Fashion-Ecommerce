import { useEffect, useMemo, useState } from "react";
import { orders as ordersAPI, articles, customers as customersAPI, reviews as reviewsAPI } from "../../api/api";
import recommendationAPI from "../../api/recommendationAPI";
import segmentationAPI from "../../api/segmentationAPI";
import { formatPrice } from "../../utils/price";

const metricCards = [
  { key: "revenueToday", label: "Revenue (Today)" },
  { key: "revenueMonth", label: "Revenue (This Month)" },
  { key: "totalOrders", label: "Total Orders" },
  { key: "totalCustomers", label: "Total Customers" },
  { key: "lowStock", label: "Low Stock Styles" },
  { key: "newReviews", label: "New Reviews" }
];

const toNumber = (value) => Number(value ?? 0) || 0;

export default function DashboardOverview() {
  const [ordersData, setOrdersData] = useState([]);
  const [products, setProducts] = useState([]);
  const [customersData, setCustomersData] = useState([]);
  const [reviewsData, setReviewsData] = useState([]);
  const [segments, setSegments] = useState([]);
  const [trendingProducts, setTrendingProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    Promise.allSettled([
      ordersAPI.getAll(0, 100),
      articles.getCatalog({ skip: 0, limit: 100, sort: "popular" }),
      customersAPI.getAll(0, 100),
      reviewsAPI.getAll(0, 100),
      segmentationAPI.getSegmentOverview(),
      recommendationAPI.getTrending(6)
    ])
      .then(([ordersRes, productsRes, customersRes, reviewsRes, segmentsRes, trendingRes]) => {
        if (!mounted) return;
        if (ordersRes.status === "fulfilled") setOrdersData(ordersRes.value.data || []);
        if (productsRes.status === "fulfilled") setProducts(productsRes.value.data?.products || productsRes.value.data || []);
        if (customersRes.status === "fulfilled") setCustomersData(customersRes.value.data || []);
        if (reviewsRes.status === "fulfilled") setReviewsData(reviewsRes.value.data || []);
        if (segmentsRes.status === "fulfilled") setSegments(segmentsRes.value.data?.segments || segmentsRes.value.data || []);
        if (trendingRes.status === "fulfilled") {
          setTrendingProducts(trendingRes.value.data?.products || trendingRes.value.data?.trending_items || []);
        }

        const failedCore = [ordersRes, productsRes, customersRes, reviewsRes].some(result => result.status === "rejected");
        if (failedCore) setError("Some dashboard data could not be loaded.");
      })
      .catch(() => {
        if (!mounted) return;
        setError("Failed to load dashboard data");
      })
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, []);

  const metrics = useMemo(() => {
    const now = new Date();
    const today = now.toISOString().slice(0, 10);
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    const revenueToday = ordersData
      .filter(order => (order.order_date || "").startsWith(today))
      .reduce((sum, order) => sum + toNumber(order.total_amount), 0);

    const revenueMonth = ordersData
      .filter(order => {
        const date = new Date(order.order_date);
        return date.getMonth() === currentMonth && date.getFullYear() === currentYear;
      })
      .reduce((sum, order) => sum + toNumber(order.total_amount), 0);

    const lowStock = products.filter(p => {
      const stock = Number(p.stock ?? p.total_stock ?? 0);
      return stock > 0 && stock < 25;
    }).length;

    const recentReviews = reviewsData.filter(review => {
      const created = new Date(review.created_at);
      if (Number.isNaN(created.getTime())) return false;
      return (now - created) / (1000 * 60 * 60 * 24) <= 7;
    }).length;

    return {
      revenueToday,
      revenueMonth,
      totalOrders: ordersData.length,
      totalCustomers: customersData.length,
      lowStock,
      newReviews: recentReviews
    };
  }, [ordersData, products, customersData, reviewsData]);

  const trendData = useMemo(() => {
    const daily = {};
    ordersData.forEach(order => {
      const day = (order.order_date || "").slice(0, 10);
      if (!day) return;
      daily[day] = (daily[day] || 0) + toNumber(order.total_amount);
    });
    return Object.entries(daily)
      .sort(([a], [b]) => (a < b ? -1 : 1))
      .slice(-7);
  }, [ordersData]);

  const monthlyRevenue = useMemo(() => {
    const monthly = {};
    ordersData.forEach(order => {
      if (!order.order_date) return;
      const date = new Date(order.order_date);
      if (Number.isNaN(date.getTime())) return;
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
      monthly[key] = (monthly[key] || 0) + toNumber(order.total_amount);
    });
    return Object.entries(monthly)
      .sort(([a], [b]) => (a < b ? -1 : 1))
      .slice(-6);
  }, [ordersData]);

  const topInventory = useMemo(() => (
    products
      .slice()
      .sort((a, b) => Number(b.stock ?? b.total_stock ?? 0) - Number(a.stock ?? a.total_stock ?? 0))
      .slice(0, 6)
  ), [products]);

  if (loading) {
    return <div className="p-6 bg-white rounded-xl border">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="p-6 bg-red-50 border border-red-200 text-red-700 rounded-xl">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {metricCards.map(card => (
          <div key={card.key} className="bg-white rounded-xl border p-4 shadow-sm">
            <p className="text-sm text-gray-500">{card.label}</p>
            <p className="text-2xl font-semibold mt-2">
              {card.key.toLowerCase().includes("revenue") ? formatPrice(metrics[card.key]) : metrics[card.key] ?? 0}
            </p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-lg text-gray-900">Daily Revenue (7d)</h3>
            <span className="text-sm text-gray-500">Based on orders data</span>
          </div>
          <div className="space-y-3">
            {trendData.length ? (
              trendData.map(([day, amount]) => (
                <div key={day} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{day}</span>
                  <span className="font-semibold">{formatPrice(amount)}</span>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">Not enough data to display trend.</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <h3 className="font-semibold text-lg text-gray-900 mb-4">Top Performing Products</h3>
          <div className="space-y-4">
            {products
              .slice()
              .sort((a, b) => Number(b.popularity_score || b.total_sold || 0) - Number(a.popularity_score || a.total_sold || 0))
              .slice(0, 5)
              .map(product => (
                <div key={product.article_id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-800">{product.prod_name || "Unnamed product"}</p>
                    <p className="text-sm text-gray-500">
                      {product.variant_count || product.variants?.length || 1} variants - Stock: {product.stock ?? product.total_stock ?? 0}
                    </p>
                  </div>
                  <span className="font-semibold text-brand-600">{formatPrice(product.min_price ?? product.price)}</span>
                </div>
              ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Panel title="Monthly Revenue" subtitle="Moved from Basic Analytics">
          <ListData
            data={monthlyRevenue.map(([month, total]) => ({ label: month, value: formatPrice(total) }))}
            empty="No monthly revenue data yet."
          />
        </Panel>

        <Panel title="Top Inventory Styles" subtitle="Grouped style stock">
          <ListData
            data={topInventory.map(product => ({
              label: product.prod_name || "Style",
              meta: `${product.variant_count || product.variants?.length || 1} variants`,
              value: `${product.stock ?? product.total_stock ?? 0} units`
            }))}
            empty="No inventory data returned."
          />
        </Panel>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Panel title="Customer Segments" subtitle="ML segmentation snapshot">
          {segments.length ? (
            <div className="grid grid-cols-2 gap-3">
              {segments.slice(0, 6).map(segment => (
                <div key={segment.segment_id || segment.id || segment.segment_label} className="rounded-lg bg-[var(--clr-primary-soft)] p-4 text-[var(--clr-primary-dark)]">
                  <p className="text-sm font-medium">{segment.segment_label || segment.segment_name || segment.name}</p>
                  <p className="mt-2 text-2xl font-semibold">{segment.count || segment.customer_count || 0}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No segmentation data returned.</p>
          )}
        </Panel>

        <Panel title="Trending Recommendations" subtitle="Recommendation engine output">
          <ListData
            data={trendingProducts.map(product => ({
              label: product.prod_name || product.name || `Article ${product.article_id || product.product_id}`,
              meta: product.product_type_name || product.category || "Recommended",
              value: product.score ? Number(product.score).toFixed(2) : ""
            }))}
            empty="No trending recommendations returned."
          />
        </Panel>
      </div>
    </div>
  );
}

function Panel({ title, subtitle, children }) {
  return (
    <div className="bg-white rounded-xl border p-6 shadow-sm">
      <div className="mb-4">
        <h3 className="font-semibold text-lg text-gray-900">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

function ListData({ data, empty }) {
  if (!data.length) return <p className="text-sm text-gray-500">{empty}</p>;
  return (
    <div className="space-y-3">
      {data.map(item => (
        <div key={`${item.label}-${item.value}`} className="flex items-center justify-between gap-4 text-sm">
          <div className="min-w-0">
            <p className="truncate font-medium text-gray-800">{item.label}</p>
            {item.meta && <p className="text-xs text-gray-500">{item.meta}</p>}
          </div>
          <span className="shrink-0 font-semibold text-gray-900">{item.value}</span>
        </div>
      ))}
    </div>
  );
}
