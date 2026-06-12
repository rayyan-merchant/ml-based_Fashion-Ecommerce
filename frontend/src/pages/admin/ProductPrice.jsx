import { useEffect, useMemo, useState } from "react";
import { articles, updateProductPrice } from "../../api/api";
import { getColorSwatch } from "../../utils/productVariants";
import { formatPriceRange, naturalPrice } from "../../utils/price";

const getVariants = product => (
  product.variants?.length
    ? product.variants
    : [{ article_id: product.article_id, colour_group_name: product.colour_group_name, price: product.price }]
);

export default function ProductPrice() {
  const [products, setProducts] = useState([]);
  const [changes, setChanges] = useState({});
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");

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
    if (!query) return products;
    return products.filter(product =>
      (product.prod_name || "").toLowerCase().includes(query) ||
      (product.product_type_name || "").toLowerCase().includes(query) ||
      String(product.product_code || product.article_id || "").includes(query) ||
      getVariants(product).some(variant => String(variant.article_id || "").includes(query))
    );
  }, [products, search]);

  const handleChange = (id, value) => {
    setChanges(prev => ({ ...prev, [id]: value }));
    setMessage("");
  };

  const handleUpdate = async product => {
    const key = product.product_code || product.article_id;
    const value = Number(changes[key]);
    if (!Number.isFinite(value) || value <= 0) {
      alert("Enter a valid price");
      return;
    }

    try {
      await Promise.all(getVariants(product).map(variant => updateProductPrice(variant.article_id, value)));
      setMessage(`Price updated for ${product.prod_name || "style"} (${getVariants(product).length} variants).`);
      setChanges(prev => ({ ...prev, [key]: "" }));
      load();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update grouped price");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Grouped Price Management</h2>
          <p className="text-gray-500">Update a style once and apply the price to all color/article variants.</p>
          {message && <p className="mt-2 text-green-600">{message}</p>}
        </div>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search style or article"
          className="rounded-lg border px-3 py-2"
        />
      </div>

      <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
            <tr>
              <th className="px-4 py-3">Style</th>
              <th className="px-4 py-3">Variants</th>
              <th className="px-4 py-3">Current Price Range</th>
              <th className="px-4 py-3">New Style Price</th>
              <th className="px-4 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">Loading grouped pricing...</td>
              </tr>
            ) : filtered.length ? (
              filtered.map(product => {
                const key = product.product_code || product.article_id;
                const variants = getVariants(product);
                const colors = Array.from(new Set(variants.map(variant => variant.colour_group_name).filter(Boolean)));

                return (
                  <tr key={key} className="border-t">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">{product.prod_name || "Unnamed style"}</p>
                      <p className="font-mono text-xs text-gray-500">Style {key}</p>
                    </td>
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
                    <td className="px-4 py-3 text-gray-800">
                      {formatPriceRange(product.min_price ?? product.price, product.max_price ?? product.price)}
                    </td>
                    <td className="px-4 py-3">
                      <input
                        type="number"
                        step="1"
                        value={changes[key] ?? ""}
                        placeholder={naturalPrice(product.min_price ?? product.price)}
                        onChange={e => handleChange(key, e.target.value)}
                        className="w-36 rounded border px-3 py-2 text-right"
                      />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleUpdate(product)}
                        className="rounded-lg bg-gray-900 px-4 py-2 text-sm text-white disabled:opacity-50"
                        disabled={!changes[key]}
                      >
                        Apply to style
                      </button>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">No grouped products match your search.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
