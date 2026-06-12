import { useState } from "react";

export default function SettingsView() {
  const [passwordForm, setPasswordForm] = useState({ current: "", next: "", confirm: "" });
  const [message, setMessage] = useState("");

  const handleChange = (field, value) => {
    setPasswordForm(prev => ({ ...prev, [field]: value }));
    setMessage("");
  };

  const handlePasswordUpdate = e => {
    e.preventDefault();
    if (passwordForm.next !== passwordForm.confirm) {
      setMessage("Passwords do not match");
      return;
    }
    setMessage("Password update endpoint not implemented. Wire to backend when ready.");
    setPasswordForm({ current: "", next: "", confirm: "" });
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border rounded-xl p-6 shadow-sm max-w-xl">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Settings</h2>
        <h3 className="text-lg font-medium text-gray-800 mb-3">Change Password</h3>
        {message && <p className="mb-3 text-sm text-orange-600">{message}</p>}
        <form onSubmit={handlePasswordUpdate} className="space-y-4">
          <Field label="Current Password">
            <input
              type="password"
              value={passwordForm.current}
              onChange={e => handleChange("current", e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
              required
            />
          </Field>
          <Field label="New Password">
            <input
              type="password"
              value={passwordForm.next}
              onChange={e => handleChange("next", e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
              required
            />
          </Field>
          <Field label="Confirm New Password">
            <input
              type="password"
              value={passwordForm.confirm}
              onChange={e => handleChange("confirm", e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
              required
            />
          </Field>
          <button className="bg-gray-900 text-white px-4 py-2 rounded-lg">Update Password</button>
        </form>
      </div>

      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-medium text-gray-800 mb-3">Maintenance</h3>
        <div className="space-y-3">
          <button
            onClick={() => alert("Hook this button to admin_refresh_matviews() when backend endpoint is ready.")}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg"
          >
            Refresh Materialized Views
          </button>
          <button
            onClick={() => alert("Hook this toggle to backend service control when available.")}
            className="bg-gray-900 text-white px-4 py-2 rounded-lg"
          >
            Toggle Recommendation Service
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
    </div>
  );
}

