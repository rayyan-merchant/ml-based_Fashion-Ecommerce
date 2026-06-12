const RAW_PRICE_SCALE = 100000;
const PRICE_FLOOR = 990;

export function naturalPrice(value) {
  const price = Number(value || 0);

  if (!Number.isFinite(price) || price <= 0) {
    return 0;
  }

  if (price < 100) {
    return Math.max(PRICE_FLOOR, Math.round((price * RAW_PRICE_SCALE) / 100) * 100 - 10);
  }

  return price;
}

export function formatPrice(value) {
  return `Rs ${naturalPrice(value).toLocaleString("en-PK", {
    maximumFractionDigits: 0
  })}`;
}

export function formatPriceRange(min, max) {
  const normalizedMin = naturalPrice(min);
  const normalizedMax = naturalPrice(max);

  if (normalizedMin === normalizedMax) {
    return formatPrice(normalizedMin);
  }

  return `${formatPrice(normalizedMin)} - ${formatPrice(normalizedMax)}`;
}
