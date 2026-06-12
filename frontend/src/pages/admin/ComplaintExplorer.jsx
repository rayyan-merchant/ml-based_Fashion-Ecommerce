import { useEffect, useMemo, useState } from "react";
import { categories as categoriesAPI } from "../../api/api";
import { nlpAPI } from "../../api/nlpAPI";
import { ComplaintList, SkeletonLoader } from "../../components/ml";

export default function ComplaintExplorer() {
  const [categories, setCategories] = useState([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [complaints, setComplaints] = useState([]);
  const [examples, setExamples] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [loadingComplaints, setLoadingComplaints] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    setLoadingCategories(true);
    categoriesAPI.getAll(100)
      .then(res => {
        if (!mounted) return;
        const list = res.data || [];
        setCategories(list);
        const first = list[0];
        setSelectedCategoryId(String(first?.category_id || first?.id || ""));
      })
      .catch(() => setError("Failed to load categories."))
      .finally(() => mounted && setLoadingCategories(false));

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedCategoryId) return;

    setLoadingComplaints(true);
    setError("");
    nlpAPI.getCategoryComplaints(selectedCategoryId, 12)
      .then(res => {
        setComplaints(res.data?.complaints || []);
        setExamples(res.data?.example_reviews || []);
      })
      .catch(() => {
        setComplaints([]);
        setExamples([]);
        setError("Failed to load complaint themes for this category.");
      })
      .finally(() => setLoadingComplaints(false));
  }, [selectedCategoryId]);

  const selectedCategory = useMemo(
    () => categories.find(cat => String(cat.category_id || cat.id) === String(selectedCategoryId)),
    [categories, selectedCategoryId]
  );

  const strongestSignal = complaints[0];

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border bg-white p-6 shadow-sm">
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--clr-primary-dark)]">NLP Intelligence</p>
        <h1 className="mt-2 text-2xl font-semibold text-gray-950">Category Complaint Explorer</h1>
        <p className="mt-2 max-w-3xl text-sm text-gray-500">
          Find recurring complaint themes by category so merchandising, support, and product teams can act before ratings drop.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <InsightCard label="Categories scanned" value={categories.length} />
        <InsightCard label="Complaint themes" value={complaints.length} />
        <InsightCard label="Strongest signal" value={strongestSignal?.text || strongestSignal?.keyword || "-"} compact />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <label className="mb-2 block text-sm font-medium text-gray-700">Select Category</label>
          {loadingCategories ? (
            <SkeletonLoader variant="text" count={3} />
          ) : (
            <select
              value={selectedCategoryId}
              onChange={e => setSelectedCategoryId(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-[var(--clr-primary)]"
            >
              {categories.map(cat => (
                <option key={cat.category_id || cat.id} value={cat.category_id || cat.id}>
                  {cat.name || cat.product_group_name}
                </option>
              ))}
            </select>
          )}

          <div className="mt-5 rounded-lg bg-[var(--clr-primary-soft)] p-4 text-sm text-[var(--clr-primary-dark)]">
            Use this view for quality complaints, sizing issues, delivery dissatisfaction, and category-level brand health monitoring.
          </div>
        </div>

        <div className="lg:col-span-2">
          <ComplaintList
            complaints={complaints}
            examples={examples}
            categoryName={selectedCategory?.name || selectedCategory?.product_group_name}
            loading={loadingComplaints}
            error={error}
          />
        </div>
      </div>
    </div>
  );
}

function InsightCard({ label, value, compact = false }) {
  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <p className={`mt-2 font-semibold text-gray-950 ${compact ? "text-lg" : "text-3xl"}`}>{value}</p>
    </div>
  );
}
