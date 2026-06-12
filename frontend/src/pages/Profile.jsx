import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { orders } from "../api/api";
import { useCustomerSegment } from "../hooks/useSegmentation";
import { useRecommendations } from "../hooks/useRecommendations";
import { SegmentBadge, SegmentCard, RecommendationSection } from "../components/ml";
import { formatPrice } from "../utils/price";

export default function Profile() {
  const navigate = useNavigate();
  const { user: contextUser, logout } = useApp();
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [orderData, setOrderData] = useState({
    ordersCount: 0,
    totalSpent: 0,
    latestOrderDate: null
  });

  // Fetch customer segment
  const segmentResult = useCustomerSegment(contextUser?.customer_id);
  const segment = segmentResult?.segment;
  const segmentLoading = segmentResult?.loading || false;

  // Fetch personalized recommendations
  const recsResult = useRecommendations(contextUser?.customer_id, {
    fetchPersonalized: true,
    fetchTrending: false,
    limit: 8
  });
  const personalized = recsResult?.personalized || [];
  const recsLoading = recsResult?.loading || false;

  useEffect(() => {
    // Wait for context to load user
    if (contextUser || contextUser === null) {
      setLoading(false);
    }
  }, [contextUser]);

  // Load order data when user is available
  useEffect(() => {
    if (contextUser) {
      orders.getMyOrders()
        .then(res => {
          const ordersList = res.data || [];
          const totalSpent = ordersList.reduce((sum, order) => sum + (order.total_amount || 0), 0);
          const latestOrder = ordersList.length > 0 ? ordersList[0] : null;

          setOrderData({
            ordersCount: ordersList.length,
            totalSpent: totalSpent,
            latestOrderDate: latestOrder ? latestOrder.created_at : null
          });
        })
        .catch(err => {
          console.error('Failed to load order data:', err);
        });
    }
  }, [contextUser]);

  const user = contextUser ? {
    id: contextUser.customer_id,
    name: `${contextUser.first_name || ''} ${contextUser.last_name || ''}`.trim() || 'User',
    firstName: contextUser.first_name || '',
    lastName: contextUser.last_name || '',
    email: contextUser.email || '',
    phone: contextUser.phone || '',
    loyaltyScore: contextUser.loyalty_score || 0,
    ordersCount: orderData.ordersCount,
    totalSpent: orderData.totalSpent,
    signupDate: contextUser.signup_date || '',
    rfm: {
      recency: contextUser.rfm_recency || 0,
      frequency: contextUser.rfm_frequency || 0,
      monetary: contextUser.rfm_monetary || 0
    }
  } : null;

  const getLoyaltyTier = (score) => {
    if (score >= 2000) return { tier: "Platinum", color: "text-purple-600", bgColor: "bg-purple-100", borderColor: "border-purple-500" };
    if (score >= 1000) return { tier: "Gold", color: "text-yellow-600", bgColor: "bg-yellow-100", borderColor: "border-yellow-500" };
    if (score >= 500) return { tier: "Silver", color: "text-gray-600", bgColor: "bg-gray-100", borderColor: "border-gray-500" };
    return { tier: "Bronze", color: "text-orange-600", bgColor: "bg-orange-100", borderColor: "border-orange-500" };
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="app-container py-8 md:py-12 min-h-[60vh]">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">My Profile</h1>

        {/* Profile Header Card Skeleton */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 md:p-8 mb-8 animate-pulse">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
            {/* Avatar Skeleton */}
            <div className="w-24 h-24 md:w-32 md:h-32 rounded-full bg-gray-200 flex-shrink-0"></div>

            {/* User Info Skeleton */}
            <div className="flex-1 w-full text-center sm:text-left">
              <div className="h-8 bg-gray-200 rounded w-48 mx-auto sm:mx-0 mb-3"></div>
              <div className="h-5 bg-gray-200 rounded w-64 mx-auto sm:mx-0 mb-4"></div>
              <div className="h-8 bg-gray-200 rounded w-32 mx-auto sm:mx-0"></div>
            </div>
          </div>
        </div>

        {/* Stats Grid Skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 animate-pulse">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-gray-200 rounded-lg w-12 h-12"></div>
              </div>
              <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-32"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="app-container py-8 md:py-12 min-h-[60vh]">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">My Profile</h1>
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
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Please Log In</h2>
          <p className="text-gray-600 mb-8">You need to be logged in to view your profile.</p>
          <button
            onClick={() => navigate('/login')}
            className="btn-soft px-6 py-3 text-base"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  const loyaltyTier = getLoyaltyTier(user.loyaltyScore);

  return (
    <div className="app-container py-8 md:py-12 min-h-[60vh]">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900">My Profile</h1>
        <button
          onClick={() => {
            logout();
            navigate('/login');
          }}
          className="mt-4 md:mt-0 px-4 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors"
        >
          Sign Out
        </button>
      </div>

      {/* Profile Header Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 md:p-8 mb-8">
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
          {/* Avatar */}
          <div className="w-24 h-24 md:w-32 md:h-32 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-3xl md:text-4xl font-bold flex-shrink-0">
            {user.name.split(' ').map(n => n[0]).join('')}
          </div>

          {/* User Info */}
          <div className="flex-1 text-center sm:text-left">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">{user.name}</h2>
            <p className="text-gray-600 mb-4">{user.email}</p>
            <div className="flex flex-wrap justify-center sm:justify-start gap-2">
              <div className={`inline-flex items-center px-4 py-2 rounded-full ${loyaltyTier.bgColor} ${loyaltyTier.color} font-semibold`}>
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                {loyaltyTier.tier} Member
              </div>
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-gray-100 text-gray-800 font-semibold">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Joined {formatDate(user.signupDate)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Customer Segment Card */}
      {(segment || segmentLoading) && (
        <div className="mb-8">
          {segmentLoading ? (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
              <div className="h-24 bg-gray-100 rounded"></div>
            </div>
          ) : segment ? (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Customer Segment</h3>
              <SegmentCard
                segmentName={segment.segment_name || segment.name}
                description={segment.description}
                characteristics={segment.characteristics || []}
                rfmData={{
                  recency: user.rfm.recency,
                  frequency: user.rfm.frequency,
                  monetary: user.rfm.monetary
                }}
              />
              {segment.perks && segment.perks.length > 0 && (
                <div className="mt-4 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg">
                  <h4 className="font-semibold text-purple-800 mb-2">🎁 Your Segment Perks</h4>
                  <ul className="space-y-1">
                    {segment.perks.map((perk, index) => (
                      <li key={index} className="text-sm text-purple-700 flex items-center gap-2">
                        <span>✓</span> {perk}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Total Spent Card */}
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6 border border-green-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">Total Spent</h3>
          <p className="text-2xl font-bold text-gray-900">{formatPrice(user.totalSpent)}</p>
          <p className="text-xs text-gray-500 mt-2">Across all orders</p>
        </div>

        {/* Orders Count Card */}
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 border border-purple-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            </div>
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">Total Orders</h3>
          <p className="text-2xl font-bold text-gray-900">{user.ordersCount}</p>
          <p className="text-xs text-gray-500 mt-2">Orders placed</p>
        </div>

        {/* Loyalty Score Card */}
        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl p-6 border border-yellow-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <svg className="w-6 h-6 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </div>
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">Loyalty Points</h3>
          <p className="text-2xl font-bold text-gray-900">{user.loyaltyScore}</p>
          <p className="text-xs text-gray-500 mt-2">{loyaltyTier.tier} tier</p>
        </div>

        {/* RFM Recency Card */}
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-6 border border-orange-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">Last Order</h3>
          <p className="text-2xl font-bold text-gray-900">{user.rfm.recency} days</p>
          <p className="text-xs text-gray-500 mt-2">Since last purchase</p>
        </div>
      </div>

      {/* RFM Analysis Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 md:p-8 mb-8">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">RFM Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="border-l-4 border-blue-500 pl-4">
            <h4 className="text-sm font-medium text-gray-600 mb-2">Recency</h4>
            <p className="text-3xl font-bold text-gray-900 mb-1">{user.rfm.recency}</p>
            <p className="text-xs text-gray-500">Days since last purchase</p>
          </div>
          <div className="border-l-4 border-green-500 pl-4">
            <h4 className="text-sm font-medium text-gray-600 mb-2">Frequency</h4>
            <p className="text-3xl font-bold text-gray-900 mb-1">{user.rfm.frequency}</p>
            <p className="text-xs text-gray-500">Total number of purchases</p>
          </div>
          <div className="border-l-4 border-purple-500 pl-4">
            <h4 className="text-sm font-medium text-gray-600 mb-2">Monetary</h4>
            <p className="text-3xl font-bold text-gray-900 mb-1">{formatPrice(user.rfm.monetary)}</p>
            <p className="text-xs text-gray-500">Total money spent</p>
          </div>
        </div>
      </div>

      {/* Personalized Recommendations */}
      {personalized.length > 0 && (
        <div className="mb-8">
          <RecommendationSection
            title="Recommended For You"
            products={personalized}
            loading={recsLoading}
            layout="carousel"
          />
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 md:p-8">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/orders')}
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors text-left"
          >
            <svg className="w-6 h-6 text-gray-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span className="font-medium text-gray-900">View Orders</span>
          </button>
          <button
            onClick={() => navigate('/wishlist')}
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors text-left"
          >
            <svg className="w-6 h-6 text-gray-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <span className="font-medium text-gray-900">My Wishlist</span>
          </button>
          <button
            onClick={() => navigate('/cart')}
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors text-left"
          >
            <svg className="w-6 h-6 text-gray-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
            <span className="font-medium text-gray-900">Shopping Cart</span>
          </button>
        </div>
      </div>
    </div>
  );
}
