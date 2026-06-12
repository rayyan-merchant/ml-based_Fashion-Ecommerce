import { useEffect, useMemo, useState } from "react";
import { fetchOrders } from "../../api/api";
import { formatPrice } from "../../utils/price";

export default function OrdersView() {
  const [orders, setOrders] = useState([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchOrders(0, 200)
      .then(res => setOrders(res.data || []))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    return orders.filter(order => {
      const matchesStatus = statusFilter === "all" || (order.payment_status || "").toLowerCase() === statusFilter;
      const matchesSearch =
        !search ||
        (order.order_id || "").toString().includes(search) ||
        (order.customer_id || "").toLowerCase().includes(search.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }, [orders, statusFilter, search]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Orders</h2>
          <p className="text-gray-500 text-sm">Track order statuses and payment information.</p>
        </div>
        <div className="flex flex-col md:flex-row gap-3">
          <input
            type="text"
            placeholder="Search by Order ID or Customer ID"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          />
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="all">All statuses</option>
            <option value="paid">Paid</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-600 uppercase text-xs tracking-wide">
            <tr>
              <th className="px-4 py-3">Order ID</th>
              <th className="px-4 py-3">Customer</th>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Total</th>
              <th className="px-4 py-3">Payment Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                  Loading orders...
                </td>
              </tr>
            ) : filtered.length ? (
              filtered.map(order => (
                <tr key={order.order_id} className="border-t">
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{order.order_id}</td>
                  <td className="px-4 py-3 text-gray-800">{order.customer_id}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {order.order_date ? new Date(order.order_date).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-3 font-semibold text-gray-900">{formatPrice(order.total_amount)}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        order.payment_status?.toLowerCase() === "paid"
                          ? "bg-green-50 text-green-600"
                          : order.payment_status?.toLowerCase() === "pending"
                          ? "bg-yellow-50 text-yellow-600"
                          : "bg-red-50 text-red-600"
                      }`}
                    >
                      {order.payment_status || "Unknown"}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                  No orders found for the selected filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
