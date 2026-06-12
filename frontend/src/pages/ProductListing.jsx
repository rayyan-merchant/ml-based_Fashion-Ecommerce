import ProductCard from "../components/ProductCard";
import { articles } from "../api/api";
import { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";

const ITEMS_PER_PAGE = 24;
const categoryLabels = {
  jacket: "Jackets",
  hoodie: "Hoodies",
  trouser: "Trousers",
  beanie: "Beanies",
  accessory: "Accessories"
};

const sectionLabels = {
  women: "Women",
  men: "Men",
  kids: "Kids",
  unisex: "Unisex"
};

export default function ProductListing() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState("popular");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const location = useLocation();
  const { category: routeCategory } = useParams();

  const queryParams = new URLSearchParams(location.search);
  const section = queryParams.get("section") || "";
  const category = queryParams.get("category") || (routeCategory && routeCategory !== "all" ? routeCategory : "");
  const isSalePage = location.pathname === "/sale";
  const isTrendingPage = location.pathname === "/trending";
  const isNewArrivalsPage = location.pathname === "/new-arrivals";

  const pageSort = isTrendingPage ? "trending" : isSalePage ? "discount" : isNewArrivalsPage ? "newest" : sortBy;

  const getTitle = () => {
    if (isSalePage) return "Sale";
    if (isNewArrivalsPage) return "New Arrivals";
    if (isTrendingPage) return "Trending Now";
    if (category) return categoryLabels[category] || category.charAt(0).toUpperCase() + category.slice(1);
    if (section && section !== "all") return `${sectionLabels[section] || section.charAt(0).toUpperCase() + section.slice(1)} Edit`;
    return "All Products";
  };

  const getSubtitle = () => {
    if (isSalePage) return "Live markdowns selected across the catalog, ranked by discount and demand.";
    if (isTrendingPage) return "Ranked by purchase activity and review momentum from the transaction data.";
    if (isNewArrivalsPage) return "Newest article styles first, grouped by parent product and color options.";
    if (category) return "A focused category view with variants kept together as one product.";
    if (section) return "Filtered by customer section so each browse path feels intentional.";
    return "Browse the full grouped catalog.";
  };

  const loadProducts = async (page = 1) => {
    setLoading(true);
    try {
      const skip = (page - 1) * ITEMS_PER_PAGE;
      const response = await articles.getCatalog({
        skip,
        limit: ITEMS_PER_PAGE,
        section,
        category,
        sort: pageSort,
        onSale: isSalePage
      });
      const products = response.data?.products || [];
      const total = Number(response.data?.total_products || products.length);
      setItems(products);
      setTotalCount(total);
      setTotalPages(Math.max(1, Math.ceil(total / ITEMS_PER_PAGE)));
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      console.error("Failed to load product catalog:", error);
      setItems([]);
      setTotalCount(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setCurrentPage(1);
    loadProducts(1);
  }, [section, category, pageSort, location.pathname]);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    loadProducts(page);
  };

  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 7;

    if (totalPages <= maxPagesToShow) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
      return pages;
    }

    if (currentPage <= 4) {
      for (let i = 1; i <= 5; i++) pages.push(i);
      pages.push("...");
      pages.push(totalPages);
    } else if (currentPage >= totalPages - 3) {
      pages.push(1);
      pages.push("...");
      for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      pages.push("...");
      for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i);
      pages.push("...");
      pages.push(totalPages);
    }

    return pages;
  };

  return (
    <div className="app-container mt-10">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="font-display text-4xl font-semibold text-[var(--clr-ink)]">{getTitle()}</h1>
          <p className="mt-1 text-sm text-[var(--clr-muted)]">{getSubtitle()}</p>
          <p className="mt-1 text-sm text-[var(--clr-muted)]">
            {loading
              ? "Loading..."
              : `Showing ${items.length} grouped products from ${totalCount} styles - Page ${currentPage} of ${totalPages}`}
          </p>
        </div>
        <div>
          <label htmlFor="sort" className="mr-2 text-sm text-[var(--clr-muted)]">Sort by:</label>
          <select
            id="sort"
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value)}
            disabled={isTrendingPage || isSalePage || isNewArrivalsPage}
            className="rounded-lg border border-[var(--clr-border)] bg-white px-3 py-2 text-sm"
          >
            <option value="popular">Most Popular</option>
            <option value="trending">Trending</option>
            <option value="price_low_high">Price: Low to High</option>
            <option value="price_high_low">Price: High to Low</option>
            <option value="newest">Newest</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="card-neutral p-4">
              <div className="h-64 animate-pulse rounded-xl bg-[var(--clr-panel)]" />
              <div className="mt-4 h-4 animate-pulse rounded bg-[var(--clr-panel)]" />
              <div className="mt-2 h-4 w-2/3 animate-pulse rounded bg-[var(--clr-panel)]" />
            </div>
          ))}
        </div>
      ) : items.length > 0 ? (
        <>
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {items.map(product => (
              <ProductCard key={product.product_code || product.article_id} product={product} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-12 flex items-center justify-center gap-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="rounded-lg border border-[var(--clr-border)] px-4 py-2 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>

              {getPageNumbers().map((page, index) => (
                page === "..." ? (
                  <span key={`ellipsis-${index}`} className="px-2 text-[var(--clr-muted)]">...</span>
                ) : (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`rounded-lg border px-4 py-2 transition ${
                      currentPage === page
                        ? "border-[var(--clr-primary)] bg-[var(--clr-primary)] text-white"
                        : "border-[var(--clr-border)] hover:bg-white"
                    }`}
                  >
                    {page}
                  </button>
                )
              ))}

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="rounded-lg border border-[var(--clr-border)] px-4 py-2 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="py-16 text-center">
          <div className="mx-auto max-w-md">
            <svg className="mx-auto h-24 w-24 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <h3 className="mt-4 text-xl font-semibold text-[var(--clr-ink)]">No products found</h3>
            <p className="mt-2 text-[var(--clr-muted)]">Try adjusting your filters or check back later.</p>
          </div>
        </div>
      )}
    </div>
  );
}
