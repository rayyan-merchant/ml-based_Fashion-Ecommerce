import { Fragment, useEffect, useMemo, useState } from "react";
import { articles, updateProductStock } from "../../api/api";
import { getColorSwatch } from "../../utils/productVariants";

const getVariants = product => (
  product.variants?.length
    ? product.variants
    : [{ article_id: product.article_id, colour_group_name: product.colour_group_name, stock: product.stock }]
);

const statusLabel = stock => {
  if (stock > 50) return "Healthy";
  if (stock > 0) return "Low";
  return "Out";
};

export default function ProductStock() {
  const [products, setProducts] = useState([]);
  const [changes, setChanges] = useState({});
  const [expanded, setExpanded] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");
  const [stockFilter, setStockFilter] = useState("all");

  const load = () => {
    setLoading(true);
    articles.getCatalog({ skip: 0, limit: 200, sort: "popular" })
      .then(res => setProducts(res.data?.products || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return products.filter(product => {
      const stock = Number(product.stock ?? product.total_stock ?? 0);
      const matchesStock =
        stockFilter === "all" ||
        (stockFilter === "low" && stock > 0 && stock <= 50) ||
        (stockFilter === "out" && stock === 0) ||
        (stockFilter === "healthy" && stock > 50);

      const variants = getVariants(product);
      const matchesSearch =
        !query ||
        (product.prod_name || "").toLowerCase().includes(query) ||
        (product.product_type_name || "").toLowerCase().includes(query) ||
        String(product.product_code || product.article_id || "").includes(query) ||
        variants.some(variant => String(variant.article_id || "").includes(query));

      return matchesStock && matchesSearch;
    });
  }, [products, search, stockFilter]);

  const handleChange = (id, value) => {
    setChanges(prev => ({ ...prev, [id]: value }));
    setMessage("");
  };

  const handleUpdate = async articleId => {
    const newValue = Number(changes[articleId]);
    if (!Number.isFinite(newValue) || newValue < 0) {
      alert("Enter a valid stock quantity");
      return;
    }

    try {
      await updateProductStock(articleId, newValue);
      setMessage(`Stock updated for article ${articleId}.`);
      setChanges(prev => ({ ...prev, [articleId]: "" }));
      load();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update stock");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Grouped Stock Management</h2>
          <p className="text-gray-500">Scan stock by style, then update individual color/article variants.</p>
          {message && <p className="mt-2 text-green-600">{message}</p>}
        </div>
        <div className="flex flex-col gap-3 md:flex-row">
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search style or article"
            className="rounded-lg border px-3 py-2"
          />
          <select value={stockFilter} onChange={e => setStockFilter(e.target.value)} className="rounded-lg border px-3 py-2">
            <option value="all">All stock</option>
            <option value="healthy">Healthy</option>
            <option value="low">Low stock</option>
            <option value="out">Out of stock</option>
          </select>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
            <tr>
              <th className="px-4 py-3">Style</th>
              <th className="px-4 py-3">Total Stock</th>
              <th className="px-4 py-3">Variants</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">Loading grouped inventory...</td>
              </tr>
            ) : filtered.length ? (
              filtered.map(product => {
                const key = product.product_code || product.article_id;
                const variants = getVariants(product);
                const totalStock = Number(product.stock ?? product.total_stock ?? 0);
                const rowExpanded = !!expanded[key];
                const colors = Array.from(new Set(variants.map(variant => variant.colour_group_name).filter(Boolean)));

                return (
                  <Fragment key={key}>
                    <tr className="border-t">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{product.prod_name || "Unnamed style"}</p>
                        <p className="font-mono text-xs text-gray-500">Style {key}</p>
                      </td>
                      <td className="px-4 py-3 text-lg font-semibold text-gray-900">{totalStock}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          {colors.slice(0, 8).map(color => (
                            <span
                              key={color}
                              title={color}
                              className="h-4 w-4 rounded-full border border-white shadow ring-1 ring-gray-200"
                              style={{ background: getColorSwatch(color) }}
                            />
                          ))}
                        </div>
                        <p className="mt-1 text-xs text-gray-500">{variants.length} articles</p>
                      </td>
                      <td className="px-4 py-3 text-gray-700">{statusLabel(totalStock)}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setExpanded(current => ({ ...current, [key]: !rowExpanded }))}
                          className="text-sm font-medium text-gray-800 hover:underline"
                        >
                          {rowExpanded ? "Hide variants" : "Edit variants"}
                        </button>
                      </td>
                    </tr>
                    {rowExpanded && (
                      <tr className="border-t bg-gray-50/70">
                        <td colSpan="5" className="px-4 py-4">
                          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                            {variants.map(variant => (
                              <div key={variant.article_id} className="rounded-lg border bg-white p-3">
                                <div className="flex items-start justify-between gap-3">
                                  <div>
                                    <p className="font-medium text-gray-900">{variant.colour_group_name || "Color variant"}</p>
                                    <p className="font-mono text-xs text-gray-500">Article {variant.article_id}</p>
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
                                    value={changes[variant.article_id] ?? ""}
                                    placeholder={variant.stock ?? 0}
                                    onChange={e => handleChange(variant.article_id, e.target.value)}
                                    className="w-24 rounded border px-2 py-1 text-right"
                                  />
                                  <button
                                    onClick={() => handleUpdate(variant.article_id)}
                                    className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-40"
                                    disabled={!changes[variant.article_id]}
                                  >
                                    Update
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
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">No grouped inventory matches your filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
