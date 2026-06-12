import { useEffect, useMemo, useState } from "react";
import { fetchCustomers } from "../../api/api";

export default function CustomersView() {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    fetchCustomers(0, 200).then(res => setCustomers(res.data || []));
  }, []);

  const filtered = useMemo(() => {
    return customers.filter(customer => {
      const matchesSearch =
        !search ||
        (customer.customer_id || "").toLowerCase().includes(search.toLowerCase()) ||
        `${customer.first_name || ""} ${customer.last_name || ""}`.toLowerCase().includes(search.toLowerCase());

      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && customer.active) ||
        (statusFilter === "inactive" && !customer.active);

      return matchesSearch && matchesStatus;
    });
  }, [customers, search, statusFilter]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Customers</h2>
          <p className="text-gray-500 text-sm">Monitor user base, loyalty, and engagement.</p>
        </div>
        <div className="flex flex-col md:flex-row gap-3">
          <input
            type="text"
            placeholder="Search customers"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          />
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-600 uppercase text-xs tracking-wide">
            <tr>
              <th className="px-4 py-3">Customer ID</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Age</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length ? (
              filtered.map(customer => (
                <tr key={customer.customer_id} className="border-t">
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{customer.customer_id}</td>
                  <td className="px-4 py-3 text-gray-800">
                    {customer.first_name || customer.last_name
                      ? `${customer.first_name || ""} ${customer.last_name || ""}`
                      : "N/A"}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{customer.email || "—"}</td>
                  <td className="px-4 py-3 text-gray-600">{customer.age ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 text-xs rounded-full font-medium ${
                        customer.active ? "bg-green-50 text-green-600" : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {customer.active ? "Active" : "Inactive"}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                  No customers found for the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
