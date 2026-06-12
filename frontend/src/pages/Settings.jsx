import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { customers } from "../api/api";

export default function Settings() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useApp();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("name");
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    contact: "",
    address: ""
  });
  const [message, setMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (user) {
      setFormData({
        firstName: user.first_name || "",
        lastName: user.last_name || "",
        contact: user.phone || "",
        address: user.postal_code || ""
      });
      setLoading(false);
    }
  }, [user, isAuthenticated, navigate]);

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    setMessage({ type: "", text: "" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!user) {
      setMessage({ type: "error", text: "User not found. Please log in again." });
      return;
    }

    try {
      const updateData = {
        first_name: formData.firstName,
        last_name: formData.lastName,
        phone: formData.contact,
        postal_code: formData.address
      };

      await customers.update(user.customer_id, updateData);
      setMessage({ type: "success", text: "Settings updated successfully!" });
      
      // Refresh user data
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (error) {
      console.error('Failed to update settings:', error);
      setMessage({ type: "error", text: "Failed to update settings. Please try again." });
    }
  };

  if (loading) {
    return (
      <div className="app-container py-8 md:py-12 min-h-[60vh]">
        <div className="text-center">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="app-container py-8 md:py-12 min-h-[60vh]">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Settings</h1>
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
          <p className="text-gray-600 mb-8">You need to be logged in to access settings.</p>
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

  return (
    <div className="app-container py-8 md:py-12 min-h-[60vh]">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-8">Settings</h1>

      <div className="max-w-4xl mx-auto">
        {/* Tabs */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab("name")}
              className={`flex-1 px-6 py-4 text-sm font-medium ${
                activeTab === "name"
                  ? "text-gray-900 border-b-2 border-gray-900"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Change Name
            </button>
            <button
              onClick={() => setActiveTab("contact")}
              className={`flex-1 px-6 py-4 text-sm font-medium ${
                activeTab === "contact"
                  ? "text-gray-900 border-b-2 border-gray-900"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Change Contact
            </button>
            <button
              onClick={() => setActiveTab("address")}
              className={`flex-1 px-6 py-4 text-sm font-medium ${
                activeTab === "address"
                  ? "text-gray-900 border-b-2 border-gray-900"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Change Address
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-6 md:p-8">
            {message.text && (
              <div
                className={`mb-6 p-4 rounded-lg ${
                  message.type === "success"
                    ? "bg-green-50 text-green-800 border border-green-200"
                    : "bg-red-50 text-red-800 border border-red-200"
                }`}
              >
                {message.text}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              {activeTab === "name" && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Update Your Name</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        First Name *
                      </label>
                      <input
                        type="text"
                        name="firstName"
                        value={formData.firstName}
                        onChange={handleChange}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Last Name *
                      </label>
                      <input
                        type="text"
                        name="lastName"
                        value={formData.lastName}
                        onChange={handleChange}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                        required
                      />
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "contact" && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Update Your Contact</h2>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Contact Number *
                    </label>
                    <input
                      type="tel"
                      name="contact"
                      value={formData.contact}
                      onChange={handleChange}
                      placeholder="Enter your contact number"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                      required
                    />
                  </div>
                </div>
              )}

              {activeTab === "address" && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Update Your Address</h2>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Address *
                    </label>
                    <textarea
                      name="address"
                      value={formData.address}
                      onChange={handleChange}
                      placeholder="Enter your full address"
                      rows={4}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition resize-none"
                      required
                    />
                  </div>
                </div>
              )}

              <div className="mt-8 flex gap-4">
                <button
                  type="submit"
                  className="bg-gray-900 text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors duration-200"
                >
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={() => navigate('/profile')}
                  className="bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-300 transition-colors duration-200"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

