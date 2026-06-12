import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { articles } from '../api/api';
import ProductCard from '../components/ProductCard';

export default function SearchResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const query = new URLSearchParams(location.search).get('query');
  const [results, setResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState(query || '');

  useEffect(() => {
    if (query) {
      articles.searchCatalog(query, 0, 200)
        .then(res => {
          setResults(res.data?.products || []);
        })
        .catch(err => {
          console.error('Search failed, falling back to client-side filtering:', err);
          articles.getCatalog({ limit: 200 }).then(res => {
            setResults((res.data?.products || []).filter(p =>
              (p.prod_name || '').toLowerCase().includes(query.toLowerCase())
            ));
          }).catch(err => console.error(err));
        });
    }
  }, [query]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?query=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <div className="app-container py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900">Search Results</h1>
        
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="flex">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-grow px-4 py-3 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Search products..."
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-6 py-3 rounded-r-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Search
            </button>
          </div>
        </form>

        {/* Results */}
        {query && (
          <>
            <p className="text-gray-600 mb-6">
              {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
            </p>
            
            {results.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {results.map(product => (
                  <ProductCard key={product.product_code || product.article_id} product={product} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">No products found matching "{query}"</p>
                <p className="text-gray-400 mt-2">Try different search terms</p>
              </div>
            )}
          </>
        )}
        
        {!query && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">Enter a search term to find products</p>
          </div>
        )}
      </div>
    </div>
  );
}
