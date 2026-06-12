import { Link, useNavigate } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { useApp } from "../context/AppContext";
import SettingsIcon from "./SettingsIcon";
import { getImageUrl } from "../utils/getimageurl";
import { getColorSwatch } from "../utils/productVariants";
import { formatPrice, formatPriceRange } from "../utils/price";

export default function ProductCard({ product, isAdmin }) {
  const navigate = useNavigate();
  const { addToCart, addToWishlist, isAuthenticated } = useApp();
  const [isAddingToCart, setIsAddingToCart] = useState(false);
  const [isAddingToWishlist, setIsAddingToWishlist] = useState(false);
  const [selectedVariantId, setSelectedVariantId] = useState(null);
  const [imageFallbackIndex, setImageFallbackIndex] = useState(0);

  const variants = product.variants || [];
  const selectedVariant = variants.find(variant => String(variant.article_id) === String(selectedVariantId));
  const productId = selectedVariant?.article_id || product.article_id || product.id || product.productId || "108775015";
  const productName = product.prod_name || product.name || "Product Name";
  const price = Number(selectedVariant?.price ?? product.price ?? 0);
  const minPrice = Number(product.min_price ?? product.price ?? 0);
  const maxPrice = Number(product.max_price ?? product.price ?? 0);
  const saleDiscount = Number(selectedVariant?.sale_discount_pct ?? product.sale_discount_pct ?? 0);
  const isOnSale = Boolean(selectedVariant?.is_on_sale ?? product.is_on_sale) && saleDiscount > 0;
  const salePrice = Number(selectedVariant?.sale_price ?? product.sale_price ?? price);
  const minSalePrice = Number(product.min_sale_price ?? salePrice ?? minPrice);
  const maxSalePrice = Number(product.max_sale_price ?? salePrice ?? maxPrice);
  const imageCandidates = useMemo(() => {
    const paths = [
      selectedVariant?.image_path,
      product.image_path,
      ...variants.map(variant => variant.image_path)
    ].filter(Boolean);

    return [...new Set(paths)];
  }, [product.image_path, selectedVariant?.image_path, variants]);
  const imagePath = imageCandidates.length > 0
    ? getImageUrl(imageCandidates[Math.min(imageFallbackIndex, imageCandidates.length - 1)])
    : getImageUrl("");
  const originalPriceLabel = selectedVariant
    ? formatPrice(price)
    : minPrice !== maxPrice
    ? formatPriceRange(minPrice, maxPrice)
    : formatPrice(price);
  const salePriceLabel = selectedVariant
    ? formatPrice(salePrice)
    : minSalePrice !== maxSalePrice
    ? formatPriceRange(minSalePrice, maxSalePrice)
    : formatPrice(salePrice);

  useEffect(() => {
    setImageFallbackIndex(0);
  }, [product.article_id, product.product_code, selectedVariantId]);

  const requireAuth = () => {
    if (!isAuthenticated) {
      navigate("/login");
      return false;
    }
    return true;
  };

  return (
    <div className="product-card group rounded-2xl border border-[var(--clr-border)] bg-white p-4 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md">
      <Link to={`/products/${productId}`} className="relative block">
        {isAdmin && (
          <button className="absolute right-2 top-2 z-20 rounded-full bg-white p-2 shadow" aria-label="Product settings">
            <SettingsIcon />
          </button>
        )}
        {isOnSale && (
          <span className="absolute left-3 top-3 z-20 rounded-full bg-[var(--clr-danger)] px-3 py-1 text-xs font-semibold text-white shadow">
            {saleDiscount}% OFF
          </span>
        )}

        <div className="h-64 w-full overflow-hidden rounded-xl bg-[var(--clr-panel)]">
          <img
            src={imagePath}
            alt={productName}
            className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]"
            onError={(event) => {
              if (imageFallbackIndex < imageCandidates.length - 1) {
                setImageFallbackIndex(index => index + 1);
                return;
              }

              event.currentTarget.onerror = null;
              event.currentTarget.src = getImageUrl("");
            }}
          />
        </div>

        <div className="mt-3">
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--clr-muted)]">
            {product.product_group_name || product.index_group_name || "LAYR"}
          </p>
          <h2 className="mt-1 line-clamp-2 text-lg font-semibold text-[var(--clr-ink)]">{productName}</h2>
          <div className="mt-2 flex items-center justify-between gap-2">
            {isOnSale ? (
              <div className="flex flex-col">
                <span className="font-semibold text-[var(--clr-danger)]">{salePriceLabel}</span>
                <span className="text-xs text-[var(--clr-muted)] line-through">{originalPriceLabel}</span>
              </div>
            ) : (
              <p className="text-[var(--clr-body)]">{originalPriceLabel}</p>
            )}
            {(product.trend_score || product.recommendation_score || product.similarity) && (
              <span className="rounded-full bg-[var(--clr-primary-soft)] px-2 py-1 text-xs text-[var(--clr-primary-dark)]">
                AI Pick
              </span>
            )}
          </div>
          {variants.length > 1 && (
            <div className="mt-3 flex items-center justify-between gap-3">
              <div className="flex -space-x-1">
                {variants.slice(0, 6).map((variant) => (
                  <button
                    key={variant.article_id}
                    type="button"
                    onClick={(event) => {
                      event.preventDefault();
                      event.stopPropagation();
                      setSelectedVariantId(variant.article_id);
                    }}
                    title={variant.colour_group_name}
                    className={`h-5 w-5 rounded-full border border-white shadow ring-1 ${
                      String(productId) === String(variant.article_id)
                        ? "ring-2 ring-[var(--clr-primary)]"
                        : "ring-[var(--clr-border)]"
                    }`}
                    style={{ background: getColorSwatch(variant.colour_group_name) }}
                  />
                ))}
              </div>
              <span className="text-xs text-[var(--clr-muted)]">
                {product.color_count || variants.length} colors
              </span>
            </div>
          )}
        </div>
      </Link>

      <div className="mt-4 flex gap-2">
        <button
          onClick={async (event) => {
            event.preventDefault();
            if (!requireAuth()) return;
            setIsAddingToCart(true);
            const result = await addToCart(productId, 1);
            setIsAddingToCart(false);
            alert(result.success ? "Added to cart!" : result.error);
          }}
          disabled={isAddingToCart}
          className="flex-1 rounded-full bg-[var(--clr-primary)] py-2 text-sm font-medium text-white transition hover:bg-[var(--clr-primary-dark)] disabled:opacity-60"
        >
          {isAddingToCart ? "Adding..." : "Add"}
        </button>

        <button
          onClick={async (event) => {
            event.preventDefault();
            if (!requireAuth()) return;
            setIsAddingToWishlist(true);
            const result = await addToWishlist(productId);
            setIsAddingToWishlist(false);
            alert(result.success ? "Added to wishlist!" : result.error);
          }}
          disabled={isAddingToWishlist}
          className="rounded-full border border-[var(--clr-border)] px-4 py-2 text-sm text-[var(--clr-body)] transition hover:border-[var(--clr-primary)] disabled:opacity-60"
        >
          {isAddingToWishlist ? "..." : "Save"}
        </button>

        <button
          onClick={async (event) => {
            event.preventDefault();
            if (!requireAuth()) return;
            setIsAddingToCart(true);
            const result = await addToCart(productId, 1);
            setIsAddingToCart(false);
            if (result.success) navigate("/cart");
            else alert(result.error);
          }}
          className="flex-1 rounded-full bg-[var(--clr-ink)] py-2 text-sm font-medium text-white transition hover:bg-black/80"
        >
          Buy
        </button>
      </div>
    </div>
  );
}
