import { formatPrice, naturalPrice } from "../utils/price";
import { getImageUrl } from "../utils/getimageurl";

export default function CartItem({ item, onRemove, onUpdateQuantity }) {
  const handleQuantityChange = (delta) => {
    const newQuantity = item.quantity + delta;
    if (onUpdateQuantity) {
      onUpdateQuantity(item.order_item_id, newQuantity);
    }
  };

  const unitPrice = naturalPrice(item.unit_price || item.price || 0);
  const originalPrice = naturalPrice(item.original_price || item.price || 0);
  const saleDiscount = Number(item.sale_discount_pct || 0);
  const itemTotal = unitPrice * item.quantity;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="flex flex-col sm:flex-row gap-4">

        {/* Product Image */}
        <div className="w-full sm:w-32 md:w-40 aspect-square bg-gray-100 rounded-lg overflow-hidden flex-shrink-0 relative">
          <img
            src={item.image || getImageUrl(item.image_path)}
            alt={item.prod_name || item.article_name}
            className="absolute inset-0 w-full h-full object-cover"
            onError={(e) => {
              e.target.src = getImageUrl("");
            }}
          />
        </div>

        {/* Product Details */}
        <div className="flex-1 flex flex-col sm:flex-row sm:justify-between gap-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.prod_name || item.article_name}</h3>
            <p className="text-gray-600 mb-1">
              {formatPrice(unitPrice)} each
              {saleDiscount > 0 && (
                <span className="ml-2 text-xs text-red-600">
                  {saleDiscount}% off <span className="line-through text-gray-400">{formatPrice(originalPrice)}</span>
                </span>
              )}
            </p>
            <p className="text-sm text-gray-500">Item ID: {item.article_id || item.order_item_id}</p>
          </div>

          {/* Quantity and Actions */}
          <div className="flex items-center gap-4 sm:flex-col sm:items-end">
            <div className="flex items-center border border-gray-300 rounded-lg">
              <button onClick={() => handleQuantityChange(-1)} className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-l-lg">−</button>
              <span className="px-4 py-2 text-gray-900 font-medium min-w-[3rem] text-center">{item.quantity}</span>
              <button onClick={() => handleQuantityChange(1)} className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-r-lg">+</button>
            </div>

            <div className="text-right">
              <p className="text-lg font-semibold text-gray-900 mb-2">{formatPrice(itemTotal)}</p>
              <button onClick={() => onRemove(item.order_item_id)} className="text-sm text-red-600 hover:text-red-700">
                Remove
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
