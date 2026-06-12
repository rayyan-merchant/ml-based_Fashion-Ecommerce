export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300 py-12">
      <div className="app-container">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div>
            <h3 className="text-xl font-bold text-white mb-4">LAYR.</h3>
            <p className="mb-4">
              Premium fashion for the modern individual. Quality, style, and comfort in every piece.
            </p>
            <p className="text-sm">
              © 2025 LAYR. All rights reserved.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li><a href="/" className="hover:text-white transition-colors">Home</a></li>
              <li><a href="/products" className="hover:text-white transition-colors">Shop</a></li>
              <li><a href="/blog" className="hover:text-white transition-colors">Blog</a></li>
              <li><a href="/contact" className="hover:text-white transition-colors">Contact</a></li>
              <li><a href="/about" className="hover:text-white transition-colors">About Us</a></li>
            </ul>
          </div>

          {/* Categories */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">Categories</h4>
            <ul className="space-y-2">
              <li><a href="/products?gender=men" className="hover:text-white transition-colors">Men</a></li>
              <li><a href="/products?gender=women" className="hover:text-white transition-colors">Women</a></li>
              <li><a href="/products?category=kids" className="hover:text-white transition-colors">Kids</a></li>
              <li><a href="/products?category=accessories" className="hover:text-white transition-colors">Accessories</a></li>
              <li><a href="/products" className="hover:text-white transition-colors">All Products</a></li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">Contact</h4>
            <ul className="space-y-2">
              <li>Email: info@layr.com</li>
              <li>Phone: +92 335 203 4811</li>
              <li className="pt-2">
                <div className="flex space-x-4">
                  <a href="#" className="hover:text-white transition-colors">FB</a>
                  <a href="#" className="hover:text-white transition-colors">IG</a>
                  <a href="#" className="hover:text-white transition-colors">TW</a>
                  <a href="#" className="hover:text-white transition-colors">PT</a>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
}