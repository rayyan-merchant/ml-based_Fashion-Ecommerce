import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="app-container flex min-h-[60vh] items-center justify-center py-20 text-center">
      <div>
        <p className="text-sm uppercase tracking-[0.22em] text-[var(--clr-primary-dark)]">404</p>
        <h1 className="mt-3 font-display text-5xl text-[var(--clr-ink)]">Page Not Found</h1>
        <p className="mx-auto mt-4 max-w-md text-[var(--clr-body)]">
          The page may have moved, but the collection is still within reach.
        </p>
        <Link
          to="/products"
          className="mt-7 inline-flex rounded-full bg-[var(--clr-primary)] px-7 py-3 text-sm font-medium text-white hover:bg-[var(--clr-primary-dark)]"
        >
          Browse Products
        </Link>
      </div>
    </div>
  );
}
