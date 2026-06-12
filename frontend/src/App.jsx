import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { ProtectedRoute, ProtectedRouteAdmin } from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import SearchResults from './pages/SearchResults';
import EditorialPage from './pages/EditorialPage';
import NotFound from './pages/NotFound';

// Customer pages
import Home from './pages/Home';
import ProductListing from './pages/ProductListing';
import ProductDetail from './pages/ProductDetail';
import Cart from './pages/Cart';
import Wishlist from './pages/Wishlist';
import Checkout from './pages/Checkout';
import OrdersHistory from './pages/OrdersHistory';
import OrderDetail from './pages/OrderDetail';
import Reviews from './pages/Reviews';
import Profile from './pages/Profile';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Contact from './pages/Contact';
import Blog from './pages/Blog';
import Settings from './pages/Settings';

// Admin page
import AdminDashboard from './pages/AdminDashboard';

export default function App() {
  return (
    <AppProvider>
      <Router>
        <AppShell />
      </Router>
    </AppProvider>
  );
}

function AppShell() {
  const location = useLocation();
  const isAdminPath = location.pathname.startsWith('/admin');

  return (
    <div className="flex min-h-screen flex-col">
      {!isAdminPath && <Navbar />}
      <main className="flex-grow">
        <Routes>
          <Route path='/' element={<Home />} />
          <Route path='/products' element={<ProductListing />} />
          <Route path='/products/:id' element={<ProductDetail />} />
          <Route path='/collections/:category' element={<ProductListing />} />
          <Route path='/sale' element={<ProductListing />} />
          <Route path='/new-arrivals' element={<ProductListing />} />
          <Route path='/trending' element={<ProductListing />} />
          <Route path='/lookbook' element={<EditorialPage />} />
          <Route path='/brands' element={<EditorialPage />} />
          <Route path='/login' element={<Login />} />
          <Route path='/admin/login' element={<Login />} />
          <Route path='/signup' element={<Signup />} />
          <Route path='/register' element={<Signup />} />
          <Route path='/contact' element={<Contact />} />
          <Route path='/blog' element={<Blog />} />
          <Route path='/search' element={<SearchResults />} />

          <Route path='/cart' element={
            <ProtectedRoute>
              <Cart />
            </ProtectedRoute>
          } />
          <Route path='/wishlist' element={
            <ProtectedRoute>
              <Wishlist />
            </ProtectedRoute>
          } />
          <Route path='/checkout' element={
            <ProtectedRoute>
              <Checkout />
            </ProtectedRoute>
          } />
          <Route path='/orders' element={
            <ProtectedRoute>
              <OrdersHistory />
            </ProtectedRoute>
          } />
          <Route path='/orders/:id' element={
            <ProtectedRoute>
              <OrderDetail />
            </ProtectedRoute>
          } />
          <Route path='/profile' element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } />
          <Route path='/settings' element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          } />
          <Route path='/reviews/:productId' element={<Reviews />} />
          <Route path='/account' element={
            <ProtectedRoute>
              <OrdersHistory />
            </ProtectedRoute>
          } />
          <Route path='/account/orders' element={
            <ProtectedRoute>
              <OrdersHistory />
            </ProtectedRoute>
          } />
          <Route path='/account/wishlist' element={
            <ProtectedRoute>
              <Wishlist />
            </ProtectedRoute>
          } />
          <Route path='/account/profile' element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } />
          <Route path='/account/reviews' element={
            <ProtectedRoute>
              <Reviews />
            </ProtectedRoute>
          } />

          <Route path='/admin/*' element={
            <ProtectedRouteAdmin>
              <AdminDashboard />
            </ProtectedRouteAdmin>
          } />
          <Route path='*' element={<NotFound />} />
        </Routes>
      </main>
      {!isAdminPath && <Footer />}
    </div>
  );
}
