import axios from 'axios';

const normalizeLocalApiUrl = (url) => {
  if (typeof window === 'undefined') return url;

  const host = window.location.hostname;
  if (host === '127.0.0.1' && url.startsWith('http://localhost:')) {
    return url.replace('http://localhost:', 'http://127.0.0.1:');
  }
  if (host === 'localhost' && url.startsWith('http://127.0.0.1:')) {
    return url.replace('http://127.0.0.1:', 'http://localhost:');
  }

  return url;
};

export const API_URL = normalizeLocalApiUrl(
  process.env.REACT_APP_API_URL ||
  process.env.VITE_API_BASE_URL ||
  process.env.VITE_API_URL ||
  'http://localhost:8000'
);

export const ML_SERVICE_URL =
  normalizeLocalApiUrl(
    process.env.REACT_APP_ML_SERVICE_URL ||
    process.env.VITE_ML_SERVICE_URL ||
    API_URL
  );

export const api = axios.create({
  baseURL: API_URL,
  // Auth in this backend is Bearer-token based. Keeping credentialed CORS on
  // public catalog calls makes browsers reject the API while the backend is in
  // local wildcard-CORS mode, so tokens are attached explicitly below instead.
  withCredentials: false,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const mlApi = axios.create({
  baseURL: ML_SERVICE_URL,
  withCredentials: false,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getToken = () => localStorage.getItem('token');
export const getAdminToken = () => localStorage.getItem('adminToken');
export const setToken = (token) => localStorage.setItem('token', token);
export const setAdminToken = (token) => localStorage.setItem('adminToken', token);
export const removeToken = () => localStorage.removeItem('token');
export const removeAdminToken = () => localStorage.removeItem('adminToken');

const chooseAuthToken = (config) => {
  const url = config.url || '';
  const method = (config.method || 'get').toLowerCase();
  const isWrite = ['post', 'put', 'patch', 'delete'].includes(method);
  const token = getToken();
  const adminToken = getAdminToken();

  if (url.startsWith('/admins') || url.startsWith('/analytics') || url.startsWith('/forecasting') || url.startsWith('/segmentation')) {
    return adminToken || token;
  }

  if (url.startsWith('/customers/auth')) {
    return token;
  }

  if (url.startsWith('/customers')) {
    return adminToken || token;
  }

  if (url.startsWith('/cart/all')) {
    return adminToken;
  }

  if (url.startsWith('/cart') || url.startsWith('/wishlist')) {
    return token;
  }

  if (
    url.startsWith('/orders/my-orders') ||
    url.startsWith('/orders/create') ||
    url.startsWith('/orders/create-with-items') ||
    /\/orders\/\d+\/(details|address)/.test(url)
  ) {
    return token || adminToken;
  }

  if (url.startsWith('/orders')) {
    return adminToken || token;
  }

  if (url.startsWith('/reviews') && method === 'delete') {
    return adminToken || token;
  }

  if (url.startsWith('/reviews')) {
    return token || adminToken;
  }

  if ((url.startsWith('/articles') || url.startsWith('/categories')) && isWrite) {
    return adminToken || token;
  }

  return token || adminToken;
};

const attachAuth = (config) => {
  const authToken = chooseAuthToken(config);
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
};

api.interceptors.request.use(attachAuth, (error) => Promise.reject(error));
mlApi.interceptors.request.use(attachAuth, (error) => Promise.reject(error));

const handleAuthFailure = (error) => {
  if (error.response?.status === 401) {
    removeToken();
    removeAdminToken();
    localStorage.removeItem('user');
    localStorage.removeItem('admin');

    const current = window.location.pathname;
    if (!current.includes('/login') && !current.includes('/admin/login')) {
      window.location.href = current.startsWith('/admin') ? '/admin/login' : '/login';
    }
  }

  return Promise.reject(error);
};

api.interceptors.response.use((response) => response, handleAuthFailure);
mlApi.interceptors.response.use((response) => response, handleAuthFailure);

export const customerAuth = {
  signup: (data) => api.post('/customers/auth/signup', data),
  login: (data) => api.post('/customers/auth/login', data),
  me: () => api.get('/customers/auth/me'),
  logout: () => {
    removeToken();
    localStorage.removeItem('user');
  },
};

export const adminAuth = {
  login: (data) => api.post('/admins/login', data),
  me: () => api.get('/admins/me'),
  logout: () => {
    removeAdminToken();
    localStorage.removeItem('admin');
  },
  changePassword: (data) => api.post('/admins/change-password', data),
  createAdmin: (data) => api.post('/admins/', data),
  listAdmins: () => api.get('/admins/'),
  getLogs: (limit = 100) => api.get('/admins/logs', { params: { limit } }),
};

export const sections = {
  getSections: () => api.get('/sections/'),
  getSectionProducts: (section, limit = 24, offset = 0) =>
    api.get(`/sections/${section}/products`, { params: { limit, offset } }),
  getSectionCategories: (section) => api.get(`/sections/${section}/categories`),
  getCategoryProducts: (section, category, sort, limit, offset) =>
    api.get(`/sections/${section}/${category}/products`, { params: { sort, limit, offset } }),
  getFilterOptions: (section, category) => api.get(`/sections/${section}/${category}/filters`),
  filterAndSort: (section, category, data) => api.post(`/sections/${section}/${category}/filter-sort`, data),
};

export const articles = {
  getAll: (skip = 0, limit = 20) => api.get('/articles/', { params: { skip, limit } }),
  getById: (id) => api.get(`/articles/${id}`),
  getByName: (name) => api.get(`/articles/by-name/${encodeURIComponent(name)}`),
  search: (query, skip = 0, limit = 50) =>
    api.get(`/articles/search/${encodeURIComponent(query)}`, { params: { skip, limit } }),
  getCatalog: ({ skip = 0, limit = 24, section = '', category = '', search = '', sort = 'popular', onSale = false } = {}) =>
    api.get('/articles/catalog/', {
      params: {
        skip,
        limit: Math.min(Math.max(Number(limit) || 24, 1), 200),
        section,
        category,
        search,
        sort,
        on_sale: onSale
      }
    }),
  searchCatalog: (query, skip = 0, limit = 50) =>
    articles.getCatalog({ skip, limit, search: query, sort: 'relevant' }),
  getVariants: (articleId) => api.get(`/articles/${articleId}/variants`),
  create: (data) => api.post('/articles/', data),
  update: (id, data) => api.put(`/articles/${id}`, data),
  delete: (id) => api.delete(`/articles/${id}`),
  getPerformance: (id) => api.get(`/articles/${id}/performance`),
  getDemandTrend: (id) => api.get(`/articles/${id}/demand-trend`),
  getInventory: (id) => api.get(`/articles/${id}/inventory`),
  getFunnelMetrics: () => api.get('/articles/funnel-metrics'),
};

export const categories = {
  getAll: (limit = 100, offset = 0) => api.get('/categories/', { params: { limit, offset } }),
  getById: (id) => api.get(`/categories/${id}`),
  create: (data) => api.post('/categories/', data),
  update: (id, data) => api.put(`/categories/${id}`, data),
  delete: (id) => api.delete(`/categories/${id}`),
  tree: () => api.get('/categories/tree'),
  performance: () => api.get('/categories/performance'),
};

export const customers = {
  getAll: (skip = 0, limit = 100) => api.get('/customers/', { params: { skip, limit } }),
  getById: (id) => api.get(`/customers/${id}`),
  create: (data) => api.post('/customers/', data),
  update: (id, data) => api.put(`/customers/${id}`, data),
  delete: (id) => api.delete(`/customers/${id}`),
  setActive: (id, active) => api.put(`/customers/${id}/active`, null, { params: { active } }),
  getFeatures: (id) => api.get(`/customers/${id}/features`),
  getPurchaseFrequency: (id) => api.get(`/customers/${id}/purchase-frequency`),
  getCLV: (id) => api.get(`/customers/${id}/clv`),
  getRFM: (id) => api.get(`/customers/${id}/rfm`),
  getEvents: (id, skip = 0, limit = 100) => api.get(`/customers/${id}/events`, { params: { skip, limit } }),
  getOrders: (id, skip = 0, limit = 100) => api.get(`/customers/${id}/orders`, { params: { skip, limit } }),
};

export const cart = {
  get: () => api.get('/cart/'),
  getByCustomer: (customerId) => api.get(`/cart/customer/${customerId}`),
  add: (articleId, quantity = 1) => api.post('/cart/add', { article_id: articleId, quantity }),
  addItem: (data) => api.post('/cart/add-item', data),
  update: (cartId, data) => api.put(`/cart/${cartId}`, data),
  remove: (cartId) => api.delete(`/cart/${cartId}`),
  clear: (customerId) => api.delete(`/cart/clear/${customerId}`),
  getCount: (customerId) => api.get(`/cart/${customerId}/count`),
  getAll: (skip = 0, limit = 100) => api.get('/cart/all', { params: { skip, limit } }),
};

export const wishlist = {
  get: () => api.get('/wishlist/'),
  getByCustomer: (customerId) => api.get(`/wishlist/customer/${customerId}`),
  add: (articleId) => api.post('/wishlist/add', { article_id: articleId }),
  addItem: (data) => api.post('/wishlist/add-item', data),
  moveToCart: (wishlistId) => api.post(`/wishlist/move-to-cart/${wishlistId}`),
  remove: (wishlistId) => api.delete(`/wishlist/item/${wishlistId}`),
  clear: (customerId) => api.delete(`/wishlist/customer/${customerId}`),
};

export const orders = {
  getMyOrders: () => api.get('/orders/my-orders'),
  create: (shippingAddress) => api.post('/orders/create', null, { params: { shipping_address: shippingAddress } }),
  createWithItems: (data) => api.post('/orders/create-with-items', data),
  getAll: (skip = 0, limit = 100) => api.get('/orders/', { params: { skip, limit } }),
  getDetails: (orderId) => api.get(`/orders/${orderId}/details`),
  getByCustomer: (customerId, skip = 0, limit = 100) =>
    api.get(`/orders/customer/${customerId}`, { params: { skip, limit } }),
  filter: (params) => api.get('/orders/filter', { params }),
  updateStatus: (orderId, status) => api.put(`/orders/${orderId}/status`, null, { params: { payment_status: status } }),
  updateAddress: (orderId, address) => api.put(`/orders/${orderId}/address`, null, { params: { new_address: address } }),
  getDailySales: (skip = 0, limit = 50) => api.get('/orders/analytics/daily-sales', { params: { skip, limit } }),
};

export const reviews = {
  getAll: (skip = 0, limit = 100) => api.get('/reviews/', { params: { skip, limit } }),
  getById: (id) => api.get(`/reviews/${id}`),
  getByArticle: (articleId, skip = 0, limit = 100) =>
    api.get(`/reviews/article/${articleId}`, { params: { skip, limit } }),
  getByCustomer: (customerId) => api.get(`/reviews/customer/${customerId}`),
  create: (articleIdOrData, reviewText) => {
    if (typeof articleIdOrData === 'object' && articleIdOrData !== null) {
      return api.post('/reviews/', articleIdOrData);
    }
    return api.post('/reviews/create', null, { params: { article_id: articleIdOrData, review_text: reviewText } });
  },
  createAuthenticated: (data) => api.post('/reviews/', data),
  update: (reviewId, data) => api.put(`/reviews/${reviewId}`, data),
  delete: (reviewId) => api.delete(`/reviews/${reviewId}`),
  getArticleStats: (articleId) => api.get(`/reviews/analytics/article/${articleId}`),
};

export const recommendations = {
  personal: (customerId, limit = 12) => api.get(`/hybrid-recommendations/personalized/${customerId}`, { params: { limit } }),
  similar: (articleId, limit = 8) => api.get(`/hybrid-recommendations/you-may-also-like-product/${articleId}`, { params: { limit } }),
  trending: (limit = 12) => api.get('/hybrid-recommendations/trending', { params: { limit } }),
  alsoBought: (customerId, limit = 12) => api.get(`/hybrid-recommendations/customers-also-bought/${customerId}`, { params: { limit } }),
  basedOnInteractions: (customerId, limit = 12) =>
    api.get(`/hybrid-recommendations/based-on-interactions/${customerId}`, { params: { limit } }),
};

export const analytics = {
  revenue: () => mlApi.get('/analytics/revenue'),
  trends: (limit = 50) => mlApi.get('/analytics/trends', { params: { limit } }),
  monthlyGrowth: () => mlApi.get('/analytics/growth/monthly'),
  stockoutRisk: (limit = 50) => mlApi.get('/analytics/stockout-risk', { params: { limit } }),
  lifecycle: (limit = 50) => mlApi.get('/analytics/lifecycle', { params: { limit } }),
  aggregate: (period = 'weekly') => mlApi.get('/analytics/aggregate', { params: { period } }),
};

export const events = {
  getAll: (skip = 0, limit = 100) => api.get('/events/', { params: { skip, limit } }),
};

export const transactions = {
  delete: (id) => api.delete(`/transactions/${id}`),
};

export const fetchProducts = articles.getAll;
export const fetchProductById = articles.getById;
export const addProduct = articles.create;
export const updateProduct = articles.update;
export const deleteProduct = articles.delete;
export const fetchProductsWithSales = articles.getAll;
export const fetchRelatedProducts = (id, limit = 8) => recommendations.similar(id, limit);
export const fetchSimilarProducts = (id, limit = 8) => recommendations.similar(id, limit);
export const fetchTrendingProducts = (limit = 12) => recommendations.trending(limit);
export const updateProductPrice = (id, price) => articles.update(id, { price });
export const updateProductStock = (id, stock) => articles.update(id, { stock });
export const updateProductSale = (id, saleDiscountPct) => articles.update(id, { sale_discount_pct: saleDiscountPct });

export const fetchCustomers = customers.getAll;
export const fetchCustomerById = customers.getById;
export const updateCustomer = customers.update;

export const fetchOrders = orders.getAll;
export const fetchOrderById = orders.getDetails;

export const fetchReviewsByProduct = reviews.getByArticle;
export const postReview = reviews.createAuthenticated;
export const fetchAllReviews = reviews.getAll;

export const fetchCategories = categories.getAll;
export const createCategory = categories.create;
export const updateCategory = categories.update;
export const deleteCategory = categories.delete;

export const fetchEvents = events.getAll;

export const submitContactForm = (formData) => api.post('/contact', formData);

export const handleApiError = (error) => {
  if (error.response) {
    return error.response.data?.detail || error.response.data?.message || 'An error occurred';
  }
  if (error.request) {
    return 'Network error. Please check your connection.';
  }
  return error.message || 'An unexpected error occurred';
};

export default api;
