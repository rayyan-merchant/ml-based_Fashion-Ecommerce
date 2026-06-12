import React, { createContext, useContext, useEffect, useState } from 'react';
import { adminAuth, api, cart, customerAuth, wishlist } from '../api/api';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [admin, setAdmin] = useState(null);
  const [cartItems, setCartItems] = useState([]);
  const [wishlistItems, setWishlistItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [token, setTokenState] = useState(localStorage.getItem('token'));
  const [adminToken, setAdminTokenState] = useState(localStorage.getItem('adminToken'));

  const clearCustomerSession = () => {
    customerAuth.logout();
    setUser(null);
    setCartItems([]);
    setWishlistItems([]);
    setTokenState(null);
    delete api.defaults.headers.common.Authorization;
  };

  const clearAdminSession = () => {
    adminAuth.logout();
    setAdmin(null);
    setAdminTokenState(null);
    delete api.defaults.headers.common.Authorization;
  };

  const loadCart = async () => {
    try {
      const response = await cart.get();
      setCartItems(Array.isArray(response.data) ? response.data : response.data?.items || []);
    } catch (error) {
      console.error('Failed to load cart:', error);
      setCartItems([]);
    }
  };

  const loadWishlist = async () => {
    try {
      const response = await wishlist.get();
      setWishlistItems(Array.isArray(response.data) ? response.data : response.data?.items || []);
    } catch (error) {
      console.error('Failed to load wishlist:', error);
      setWishlistItems([]);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const storedAdminToken = localStorage.getItem('adminToken');
      const storedToken = localStorage.getItem('token');

      if (storedAdminToken) {
        try {
          api.defaults.headers.common.Authorization = `Bearer ${storedAdminToken}`;
          const response = await adminAuth.me();
          setAdmin(response.data);
          localStorage.setItem('admin', JSON.stringify(response.data));
        } catch (error) {
          console.error('Admin auth failed:', error);
          clearAdminSession();
        }
      }

      if (storedToken) {
        try {
          api.defaults.headers.common.Authorization = `Bearer ${storedToken}`;
          const response = await customerAuth.me();
          setUser(response.data);
          localStorage.setItem('user', JSON.stringify(response.data));
          await Promise.allSettled([loadCart(), loadWishlist()]);
        } catch (error) {
          console.error('Customer auth failed:', error);
          clearCustomerSession();
        }
      }

      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await customerAuth.login({ email, password });
      const { access_token } = response.data;

      localStorage.setItem('token', access_token);
      setTokenState(access_token);
      api.defaults.headers.common.Authorization = `Bearer ${access_token}`;

      const userResponse = await customerAuth.me();
      setUser(userResponse.data);
      localStorage.setItem('user', JSON.stringify(userResponse.data));
      await Promise.allSettled([loadCart(), loadWishlist()]);

      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      clearCustomerSession();
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      };
    }
  };

  const loginAdmin = async (usernameOrEmail, password) => {
    try {
      const response = await adminAuth.login({
        username_or_email: usernameOrEmail,
        password
      });
      const { access_token } = response.data;

      localStorage.setItem('adminToken', access_token);
      setAdminTokenState(access_token);
      api.defaults.headers.common.Authorization = `Bearer ${access_token}`;

      const adminResponse = await adminAuth.me();
      const role = String(adminResponse.data?.role || "").toLowerCase();
      const allowedRoles = ["admin", "super_admin", "manager", "analyst"];
      if (role && !allowedRoles.includes(role)) {
        clearAdminSession();
        return { success: false, error: "Access denied: admin role required" };
      }
      setAdmin(adminResponse.data);
      localStorage.setItem('admin', JSON.stringify(adminResponse.data));

      return { success: true };
    } catch (error) {
      console.error('Admin login failed:', error);
      clearAdminSession();
      return {
        success: false,
        error: error.response?.data?.detail || 'Admin login failed'
      };
    }
  };

  const signup = async (data) => {
    try {
      const response = await customerAuth.signup(data);
      const { access_token } = response.data;

      localStorage.setItem('token', access_token);
      setTokenState(access_token);
      api.defaults.headers.common.Authorization = `Bearer ${access_token}`;

      const userResponse = await customerAuth.me();
      setUser(userResponse.data);
      localStorage.setItem('user', JSON.stringify(userResponse.data));
      await Promise.allSettled([loadCart(), loadWishlist()]);

      return { success: true };
    } catch (error) {
      console.error('Signup failed:', error);
      clearCustomerSession();
      return {
        success: false,
        error: error.response?.data?.detail || 'Signup failed'
      };
    }
  };

  const logout = () => {
    clearCustomerSession();
  };

  const logoutAdmin = () => {
    clearAdminSession();
  };

  const addToCart = async (articleId, quantity = 1) => {
    if (!user) {
      return { success: false, error: 'Please login to add items to cart' };
    }

    try {
      await cart.add(articleId, quantity);
      await loadCart();
      return { success: true };
    } catch (error) {
      console.error('Failed to add to cart:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to add to cart'
      };
    }
  };

  const removeFromCart = async (cartId) => {
    try {
      await cart.remove(cartId);
      await loadCart();
      return { success: true };
    } catch (error) {
      console.error('Failed to remove from cart:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to remove from cart' };
    }
  };

  const updateCartItem = async (cartId, quantity) => {
    try {
      await cart.update(cartId, { quantity });
      await loadCart();
      return { success: true };
    } catch (error) {
      console.error('Failed to update cart:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update cart' };
    }
  };

  const clearCart = async () => {
    if (!user) return { success: false, error: 'Please login first' };

    try {
      await cart.clear(user.customer_id);
      setCartItems([]);
      return { success: true };
    } catch (error) {
      console.error('Failed to clear cart:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to clear cart' };
    }
  };

  const addToWishlist = async (articleId) => {
    if (!user) {
      return { success: false, error: 'Please login to add items to wishlist' };
    }

    try {
      await wishlist.add(articleId);
      await loadWishlist();
      return { success: true };
    } catch (error) {
      console.error('Failed to add to wishlist:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to add to wishlist'
      };
    }
  };

  const removeFromWishlist = async (wishlistId) => {
    try {
      await wishlist.remove(wishlistId);
      await loadWishlist();
      return { success: true };
    } catch (error) {
      console.error('Failed to remove from wishlist:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to remove from wishlist' };
    }
  };

  const moveWishlistToCart = async (wishlistId) => {
    try {
      await wishlist.moveToCart(wishlistId);
      await Promise.allSettled([loadCart(), loadWishlist()]);
      return { success: true };
    } catch (error) {
      console.error('Failed to move to cart:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to move to cart' };
    }
  };

  const value = {
    user,
    admin,
    cartItems,
    wishlistItems,
    loading,
    token,
    adminToken,
    isAuthenticated: !!user,
    isAdmin: !!admin,
    login,
    loginAdmin,
    signup,
    logout,
    logoutAdmin,
    addToCart,
    removeFromCart,
    updateCartItem,
    clearCart,
    loadCart,
    addToWishlist,
    removeFromWishlist,
    moveWishlistToCart,
    loadWishlist,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
