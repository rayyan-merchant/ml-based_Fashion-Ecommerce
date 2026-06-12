import { useEffect, useMemo, useState } from "react";
import { fetchCategories, createCategory } from "../../api/api";

export default function CategoriesView() {
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({ name: "", parent_category_id: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    fetchCategories(200, 0)
      .then(res => setCategories(res.data || []))
      .catch(() => setError("Failed to load categories"));
  };

  useEffect(() => {
    load();
  }, []);

  const tree = useMemo(() => {
    const map = {};
    categories.forEach(cat => {
      map[cat.category_id] = { ...cat, children: [] };
    });
    const root = [];
    categories.forEach(cat => {
      if (cat.parent_category_id && map[cat.parent_category_id]) {
        map[cat.parent_category_id].children.push(map[cat.category_id]);
      } else {
        root.push(map[cat.category_id]);
      }
    });
    return root;
  }, [categories]);

  const handleSubmit = async e => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      await createCategory({
        name: form.name,
        parent_category_id: form.parent_category_id ? Number(form.parent_category_id) : null
      });
      setMessage("Category created!");
      setForm({ name: "", parent_category_id: "" });
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create category");
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Category Tree</h2>
          {error && <p className="text-red-600 mb-4">{error}</p>}
          <div className="space-y-3 text-sm text-gray-700">
            {tree.length ? tree.map(node => <TreeNode key={node.category_id} node={node} depth={0} />) : <p>No categories yet.</p>}
          </div>
        </div>

        <div className="bg-white border rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Create Category</h2>
          {message && <p className="text-green-600 mb-4">{message}</p>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category Name *</label>
              <input
                value={form.name}
                onChange={e => setForm(prev => ({ ...prev, name: e.target.value }))}
                required
                className="w-full border rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Parent Category</label>
              <select
                value={form.parent_category_id}
                onChange={e => setForm(prev => ({ ...prev, parent_category_id: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="">None</option>
                {categories.map(cat => (
                  <option key={cat.category_id} value={cat.category_id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              className="bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-800"
            >
              Save Category
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function TreeNode({ node, depth }) {
  return (
    <div>
      <div className="flex items-center gap-2" style={{ paddingLeft: depth * 16 }}>
        <span className="font-medium">{node.name}</span>
        <span className="text-xs text-gray-500">#{node.category_id}</span>
      </div>
      {node.children?.length ? node.children.map(child => <TreeNode key={child.category_id} node={child} depth={depth + 1} />) : null}
    </div>
  );
}

