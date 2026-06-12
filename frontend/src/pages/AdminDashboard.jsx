import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import DashboardOverview from "./admin/DashboardOverview";
import ProductsView from "./admin/ProductsView";
import ProductAdd from "./admin/ProductAdd";
import ProductStock from "./admin/ProductStock";
import ProductPrice from "./admin/ProductPrice";
import CategoriesView from "./admin/CategoriesView";
import OrdersView from "./admin/OrdersView";
import CustomersView from "./admin/CustomersView";
import ReviewsView from "./admin/ReviewsView";
import AnalyticsView from "./admin/AnalyticsView";
import EventsView from "./admin/EventsView";
import LogsView from "./admin/LogsView";
import SettingsView from "./admin/SettingsView";

// ML Dashboard imports
import MLReviewsDashboard from "./admin/MLReviewsDashboard";
import ComplaintExplorer from "./admin/ComplaintExplorer";
import SegmentationDashboard from "./admin/SegmentationDashboard";
import ForecastDashboard from "./admin/ForecastDashboard";
import MLAnalyticsDashboard from "./admin/MLAnalyticsDashboard";
import { useApp } from "../context/AppContext";

const navStructure = [
  {
    label: "Dashboard",
    items: [{ id: "dashboard", title: "Overview" }]
  },
  {
    label: "Products",
    items: [
      { id: "products-view", title: "View Products" },
      { id: "products-add", title: "Add Product" },
      { id: "products-stock", title: "Update Stock" },
      { id: "products-price", title: "Update Price" }
    ]
  },
  {
    label: "Operations",
    items: [
      { id: "categories", title: "Categories" },
      { id: "orders", title: "Orders" },
      { id: "customers", title: "Customers" },
      { id: "reviews", title: "Reviews" },
      { id: "events", title: "Events" }
    ]
  },
  {
    label: "ML Intelligence",
    items: [
      { id: "ml-reviews", title: "Reviews Insights" },
      { id: "ml-complaints", title: "Complaint Explorer" },
      { id: "ml-segmentation", title: "Segmentation" },
      { id: "ml-forecasting", title: "Forecasting" },
      { id: "ml-analytics", title: "ML Analytics" }
    ]
  },
  {
    label: "System",
    items: [
      { id: "logs", title: "Admin Logs" },
      { id: "settings", title: "Settings" }
    ]
  }
];

const componentMap = {
  dashboard: DashboardOverview,
  "products-view": ProductsView,
  "products-add": ProductAdd,
  "products-stock": ProductStock,
  "products-price": ProductPrice,
  categories: CategoriesView,
  orders: OrdersView,
  customers: CustomersView,
  reviews: ReviewsView,
  analytics: AnalyticsView,
  events: EventsView,
  logs: LogsView,
  settings: SettingsView,
  // ML Dashboard components
  "ml-reviews": MLReviewsDashboard,
  "ml-complaints": ComplaintExplorer,
  "ml-segmentation": SegmentationDashboard,
  "ml-forecasting": ForecastDashboard,
  "ml-analytics": MLAnalyticsDashboard
};

const routeToSection = (pathname) => {
  if (pathname === "/admin" || pathname === "/admin/") return "dashboard";
  if (pathname.includes("/admin/products/pricing")) return "products-price";
  if (pathname.includes("/admin/products/new") || pathname.includes("/admin/products/") && pathname.includes("/edit")) return "products-add";
  if (pathname.includes("/admin/products")) return "products-view";
  if (pathname.includes("/admin/categories")) return "categories";
  if (pathname.includes("/admin/orders")) return "orders";
  if (pathname.includes("/admin/customers")) return "customers";
  if (pathname.includes("/admin/reviews")) return "reviews";
  if (pathname.includes("/admin/intelligence/complaints")) return "ml-complaints";
  if (pathname.includes("/admin/intelligence/sentiment")) return "ml-reviews";
  if (pathname.includes("/admin/intelligence/forecasting")) return "ml-forecasting";
  if (pathname.includes("/admin/intelligence/segments")) return "ml-segmentation";
  if (pathname.includes("/admin/intelligence")) return "ml-analytics";
  if (pathname.includes("/admin/inventory")) return "products-stock";
  if (pathname.includes("/admin/analytics")) return "analytics";
  if (pathname.includes("/admin/settings/audit")) return "logs";
  if (pathname.includes("/admin/settings")) return "settings";
  if (pathname.includes("/admin/notifications")) return "events";
  return "dashboard";
};

const sectionToRoute = {
  dashboard: "/admin",
  "products-view": "/admin/products",
  "products-add": "/admin/products/new",
  "products-stock": "/admin/inventory",
  "products-price": "/admin/products/pricing",
  categories: "/admin/categories",
  orders: "/admin/orders",
  customers: "/admin/customers",
  reviews: "/admin/reviews",
  analytics: "/admin/analytics",
  events: "/admin/notifications",
  logs: "/admin/settings/audit",
  settings: "/admin/settings",
  "ml-reviews": "/admin/intelligence/sentiment",
  "ml-complaints": "/admin/intelligence/complaints",
  "ml-segmentation": "/admin/intelligence/segments",
  "ml-forecasting": "/admin/intelligence/forecasting",
  "ml-analytics": "/admin/intelligence/recommendations"
};

export default function AdminDashboard() {
  const [activeSection, setActiveSection] = useState("dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const { admin, isAdmin, logoutAdmin } = useApp();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    setActiveSection(routeToSection(location.pathname));
  }, [location.pathname]);
  const visibleNav = useMemo(() => {
    return navStructure
      .map(section => ({
        ...section,
        items: section.items.filter(item => item.id !== "settings" || isAdmin)
      }))
      .filter(section => section.items.length);
  }, [isAdmin]);
  const ActiveComponent = useMemo(() => componentMap[activeSection] || DashboardOverview, [activeSection]);
  const currentTitle = useMemo(() => {
    for (const section of navStructure) {
      const found = section.items.find(item => item.id === activeSection);
      if (found) return found.title;
    }
    return "Overview";
  }, [activeSection]);

  if (!isAdmin) {
    return (
      <div className="p-10 text-center">
        <p className="text-xl text-gray-600">You must be an administrator to view this page.</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[var(--clr-surface)]">
      <aside className={`fixed inset-y-0 left-0 z-30 bg-[var(--clr-sidebar-bg)] text-[var(--clr-sidebar-text)] border-r border-black shadow-sm transition-all ${collapsed ? "w-20" : "w-72"}`}>
        <div className="px-6 py-5 border-b border-white/10 flex items-center justify-between">
          <div>
            {!collapsed && <p className="text-xs uppercase text-[var(--clr-primary)] tracking-wide">Commerce Intelligence</p>}
            <h1 className="text-2xl font-display text-white">LAYR</h1>
          </div>
          <button
            onClick={() => setCollapsed(prev => !prev)}
            className="text-[var(--clr-sidebar-text)] hover:text-white"
          >
            {collapsed ? ">>" : "<<"}
          </button>
        </div>
        <nav className="h-[calc(100vh-80px)] space-y-6 overflow-y-auto p-4">
          {visibleNav.map(section => (
            <div key={section.label}>
              {!collapsed && <p className="text-xs uppercase text-gray-500 mb-2">{section.label}</p>}
              <div className="space-y-1">
                {section.items.map(item => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveSection(item.id);
                      navigate(sectionToRoute[item.id] || "/admin");
                    }}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium ${activeSection === item.id ? "bg-[var(--clr-primary)] text-black" : "text-[var(--clr-sidebar-text)] hover:bg-white/10"
                      }`}
                    title={collapsed ? item.title : undefined}
                  >
                    {collapsed ? item.title.charAt(0) : item.title}
                  </button>
                ))}
              </div>
            </div>
          ))}
          <button
            onClick={() => {
              logoutAdmin();
              window.location.href = "/login";
            }}
            className="w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-red-300 hover:bg-red-500/10"
            title={collapsed ? "Logout" : undefined}
          >
            Logout
          </button>
        </nav>
      </aside>

      <main className={`min-w-0 flex-1 transition-all ${collapsed ? "ml-20" : "ml-72"}`}>
        <header className="sticky top-0 z-20 border-b border-[var(--clr-border)] bg-white/95 px-6 py-4 backdrop-blur">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-[var(--clr-primary-dark)]">Admin Panel</p>
              <h2 className="text-2xl font-semibold text-gray-950">{currentTitle}</h2>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <button
                onClick={() => navigate("/admin/products/new")}
                className="rounded-full bg-gray-950 px-4 py-2 font-medium text-white hover:bg-black"
              >
                New Product
              </button>
              <button
                onClick={() => navigate("/admin/intelligence/recommendations")}
                className="rounded-full border border-[var(--clr-border)] px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
              >
                ML Insights
              </button>
              <div className="rounded-full bg-[var(--clr-panel)] px-4 py-2 text-gray-700">
                {admin?.username || admin?.email || "Admin"}
              </div>
            </div>
          </div>
        </header>
        <div className="p-6">
          <ActiveComponent />
        </div>
      </main>
    </div>
  );
}
