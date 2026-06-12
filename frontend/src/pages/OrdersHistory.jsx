import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { orders } from "../api/api";
import { formatPrice } from "../utils/price";

export default function OrdersHistory() {
  const { user, isAuthenticated } = useApp();
  const [ordersList, setOrdersList] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (user) {
      // Load customer orders using the correct endpoint
      orders.getMyOrders()
        .then(res => {
          setOrdersList(res.data || []);
        })
        .catch(err => {
          console.error('Failed to load orders:', err);
          setOrdersList([]);
        })
        .finally(() => setLoading(false));
    }
  }, [user, isAuthenticated, navigate]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getStatusColor = (status) => {
    const statusColors = {
      'Pending': 'bg-yellow-100 text-yellow-800',
      'Processing': 'bg-blue-100 text-blue-800',
      'Shipped': 'bg-purple-100 text-purple-800',
      'Delivered': 'bg-green-100 text-green-800',
      'Cancelled': 'bg-red-100 text-red-800'
    };
    return statusColors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="app-container py-8 md:py-12 min-h-[60vh]">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Order History</h1>
        <div className="flex justify-center items-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
            <p className="text-gray-600">Loading your orders...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container py-8 md:py-12 min-h-[60vh]">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Order History</h1>
      
      {ordersList.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 md:p-12 text-center">
          <svg
            className="mx-auto h-24 w-24 text-gray-300 mb-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
            />
          </svg>
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">No Orders Yet</h2>
          <p className="text-gray-600 mb-8">You haven't placed any orders yet.</p>
          <button
            onClick={() => navigate('/products')}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Start Shopping
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {ordersList.map((order) => (
            <div
              key={order.order_id}
              className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    Order #{order.order_id}
                  </h3>
                  <p className="text-sm text-gray-600">
                    Placed on {formatDate(order.created_at)}
                  </p>
                </div>
                <div className="mt-4 md:mt-0">
                  <span className={`px-4 py-2 rounded-full text-sm font-medium ${getStatusColor(order.payment_status)}`}>
                    {order.payment_status || 'Processing'}
                  </span>
                </div>
              </div>

              <div className="border-t border-gray-200 pt-4 mt-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Amount</p>
                    <p className="text-xl font-bold text-gray-900">{formatPrice(order.total_amount)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Shipping Address</p>
                    <p className="text-gray-900">{order.shipping_address || 'N/A'}</p>
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 mt-4">
                <button
                  onClick={() => navigate(`/orders/${order.order_id}`)}
                  className="flex-1 bg-blue-50 text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-blue-100 transition-colors"
                >
                  View Details
                </button>
                {order.payment_status === 'Delivered' && (
                  <button
                    onClick={() => navigate('/products')}
                    className="flex-1 bg-gray-50 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors"
                  >
                    Buy Again
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
