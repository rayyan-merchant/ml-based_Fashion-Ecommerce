import ProductCard from "../components/ProductCard";
import Button from "../components/Button";
import { sections, articles } from "../api/api";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { useRecommendations } from "../hooks/useRecommendations";
import { RecommendationSection } from "../components/ml";

const heroSlides = [
  {
    image: "https://images.pexels.com/photos/5119930/pexels-photo-5119930.jpeg?auto=compress&cs=tinysrgb&w=1800",
    title: "Layer Up for the Modern You",
    kicker: "LAYR winter edit",
    body: "Outerwear, knitwear, beanies and clean everyday essentials curated for crisp weather and quiet confidence.",
    align: "left",
    position: "center"
  },
  {
    image: "https://images.pexels.com/photos/6626749/pexels-photo-6626749.jpeg?auto=compress&cs=tinysrgb&w=1800",
    title: "Warmth Without Noise",
    kicker: "Men's outerwear",
    body: "Structured coats, soft hooded layers and winter staples designed to look composed in motion.",
    align: "left",
    position: "center"
  },
  {
    image: "https://images.pexels.com/photos/6211599/pexels-photo-6211599.jpeg?auto=compress&cs=tinysrgb&w=1800",
    title: "Soft Layers, Sharp Details",
    kicker: "Women's essentials",
    body: "Wool textures, crossbody details and neutral palettes made for layered winter dressing.",
    align: "right",
    position: "center"
  }
];

const categoryTiles = [
  {
    title: "Men's Winter Edit",
    body: "Structured outer layers.",
    href: "/products?section=men",
    image: "https://images.pexels.com/photos/16430970/pexels-photo-16430970.jpeg?auto=compress&cs=tinysrgb&w=1400",
    fallback: "/products/men.jpg",
    position: "center 32%"
  },
  {
    title: "Women's Soft Layers",
    body: "Neutral warmth, clean lines.",
    href: "/products?section=women",
    image: "https://images.pexels.com/photos/8530712/pexels-photo-8530712.jpeg?auto=compress&cs=tinysrgb&w=1400",
    fallback: "/products/women.png",
    position: "center 34%"
  },
  {
    title: "Little Layers",
    body: "Easy pieces with quiet charm.",
    href: "/products?section=kids",
    image: "https://images.pexels.com/photos/6261891/pexels-photo-6261891.jpeg?auto=compress&cs=tinysrgb&w=1400",
    fallback: "/products/product1.png",
    position: "center 36%"
  },
  {
    title: "Beanies & Finishing Touches",
    body: "Soft texture for cold days.",
    href: "/products?section=accessories",
    image: "https://images.pexels.com/photos/2083751/pexels-photo-2083751.jpeg?auto=compress&cs=tinysrgb&w=1400",
    fallback: "/products/beanie1.jpg",
    position: "center 34%"
  }
];

export default function Home() {
  const { user } = useApp();
  const isLoggedIn = !!user;
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [sectionsList, setSectionsList] = useState([]);
  const [activeSection, setActiveSection] = useState("women");
  const [sectionProducts, setSectionProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [heroIndex, setHeroIndex] = useState(0);
  const activeHero = heroSlides[heroIndex];

  // Fetch recommendations using the hook
  const recommendations = useRecommendations(user?.customer_id, {
    fetchPersonalized: isLoggedIn,
    fetchTrending: true,
    fetchAlsoBought: isLoggedIn,
    fetchInteractions: isLoggedIn,
    limit: 12
  });

  // Safely access recommendation data
  const personalized = recommendations.personalized;
  const trending = recommendations.trending;
  const alsoBought = recommendations.alsoBought;
  const interactions = recommendations.interactions;
  const recsLoading = recommendations.loading;

  useEffect(() => {
    const timer = setInterval(() => {
      setHeroIndex(index => (index + 1) % heroSlides.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Load sections
    sections.getSections()
      .then(res => {
        setSectionsList(res.data?.sections || []);
      })
      .catch(err => console.error('Failed to load sections:', err));

    // Load featured parent products. Color variants stay attached to each product card.
    articles.getCatalog({ limit: 8, sort: "popular" })
      .then(res => {
        setFeaturedProducts(res.data?.products || []);
      })
      .catch(err => console.error('Failed to load products:', err))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    // Load section products when active section changes
    if (activeSection) {
      articles.getCatalog({ section: activeSection, limit: 8, sort: "newest" })
        .then(res => {
          setSectionProducts(res.data?.products || []);
        })
        .catch(err => console.error('Failed to load section products:', err));
    }
  }, [activeSection]);

  return (
    <div>
      {/* HERO */}
      <section className="relative min-h-[76vh] w-full overflow-hidden bg-[var(--clr-ink)]">
        {heroSlides.map((slide, index) => (
          <img
            key={slide.image}
            src={slide.image}
            alt={slide.title}
            className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-700 ${
              index === heroIndex ? "opacity-100" : "opacity-0"
            }`}
            style={{ objectPosition: slide.position }}
          />
        ))}
        <div className="absolute inset-0 bg-gradient-to-r from-black/78 via-black/38 to-black/28" />
        <div className="absolute inset-x-0 bottom-0 h-36 bg-gradient-to-t from-[var(--clr-ink)]/70 to-transparent" />

        <div className="app-container relative z-10 flex min-h-[76vh] items-center py-20">
          <div className={`max-w-3xl text-white ${activeHero.align === "right" ? "ml-auto text-right" : ""}`}>
            <p className="mb-5 text-xs uppercase tracking-[0.32em] text-[var(--clr-primary)]">{activeHero.kicker}</p>
            <h1 className="font-display text-5xl font-semibold leading-[0.98] md:text-7xl lg:text-8xl">
              {activeHero.title}
            </h1>
            <p className={`mt-6 max-w-xl text-base leading-7 text-white/82 md:text-lg ${activeHero.align === "right" ? "ml-auto" : ""}`}>
              {activeHero.body}
            </p>

            <div className={`mt-9 flex flex-wrap gap-3 ${activeHero.align === "right" ? "justify-end" : ""}`}>
              <Link to="/products">
                <Button className="rounded-full bg-[var(--clr-primary)] px-7 py-3 text-white hover:bg-[var(--clr-primary-dark)]">
                  Shop Outerwear
                </Button>
              </Link>
              <Link
                to="/new-arrivals"
                className="inline-flex rounded-full border border-white/60 px-7 py-3 text-sm font-medium text-white transition hover:border-white hover:bg-white/10"
              >
                New Arrivals
              </Link>
            </div>

            <div className={`mt-10 flex gap-3 ${activeHero.align === "right" ? "justify-end" : ""}`}>
              {heroSlides.map((slide, index) => (
                <button
                  key={slide.image}
                  type="button"
                  onClick={() => setHeroIndex(index)}
                  className={`h-1.5 rounded-full transition-all ${
                    index === heroIndex ? "w-12 bg-[var(--clr-primary)]" : "w-6 bg-white/45"
                  }`}
                  aria-label={`Show hero slide ${index + 1}`}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="absolute bottom-5 left-1/2 z-10 hidden -translate-x-1/2 items-center gap-6 rounded-full border border-white/20 bg-black/25 px-6 py-3 text-xs uppercase tracking-[0.18em] text-white/80 backdrop-blur md:flex">
          <span>Coats</span>
          <span className="h-1 w-1 rounded-full bg-[var(--clr-primary)]" />
          <span>Knitwear</span>
          <span className="h-1 w-1 rounded-full bg-[var(--clr-primary)]" />
          <span>Beanies</span>
          <span className="h-1 w-1 rounded-full bg-[var(--clr-primary)]" />
          <span>Accessories</span>
        </div>
      </section>

      {/* PERSONALIZED FOR YOU - Only for logged-in users */}
      {isLoggedIn && personalized.length > 0 && (
        <section className="app-container mt-12">
          <RecommendationSection
            title="Personalized For You"
            products={personalized}
            loading={recsLoading}
            layout="carousel"
          />
        </section>
      )}

      {/* TRENDING NOW - For all users */}
      {trending.length > 0 && (
        <section className="app-container mt-12">
          <RecommendationSection
            title="Trending Now"
            products={trending}
            loading={recsLoading}
            layout="grid"
            columns={4}
          />
        </section>
      )}

      {/* CUSTOMERS ALSO BOUGHT - For logged-in users */}
      {isLoggedIn && alsoBought.length > 0 && (
        <section className="app-container mt-12">
          <RecommendationSection
            title="Customers Also Bought"
            products={alsoBought}
            loading={recsLoading}
            layout="carousel"
          />
        </section>
      )}

      {/* BASED ON YOUR INTERACTIONS - For logged-in users */}
      {isLoggedIn && interactions.length > 0 && (
        <section className="app-container mt-12">
          <RecommendationSection
            title="Based on Your Activity"
            products={interactions}
            loading={recsLoading}
            layout="carousel"
          />
        </section>
      )}

      {/* FEATURED PRODUCTS - Always show */}
      <section className="app-container mt-16">
        <h2 className="text-3xl font-semibold text-gray-900 text-center mb-10">Featured Products</h2>
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="card-neutral p-4">
                <div className="h-44 bg-gray-50 animate-pulse rounded-md"></div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {featuredProducts.map((product) => (
              <ProductCard key={product.product_code || product.article_id} product={product} />
            ))}
          </div>
        )}
      </section>

      {/* NEW ARRIVALS BY SECTION */}
      <section className="app-container mt-16">
        <h2 className="text-3xl font-semibold text-gray-900 text-center">New Arrivals</h2>
        <div className="flex justify-center mt-6 text-sm text-gray-500 space-x-6 flex-wrap">
          {sectionsList.map((section) => (
            <button
              key={section.id}
              className={`pb-1 ${activeSection === section.name ? "border-b-2 border-gray-900" : ""}`}
              onClick={() => setActiveSection(section.name)}
            >
              {section.display}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-10 mt-10">
          {sectionProducts.length > 0
            ? sectionProducts.map((p) => (
              <ProductCard key={p.product_code || p.article_id} product={p} />
            ))
            : Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="card-neutral p-4">
                <div className="h-44 bg-gray-50 animate-pulse rounded-md"></div>
              </div>
            ))}
        </div>
      </section>

      {/* CATEGORY CARDS */}
      <section className="app-container mt-16 grid grid-cols-1 md:grid-cols-4 gap-6 mb-20">
        {categoryTiles.map((tile) => (
          <div
            key={tile.title}
            className="group relative flex aspect-[4/3] min-h-[250px] flex-col justify-between overflow-hidden rounded-2xl bg-[var(--clr-ink)] p-6 text-white shadow-sm"
          >
            <img
              src={tile.image}
              alt={tile.title}
              loading="lazy"
              decoding="async"
              className="absolute inset-0 h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]"
              style={{ objectPosition: tile.position }}
              onError={(event) => {
                if (tile.fallback && !event.currentTarget.dataset.fallbackApplied) {
                  event.currentTarget.dataset.fallbackApplied = "true";
                  event.currentTarget.src = tile.fallback;
                }
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/78 via-black/35 to-black/10" />
            <div className="relative z-10">
              <h3 className="mb-2 text-xl font-semibold sm:text-2xl">{tile.title}</h3>
              <p className="mb-4 text-sm text-white/86">{tile.body}</p>
            </div>
            <Link to={tile.href} className="relative z-10 self-start">
              <Button className="bg-[var(--clr-primary)] text-white hover:bg-[var(--clr-primary-dark)]">Shop Now</Button>
            </Link>
          </div>
        ))}
      </section>
    </div>
  );
}
