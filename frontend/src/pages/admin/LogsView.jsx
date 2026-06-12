import { useEffect, useState } from "react";
import { adminAuth } from "../../api/api";

export default function LogsView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    adminAuth.getLogs(100)
      .then(res => setLogs(res.data || []))
      .catch(err => {
        console.error("Failed to load admin logs:", err);
        setError(err.response?.data?.detail || "Failed to load admin logs");
      })
      .finally(() => setLoading(false));
  }, []);

  const getAdminLabel = (log) => log.admin_email || log.admin || log.admin_id || log.username || "System";
  const getTimestamp = (log) => log.timestamp || log.created_at || log.action_time || log.logged_at;
  const getDetails = (log) => log.detail || log.details || log.metadata || {};

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-semibold text-gray-900">Admin Logs</h2>
        <p className="text-gray-500 text-sm">Track critical changes made by administrators.</p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-600 uppercase text-xs tracking-wide">
            <tr>
              <th className="px-4 py-3">Log ID</th>
              <th className="px-4 py-3">Admin</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Details</th>
              <th className="px-4 py-3">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                  Loading logs...
                </td>
              </tr>
            ) : logs.length ? (
              logs.map((log, index) => (
                <tr key={log.id || log.log_id || index} className="border-t">
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{log.id || log.log_id || index + 1}</td>
                  <td className="px-4 py-3 text-gray-800">{getAdminLabel(log)}</td>
                  <td className="px-4 py-3 text-gray-600">{log.action || log.event || "audit_event"}</td>
                  <td className="px-4 py-3">
                    <pre className="text-xs bg-gray-50 border rounded p-2 overflow-auto">
{JSON.stringify(getDetails(log), null, 2)}
                    </pre>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {getTimestamp(log) ? new Date(getTimestamp(log)).toLocaleString() : "N/A"}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                  No audit logs returned by the backend.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
