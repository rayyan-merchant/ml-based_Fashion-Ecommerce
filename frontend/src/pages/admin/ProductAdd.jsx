import { useState } from "react";
import { addProduct } from "../../api/api";

const initialForm = {
  article_id: "",
  prod_name: "",
  product_code: "",
  product_type_name: "",
  product_group_name: "",
  graphical_appearance_name: "",
  department_no: "",
  department_name: "",
  index_name: "",
  index_group_name: "",
  price: "",
  stock: "",
  colour_group_name: "",
  section_name: "",
  garment_group_name: "",
  category_id: "",
  detail_desc: ""
};

export default function ProductAdd() {
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setError("");
    setMessage("");
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await addProduct({
        ...form,
        product_code: Number(form.product_code) || Number(form.article_id) || 0,
        price: parseFloat(form.price) || 0,
        stock: parseInt(form.stock, 10) || 0,
        category_id: Number(form.category_id) || null,
        department_no: Number(form.department_no) || 0,
        product_group_name: form.product_group_name || "Unknown",
        graphical_appearance_name: form.graphical_appearance_name || "Unknown",
        index_name: form.index_name || "Unknown",
        index_group_name: form.index_group_name || "Unknown",
        garment_group_name: form.garment_group_name || "Unknown",
        product_type_name: form.product_type_name || "Unknown",
        department_name: form.department_name || "Unknown",
        colour_group_name: form.colour_group_name || "Unknown",
        section_name: form.section_name || "Unknown",
        detail_desc: form.detail_desc || ""
      });
      setMessage("Product created successfully!");
      setForm(initialForm);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to add product");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white border rounded-xl shadow-sm p-6 max-w-3xl">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Add New Product</h2>
      {message && <p className="mb-4 text-green-600 bg-green-50 border border-green-200 px-4 py-2 rounded">{message}</p>}
      {error && <p className="mb-4 text-red-600 bg-red-50 border border-red-200 px-4 py-2 rounded">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Article ID *" required>
            <input
              value={form.article_id}
              onChange={e => handleChange("article_id", e.target.value)}
              required
              className={inputClasses}
            />
          </Field>
          <Field label="Product Code">
            <input
              value={form.product_code || ""}
              onChange={e => handleChange("product_code", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Product Name *" required className="md:col-span-2">
            <input
              value={form.prod_name}
              onChange={e => handleChange("prod_name", e.target.value)}
              required
              className={inputClasses}
            />
          </Field>
          <Field label="Product Type">
            <input
              value={form.product_type_name}
              onChange={e => handleChange("product_type_name", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Product Group">
            <input
              value={form.product_group_name}
              onChange={e => handleChange("product_group_name", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Graphical Appearance">
            <input
              value={form.graphical_appearance_name}
              onChange={e => handleChange("graphical_appearance_name", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Department No">
            <input
              type="number"
              value={form.department_no}
              onChange={e => handleChange("department_no", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Department">
            <input
              value={form.department_name}
              onChange={e => handleChange("department_name", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Color Group">
            <input
              value={form.colour_group_name}
              onChange={e => handleChange("colour_group_name", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Section">
            <input
              value={form.section_name}
              onChange={e => handleChange("section_name", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Index">
            <input
              value={form.index_name}
              onChange={e => handleChange("index_name", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Index Group">
            <input
              value={form.index_group_name}
              onChange={e => handleChange("index_group_name", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Garment Group">
            <input
              value={form.garment_group_name}
              onChange={e => handleChange("garment_group_name", e.target.value)}
              className={inputClasses}
            />
          </Field>
          <Field label="Price *" required>
            <input
              type="number"
              step="0.01"
              value={form.price}
              onChange={e => handleChange("price", e.target.value)}
              required
              className={inputClasses}
            />
          </Field>
          <Field label="Stock *" required>
            <input
              type="number"
              value={form.stock}
              onChange={e => handleChange("stock", e.target.value)}
              required
              className={inputClasses}
            />
          </Field>
          <Field label="Category ID">
            <input
              value={form.category_id || ""}
              onChange={e => handleChange("category_id", e.target.value)}
              className={inputClasses}
            />
          </Field>
        </div>

        <Field label="Description">
          <textarea
            value={form.detail_desc}
            onChange={e => handleChange("detail_desc", e.target.value)}
            rows={4}
            className={inputClasses}
          />
        </Field>

        <button
          type="submit"
          disabled={submitting}
          className="w-full md:w-auto bg-gray-900 text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-800 disabled:opacity-50"
        >
          {submitting ? "Saving..." : "Create Product"}
        </button>
      </form>
    </div>
  );
}

function Field({ label, children, required, className = "" }) {
  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {children}
    </div>
  );
}

const inputClasses =
  "w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-gray-900 focus:outline-none transition";
