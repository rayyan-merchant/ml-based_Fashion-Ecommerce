import { Link, useLocation } from "react-router-dom";

const pageCopy = {
  "/lookbook": {
    title: "The LAYR Lookbook",
    eyebrow: "Editorial curation",
    body: "Seasonal edits, outfit ideas, and product stories curated from the intelligence system.",
    cta: "Shop the Edit"
  },
  "/brands": {
    title: "Brand Directory",
    eyebrow: "Boutique partners",
    body: "Explore collections by label, category, and current customer sentiment.",
    cta: "Browse Products"
  }
};

export default function EditorialPage() {
  const { pathname } = useLocation();
  const copy = pageCopy[pathname] || pageCopy["/lookbook"];

  return (
    <div className="min-h-[60vh] bg-[var(--clr-surface)]">
      <section className="app-container py-20">
        <div className="grid gap-10 lg:grid-cols-[1fr_0.9fr] lg:items-center">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-[var(--clr-primary-dark)]">{copy.eyebrow}</p>
            <h1 className="mt-4 font-display text-5xl text-[var(--clr-ink)] md:text-7xl">{copy.title}</h1>
            <p className="mt-5 max-w-xl text-lg text-[var(--clr-body)]">{copy.body}</p>
            <Link
              to="/products"
              className="mt-8 inline-flex rounded-full bg-[var(--clr-primary)] px-7 py-3 text-sm font-medium text-white transition hover:bg-[var(--clr-primary-dark)]"
            >
              {copy.cta}
            </Link>
          </div>
          <div className="overflow-hidden rounded-2xl border border-[var(--clr-border)] bg-white shadow-sm">
            <img
              src="/hero.jpg"
              alt="LAYR editorial fashion collection"
              className="h-[420px] w-full object-cover"
            />
          </div>
        </div>
      </section>
    </div>
  );
}
