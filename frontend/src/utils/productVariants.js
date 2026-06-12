export function getProductKey(product) {
  if (!product) return "";
  return String(
    product.product_code ||
    product.product_id ||
    `${product.prod_name || product.name || ""}:${product.product_type_name || ""}:${product.detail_desc || ""}`
  );
}

export function groupProductVariants(products = []) {
  const groups = new Map();

  products.filter(Boolean).forEach((product) => {
    const key = getProductKey(product);
    if (!key) return;

    const current = groups.get(key);
    const variants = product.variants?.length
      ? product.variants
      : [{
          article_id: product.article_id || product.id,
          colour_group_name: product.colour_group_name,
          graphical_appearance_name: product.graphical_appearance_name,
          price: product.price,
          stock: product.stock,
          image_path: product.image_path
        }];

    if (!current) {
      groups.set(key, {
        ...product,
        product_key: key,
        variants: [...variants]
      });
      return;
    }

    const existingVariantIds = new Set(current.variants.map(variant => String(variant.article_id)));
    variants.forEach((variant) => {
      if (!existingVariantIds.has(String(variant.article_id))) {
        current.variants.push(variant);
        existingVariantIds.add(String(variant.article_id));
      }
    });

    const currentPrice = Number(current.price || current.min_price || 0);
    const productPrice = Number(product.price || product.min_price || 0);
    current.min_price = Math.min(Number(current.min_price ?? currentPrice), Number(product.min_price ?? productPrice));
    current.max_price = Math.max(Number(current.max_price ?? currentPrice), Number(product.max_price ?? productPrice));
    current.stock = Number(current.stock || 0) + Number(product.stock || 0);
    current.variant_count = current.variants.length;
    current.color_count = new Set(current.variants.map(variant => variant.colour_group_name).filter(Boolean)).size;
  });

  return Array.from(groups.values()).map((product) => {
    const prices = product.variants
      .map(variant => Number(variant.price))
      .filter(price => Number.isFinite(price));
    const stocks = product.variants
      .map(variant => Number(variant.stock || 0))
      .filter(stock => Number.isFinite(stock));

    return {
      ...product,
      min_price: product.min_price ?? (prices.length ? Math.min(...prices) : product.price),
      max_price: product.max_price ?? (prices.length ? Math.max(...prices) : product.price),
      stock: product.total_stock ?? (stocks.length ? stocks.reduce((sum, stock) => sum + stock, 0) : product.stock),
      variant_count: product.variant_count ?? product.variants.length,
      color_count: product.color_count ?? new Set(product.variants.map(variant => variant.colour_group_name).filter(Boolean)).size
    };
  });
}

const colorMap = {
  black: "#1f1f1f",
  dark: "#2d2a28",
  grey: "#9ca3af",
  gray: "#9ca3af",
  white: "#f8fafc",
  beige: "#d8c3a5",
  brown: "#7c4a2d",
  camel: "#b88758",
  orange: "#c46a3a",
  red: "#b91c1c",
  pink: "#e8a4b8",
  blue: "#315f95",
  navy: "#1d3557",
  green: "#556b4e",
  khaki: "#777255",
  olive: "#626b3f",
  yellow: "#d6ad3f",
  purple: "#7c5a9f",
  multi: "linear-gradient(135deg,#1f2937,#c9a96e,#f8fafc)"
};

export function getColorSwatch(colourName = "") {
  const lower = colourName.toLowerCase();
  const match = Object.entries(colorMap).find(([key]) => lower.includes(key));
  return match ? match[1] : "#d8d5cf";
}
