import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ordersService } from '../services';

export default function OrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchOrder = async () => {
      try {
        setLoading(true);
        const data = await ordersService.get(id);
        setOrder(data);
      } catch (err) {
        setError(err.message || 'Failed to fetch order details');
      } finally {
        setLoading(false);
      }
    };
    if (id) {
      fetchOrder();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <h2 className="text-2xl font-bold mb-4">Order not found</h2>
        <p className="text-gray-600 mb-8">{error || "We couldn't find the details for this order."}</p>
        <button 
          onClick={() => navigate('/orders')}
          className="px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
        >
          Back to Orders
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 mb-16 app-container">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <button 
            onClick={() => navigate('/orders')}
            className="text-gray-500 hover:text-gray-900 flex items-center gap-2 mb-4"
          >
             &larr; Back to Orders
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Order #{order.order_id || id}</h1>
          <p className="text-gray-500 mt-2">Placed on {new Date(order.created_at || Date.now()).toLocaleDateString()}</p>
        </div>
        <div>
          <span className={`px-4 py-2 rounded-full text-sm font-semibold capitalize
            ${order.order_status === 'pending' || order.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
              order.order_status === 'completed' || order.status === 'completed' ? 'bg-green-100 text-green-800' :
              'bg-gray-100 text-gray-800'}`}>
            {order.order_status || order.status || 'Processing'}
          </span>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 p-6 sm:p-8 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div>
            <h3 className="text-lg font-semibold mb-4 border-b pb-2">Shipping Information</h3>
            <p className="text-gray-800">{order.shipping_address || 'Address not provided'}</p>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-4 border-b pb-2">Payment Details</h3>
            <p className="text-gray-600 mb-1">Status: <span className="font-semibold text-gray-900">{order.payment_status || 'Pending'}</span></p>
            <p className="text-gray-600">Total Amount: <span className="font-semibold text-gray-900">Rs {order.total_amount?.toLocaleString() || '0'}</span></p>
          </div>
        </div>

        {order.items && order.items.length > 0 ? (
          <div>
            <h3 className="text-lg font-semibold mb-4 border-b pb-2">Order Items</h3>
            <div className="divide-y">
              {order.items.map((item, idx) => (
                <div key={idx} className="py-4 flex justify-between items-center">
                  <div>
                    <p className="font-medium text-gray-900">{item.article_id || 'Item'}</p>
                    <p className="text-sm text-gray-500">Qty: {item.quantity || 1}</p>
                  </div>
                  <p className="font-medium">Rs {item.price?.toLocaleString() || '0'}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 p-4 rounded-lg text-center text-gray-500">
            No item details found for this order.
          </div>
        )}
      </div>
    </div>
  );
}