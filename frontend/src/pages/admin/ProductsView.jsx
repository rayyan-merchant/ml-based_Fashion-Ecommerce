import { Fragment, useEffect, useMemo, useState } from "react";
import { articles, deleteProduct, updateProductPrice, updateProductSale, updateProductStock } from "../../api/api";
import { getImageUrl } from "../../utils/getimageurl";
import { getColorSwatch } from "../../utils/productVariants";
import { formatPrice, formatPriceRange, naturalPrice } from "../../utils/price";

const statusLabel = stock => {
  if (stock > 50) return { label: "In Stock", color: "text-green-700 bg-green-50" };
  if (stock > 0) return { label: "Low Stock", color: "text-yellow-700 bg-yellow-50" };
  return { label: "Out of Stock", color: "text-red-700 bg-red-50" };
};

const getVariants = product => (
  product.variants?.length
    ? product.variants
    : [{
      article_id: product.article_id,
      colour_group_name: product.colour_group_name,
      price: product.price,
      stock: product.stock,
      sale_discount_pct: product.sale_discount_pct,
      image_path: product.image_path
    }]
);

const getVariantIds = product => getVariants(product)
  .map(variant => variant.article_id)
  .filter(Boolean);

const uniqueColors = product => Array.from(new Set(
  getVariants(product)
    .map(variant => variant.colour_group_name)
    .filter(Boolean)
));

export default function ProductsView() {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [stockFilter, setStockFilter] = useState("all");
  const [saleFilter, setSaleFilter] = useState("all");
  const [sectionFilter, setSectionFilter] = useState("all");
  const [sort, setSort] = useState("popular");
  const [expanded, setExpanded] = useState({});
  const [variantStockDrafts, setVariantStockDrafts] = useState({});
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState("");
  const [error, setError] = useState("");

  const loadProducts = () => {
    setLoading(true);
    setError("");
    articles.getCatalog({
      skip: 0,
      limit: 200,
      section: sectionFilter,
      sort,
      onSale: saleFilter === "sale"
    })
      .then(res => setItems(res.data?.products || []))
      .catch(() => setError("Failed to load grouped product catalog"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProducts();
  }, [sectionFilter, sort, saleFilter]);

  const filteredItems = useMemo(() => {
    const query = search.trim().toLowerCase();

    return items.filter(item => {
      const variants = getVariants(item);
      const matchesSearch =
        !query ||
        (item.prod_name || "").toLowerCase().includes(query) ||
        (item.product_type_name || "").toLowerCase().includes(query) ||
        (item.product_group_name || "").toLowerCase().includes(query) ||
        String(item.product_code || "").includes(query) ||
        variants.some(variant => String(variant.article_id || "").includes(query));

      const stock = Number(item.stock ?? item.total_stock ?? 0);
      let matchesStock = true;
      if (stockFilter === "low") matchesStock = stock > 0 && stock <= 50;
      if (stockFilter === "out") matchesStock = stock === 0;
      if (stockFilter === "in") matchesStock = stock > 50;

      const onSale = Number(item.sale_discount_pct || 0) > 0 ||
        variants.some(variant => Number(variant.sale_discount_pct || 0) > 0);
      let matchesSale = true;
      if (saleFilter === "sale") matchesSale = onSale;
      if (saleFilter === "full") matchesSale = !onSale;

      return matchesSearch && matchesStock && matchesSale;
    });
  }, [items, search, stockFilter, saleFilter]);

  const summary = useMemo(() => {
    const totalStyles = items.length;
    const totalArticles = items.reduce((sum, item) => sum + getVariants(item).length, 0);
    const saleStyles = items.filter(item => Number(item.sale_discount_pct || 0) > 0).length;
    const lowStockStyles = items.filter(item => {
      const stock = Number(item.stock ?? item.total_stock ?? 0);
      return stock > 0 && stock <= 50;
    }).length;
    const outOfStockStyles = items.filter(item => Number(item.stock ?? item.total_stock ?? 0) === 0).length;

    return { totalStyles, totalArticles, saleStyles, lowStockStyles, outOfStockStyles };
  }, [items]);

  const handleGroupUpdate = async (product, field, value) => {
    const ids = getVariantIds(product);
    if (!ids.length) return;

    try {
      setUpdating(`${field}-${product.article_id}`);
      if (field === "price") {
        const price = Number(value);
        if (!Number.isFinite(price) || price <= 0) throw new Error("Enter a valid price");
        await Promise.all(ids.map(articleId => updateProductPrice(articleId, price)));
      } else if (field === "sale") {
        const discount = Math.max(0, Math.min(80, parseInt(value || "0", 10)));
        await Promise.all(ids.map(articleId => updateProductSale(articleId, Number.isFinite(discount) ? discount : 0)));
      }
      loadProducts();
    } catch (err) {
      alert(err.message || err.response?.data?.detail || `Failed to update ${field}`);
    } finally {
      setUpdating("");
    }
  };

  const handleVariantStockUpdate = async articleId => {
    const value = Number(variantStockDrafts[articleId]);
    if (!Number.isFinite(value) || value < 0) {
      alert("Enter a valid stock quantity");
      return;
    }

    try {
      setUpdating(`stock-${articleId}`);
      await updateProductStock(articleId, value);
      setVariantStockDrafts(current => ({ ...current, [articleId]: "" }));
      loadProducts();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update stock");
    } finally {
      setUpdating("");
    }
  };

  const handleDeleteStyle = async product => {
    const ids = getVariantIds(product);
    if (!window.confirm(`Delete "${product.prod_name}" and all ${ids.length} article variants?`)) return;

    try {
      setUpdating(`delete-${product.article_id}`);
      await Promise.all(ids.map(articleId => deleteProduct(articleId)));
      loadProducts();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete product style");
    } finally {
      setUpdating("");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Grouped Product Catalog</h2>
          <p className="text-gray-500 text-sm">
            Manage one style per row. Color/article variants are grouped underneath for stock-level control.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          <input
            type="text"
            placeholder="Search style, category, article"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="col-span-2 px-3 py-2 border rounded-lg md:col-span-2"
          />
          <select value={sectionFilter} onChange={e => setSectionFilter(e.target.value)} className="px-3 py-2 border rounded-lg">
            <option value="all">All genders</option>
            <option value="women">Women</option>
            <option value="men">Men</option>
            <option value="kids">Kids</option>
            <option value="unisex">Unisex</option>
            <option value="accessories">Accessories</option>
          </select>
          <select value={stockFilter} onChange={e => setStockFilter(e.target.value)} className="px-3 py-2 border rounded-lg">
            <option value="all">All stock</option>
            <option value="in">In stock</option>
            <option value="low">Low stock</option>
            <option value="out">Out of stock</option>
          </select>
          <select value={saleFilter} onChange={e => setSaleFilter(e.target.value)} className="px-3 py-2 border rounded-lg">
            <option value="all">All sale states</option>
            <option value="sale">On sale</option>
            <option value="full">Full price</option>
          </select>
          <select value={sort} onChange={e => setSort(e.target.value)} className="col-span-2 px-3 py-2 border rounded-lg md:col-span-1">
            <option value="popular">Most sold</option>
            <option value="trending">Trending</option>
            <option value="newest">Newest</option>
            <option value="discount">Biggest sale</option>
            <option value="price_low_high">Price low-high</option>
            <option value="price_high_low">Price high-low</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Metric label="Styles loaded" value={summary.totalStyles} />
        <Metric label="Article variants" value={summary.totalArticles} />
        <Metric label="Styles on sale" value={summary.saleStyles} />
        <Metric label="Low stock styles" value={summary.lowStockStyles} />
        <Metric label="Out of stock" value={summary.outOfStockStyles} />
      </div>

      <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
            <tr>
              <th className="px-4 py-3">Style</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Colors</th>
              <th className="px-4 py-3">Price</th>
              <th className="px-4 py-3">Sale</th>
              <th className="px-4 py-3">Stock</th>
              <th className="px-4 py-3">Sold</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="9" className="px-4 py-8 text-center text-gray-500">Loading grouped products...</td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan="9" className="px-4 py-8 text-center text-red-500">{error}</td>
              </tr>
            ) : filteredItems.length ? (
              filteredItems.map(product => {
                const variants = getVariants(product);
                const colors = uniqueColors(product);
                const status = statusLabel(Number(product.stock ?? product.total_stock ?? 0));
                const rowExpanded = !!expanded[product.article_id];
                const priceMin = product.min_price ?? product.price;
                const priceMax = product.max_price ?? product.price;
                const discount = Number(product.sale_discount_pct || 0);

                return (
                  <Fragment key={product.article_id}>
                    <tr className="border-t align-top">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <img
                            src={getImageUrl(product.image_path)}
                            alt={product.prod_name}
                            className="h-14 w-14 rounded-lg border bg-gray-50 object-contain"
                          />
                          <div>
                            <p className="font-medium text-gray-900">{product.prod_name || "Unnamed style"}</p>
                            <p className="mt-1 font-mono text-xs text-gray-500">
                              Style {product.product_code || product.article_id} - {variants.length} article{variants.length === 1 ? "" : "s"}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        <p>{product.product_type_name || "Unknown"}</p>
                        <p className="text-xs text-gray-400">{product.section_name || product.index_group_name || "Unassigned"}</p>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap items-center gap-1.5">
                          {colors.slice(0, 7).map(color => (
                            <span
                              key={color}
                              title={color}
                              className="h-4 w-4 rounded-full border border-white shadow ring-1 ring-gray-200"
                              style={{ background: getColorSwatch(color) }}
                            />
                          ))}
                          {colors.length > 7 && <span className="text-xs text-gray-500">+{colors.length - 7}</span>}
                        </div>
                        <p className="mt-1 text-xs text-gray-500">{colors.length || product.color_count || 1} colors</p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="mb-2 text-xs text-gray-500">{formatPriceRange(priceMin, priceMax)}</p>
                        <input
                          type="number"
                          className="w-24 rounded border px-2 py-1 text-right"
                          defaultValue={naturalPrice(priceMin)}
                          onBlur={e => handleGroupUpdate(product, "price", e.target.value)}
                        />
                        <p className="mt-1 text-xs text-gray-400">Applies to all colors</p>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            min="0"
                            max="80"
                            className="w-16 rounded border px-2 py-1 text-right"
                            defaultValue={discount}
                            onBlur={e => handleGroupUpdate(product, "sale", e.target.value)}
                          />
                          {discount > 0 && <span className="rounded-full bg-red-50 px-2 py-1 text-xs font-medium text-red-600">{discount}%</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3 font-semibold text-gray-900">{product.stock ?? product.total_stock ?? 0}</td>
                      <td className="px-4 py-3 text-gray-600">{product.popularity_score ?? product.total_sold ?? 0}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-1 text-xs font-medium ${status.color}`}>{status.label}</span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setExpanded(current => ({ ...current, [product.article_id]: !rowExpanded }))}
                          className="mr-3 text-sm font-medium text-gray-700 hover:underline"
                        >
                          {rowExpanded ? "Hide variants" : "Variants"}
                        </button>
                        <button
                          onClick={() => handleDeleteStyle(product)}
                          className="text-sm text-red-600 hover:underline"
                          disabled={updating === `delete-${product.article_id}`}
                        >
                          Delete style
                        </button>
                      </td>
                    </tr>
                    {rowExpanded && (
                      <tr className="border-t bg-gray-50/70">
                        <td colSpan="9" className="px-4 py-4">
                          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                            {variants.map(variant => (
                              <div key={variant.article_id} className="rounded-lg border bg-white p-3">
                                <div className="flex items-start justify-between gap-3">
                                  <div>
                                    <p className="font-medium text-gray-900">{variant.colour_group_name || "Color variant"}</p>
                                    <p className="font-mono text-xs text-gray-500">Article {variant.article_id}</p>
                                    <p className="mt-1 text-xs text-gray-500">{formatPrice(variant.price)}</p>
                                  </div>
                                  <span
                                    className="h-5 w-5 rounded-full border border-white shadow ring-1 ring-gray-200"
                                    style={{ background: getColorSwatch(variant.colour_group_name) }}
                                  />
                                </div>
                                <div className="mt-3 flex items-center gap-2">
                                  <input
                                    type="number"
                                    min="0"
                                    placeholder={variant.stock ?? 0}
                                    value={variantStockDrafts[variant.article_id] ?? ""}
                                    onChange={e => setVariantStockDrafts(current => ({ ...current, [variant.article_id]: e.target.value }))}
                                    className="w-24 rounded border px-2 py-1 text-right"
                                  />
                                  <button
                                    onClick={() => handleVariantStockUpdate(variant.article_id)}
                                    disabled={!variantStockDrafts[variant.article_id] || updating === `stock-${variant.article_id}`}
                                    className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-40"
                                  >
                                    Update stock
                                  </button>
                                  <span className="text-xs text-gray-500">Current: {variant.stock ?? 0}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })
            ) : (
              <tr>
                <td colSpan="9" className="px-4 py-8 text-center text-gray-500">No styles match the current filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p>
    </div>
  );
}
