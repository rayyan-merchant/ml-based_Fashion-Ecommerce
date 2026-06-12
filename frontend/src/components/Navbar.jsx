import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useApp } from "../context/AppContext";

const messages = [
  "Free delivery on orders above Rs 25,000",
  "AI-curated edits refresh throughout the day",
  "30-day returns on all boutique essentials"
];

export default function Navbar() {
  const [showSearch, setShowSearch] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showCategories, setShowCategories] = useState(false);
  const [showGender, setShowGender] = useState(false);
  const [query, setQuery] = useState("");
  const [messageIndex, setMessageIndex] = useState(0);
  const [showAnnouncement, setShowAnnouncement] = useState(true);
  const navigate = useNavigate();
  const { user, admin, cartItems, wishlistItems, logout, logoutAdmin } = useApp();

  useEffect(() => {
    const timer = setInterval(() => {
      setMessageIndex(index => (index + 1) % messages.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const handleSearch = (event) => {
    event.preventDefault();
    if (!query.trim()) return;
    navigate(`/search?query=${encodeURIComponent(query.trim())}`);
    setQuery("");
    setShowSearch(false);
  };

  const handleLogout = () => {
    if (admin) logoutAdmin();
    else logout();
    navigate(admin ? "/admin/login" : "/login");
  };

  const categoryLinks = [
    { label: "Jackets", to: "/products?category=jacket", note: "Outerwear" },
    { label: "Hoodies", to: "/products?category=hoodie", note: "Soft layers" },
    { label: "Trousers", to: "/products?category=trouser", note: "Denim & bottoms" },
    { label: "Beanies", to: "/products?category=beanie", note: "Cold-weather accessories" },
    { label: "Accessories", to: "/products?category=accessory", note: "Finishing touches" }
  ];

  const genderLinks = [
    { label: "Women", to: "/products?section=women" },
    { label: "Men", to: "/products?section=men" },
    { label: "Kids", to: "/products?section=kids" },
    { label: "Unisex", to: "/products?section=unisex" }
  ];

  const directLinks = [
    { label: "Home", to: "/" },
    { label: "New Arrivals", to: "/new-arrivals" },
    { label: "Sale", to: "/sale" },
    { label: "Trending", to: "/trending" }
  ];

  return (
    <header className="sticky top-0 z-30 w-full border-b border-[var(--clr-border)] bg-white/85 backdrop-blur-md">
      {showAnnouncement && (
        <div className="bg-[var(--clr-ink)] text-white">
          <div className="app-container flex h-9 items-center justify-between text-xs">
            <span className="tracking-wide">{messages[messageIndex]}</span>
            <button
              type="button"
              onClick={() => setShowAnnouncement(false)}
              className="text-white/70 transition hover:text-white"
              aria-label="Dismiss announcement"
            >
              Close
            </button>
          </div>
        </div>
      )}

      <div className="app-container flex min-h-16 items-center justify-between py-3">
        <button
          type="button"
          className="rounded-full border border-[var(--clr-border)] px-3 py-2 text-sm md:hidden"
          onClick={() => setShowMenu(menu => !menu)}
          aria-label="Toggle navigation"
        >
          Menu
        </button>

        <nav className="hidden items-center gap-5 text-sm text-[var(--clr-muted)] md:flex">
          {directLinks.slice(0, 1).map(link => (
            <Link key={link.to} to={link.to} className="transition hover:text-[var(--clr-ink)]">
              {link.label}
            </Link>
          ))}

          <div
            className="relative -my-3 py-3"
            onMouseEnter={() => {
              setShowCategories(true);
              setShowGender(false);
            }}
            onMouseLeave={() => setShowCategories(false)}
            onFocus={() => {
              setShowCategories(true);
              setShowGender(false);
            }}
          >
            <button
              type="button"
              className="transition hover:text-[var(--clr-ink)]"
              aria-expanded={showCategories}
            >
              Shop by Category
            </button>
            {showCategories && (
              <div className="absolute left-0 top-full z-40 w-64 pt-2">
                <div className="rounded-2xl border border-[var(--clr-border)] bg-white p-3 shadow-lg">
                  {categoryLinks.map(link => (
                    <Link
                      key={link.to}
                      to={link.to}
                      onClick={() => setShowCategories(false)}
                      className="block rounded-xl px-3 py-2 transition hover:bg-[var(--clr-panel)] hover:text-[var(--clr-ink)]"
                    >
                      <span className="block font-medium text-[var(--clr-ink)]">{link.label}</span>
                      <span className="text-xs text-[var(--clr-muted)]">{link.note}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div
            className="relative -my-3 py-3"
            onMouseEnter={() => {
              setShowGender(true);
              setShowCategories(false);
            }}
            onMouseLeave={() => setShowGender(false)}
            onFocus={() => {
              setShowGender(true);
              setShowCategories(false);
            }}
          >
            <button
              type="button"
              className="transition hover:text-[var(--clr-ink)]"
              aria-expanded={showGender}
            >
              Shop by Gender
            </button>
            {showGender && (
              <div className="absolute left-0 top-full z-40 w-44 pt-2">
                <div className="rounded-2xl border border-[var(--clr-border)] bg-white p-2 shadow-lg">
                  {genderLinks.map(link => (
                    <Link
                      key={link.to}
                      to={link.to}
                      onClick={() => setShowGender(false)}
                      className="block rounded-xl px-3 py-2 transition hover:bg-[var(--clr-panel)] hover:text-[var(--clr-ink)]"
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>

          {directLinks.slice(1).map(link => (
            <Link key={link.to} to={link.to} className="transition hover:text-[var(--clr-ink)]">
              {link.label}
            </Link>
          ))}
        </nav>

        <Link to="/" className="font-display text-3xl text-[var(--clr-ink)]">
          LAYR<span className="text-[var(--clr-primary)]">.</span>
        </Link>

        <div className="relative flex items-center gap-2 text-sm">
          <button
            onClick={() => setShowSearch(prev => !prev)}
            className="rounded-full px-3 py-2 text-[var(--clr-body)] transition hover:bg-[var(--clr-panel)]"
            aria-label="Search"
          >
            Search
          </button>

          {showSearch && (
            <form onSubmit={handleSearch} className="absolute right-0 top-12 w-80 rounded-2xl border border-[var(--clr-border)] bg-white p-3 shadow-lg">
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="w-full rounded-lg border border-[var(--clr-border)] bg-[var(--clr-panel)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--clr-primary)]"
                placeholder="Search products..."
                aria-label="Search products"
              />
              <button
                type="submit"
                className="mt-2 w-full rounded-full bg-[var(--clr-primary)] py-2 text-sm text-white transition hover:bg-[var(--clr-primary-dark)]"
              >
                Search
              </button>
            </form>
          )}

          <Link to="/wishlist" className="rounded-full px-3 py-2 transition hover:bg-[var(--clr-panel)]">
            Wishlist{wishlistItems.length ? ` ${wishlistItems.length}` : ""}
          </Link>

          {admin ? (
            <Link to="/admin" className="rounded-full px-3 py-2 transition hover:bg-[var(--clr-panel)]">Admin</Link>
          ) : user ? (
            <Link to="/profile" className="hidden rounded-full px-3 py-2 transition hover:bg-[var(--clr-panel)] sm:inline-flex">
              {user.first_name || "Account"}
            </Link>
          ) : (
            <Link to="/login" className="rounded-full px-3 py-2 transition hover:bg-[var(--clr-panel)]">Login</Link>
          )}

          {(user || admin) && (
            <button onClick={handleLogout} className="hidden rounded-full px-3 py-2 text-[var(--clr-muted)] transition hover:bg-[var(--clr-panel)] sm:inline-flex">
              Logout
            </button>
          )}

          <Link to="/cart" className="relative rounded-full bg-[var(--clr-ink)] px-4 py-2 text-white">
            Cart
            {cartItems.length > 0 && (
              <span className="absolute -right-2 -top-2 flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--clr-primary)] px-1 text-xs text-white">
                {cartItems.length}
              </span>
            )}
          </Link>
        </div>
      </div>

      {showMenu && (
        <nav className="border-t border-[var(--clr-border)] bg-white px-4 py-4 md:hidden">
          <div className="flex flex-col gap-4">
            {directLinks.map(link => (
              <Link key={link.to} to={link.to} onClick={() => setShowMenu(false)}>
                {link.label}
              </Link>
            ))}
            <div>
              <p className="mb-2 text-xs uppercase tracking-[0.18em] text-[var(--clr-muted)]">Shop by Category</p>
              <div className="grid grid-cols-2 gap-2">
                {categoryLinks.map(link => (
                  <Link key={link.to} to={link.to} onClick={() => setShowMenu(false)} className="rounded-lg bg-[var(--clr-panel)] px-3 py-2">
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-2 text-xs uppercase tracking-[0.18em] text-[var(--clr-muted)]">Shop by Gender</p>
              <div className="grid grid-cols-2 gap-2">
                {genderLinks.map(link => (
                  <Link key={link.to} to={link.to} onClick={() => setShowMenu(false)} className="rounded-lg bg-[var(--clr-panel)] px-3 py-2">
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </nav>
      )}
    </header>
  );
}
