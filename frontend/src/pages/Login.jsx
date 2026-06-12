import { useEffect, useState } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { useApp } from "../context/AppContext";

export default function Login() {
  const [emailOrUsername, setEmailOrUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isAdminLogin, setIsAdminLogin] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();
  const { login, loginAdmin } = useApp();

  useEffect(() => {
    if (location.pathname.startsWith("/admin/login")) {
      setIsAdminLogin(true);
    }
  }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let result;

      if (isAdminLogin) {
        // ---------- ADMIN LOGIN ----------
        if (!emailOrUsername || !password) {
          setError("Please enter username/email and password");
          setLoading(false);
          return;
        }

        result = await loginAdmin(emailOrUsername, password);
      } else {
        // ---------- CUSTOMER LOGIN ----------
        if (!emailOrUsername || !password) {
          setError("Please enter email and password");
          setLoading(false);
          return;
        }

        result = await login(emailOrUsername, password);
      }

      if (result.success) {
        if (isAdminLogin) navigate("/admin");
        else navigate("/profile");
      } else {
        setError(result.error || "Login failed");
      }
    } catch (err) {
      setError("Unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-4">
        {isAdminLogin ? "Admin Login" : "Customer Login"}
      </h1>

      {/* SWITCH BETWEEN CUSTOMER / ADMIN */}
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => {
            setIsAdminLogin(false);
            setError("");
          }}
          className={`px-4 py-2 rounded-full ${!isAdminLogin ? "bg-[var(--clr-primary)] text-white" : "bg-[var(--clr-panel)] text-gray-700"
            }`}
        >
          Customer
        </button>

        <button
          onClick={() => {
            setIsAdminLogin(true);
            setError("");
          }}
          className={`px-4 py-2 rounded-full ${isAdminLogin ? "bg-[var(--clr-primary)] text-white" : "bg-[var(--clr-panel)] text-gray-700"
            }`}
        >
          Admin
        </button>
      </div>

      {/* ERROR MESSAGE */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* LOGIN FORM */}
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-gray-700 mb-2">
            {isAdminLogin ? "Username or Email" : "Email"}
          </label>
          <input
            type={isAdminLogin ? "text" : "email"}
            value={emailOrUsername}
            onChange={(e) => setEmailOrUsername(e.target.value)}
            className="w-full px-3 py-2 border border-[var(--clr-border)] bg-[var(--clr-panel)] rounded-lg focus:ring-2 focus:ring-[var(--clr-primary)]"
            placeholder={
              isAdminLogin ? "Enter username or email" : "Enter email"
            }
          />
        </div>

        <div className="mb-4">
          <label className="block text-gray-700 mb-2">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-[var(--clr-border)] bg-[var(--clr-panel)] rounded-lg focus:ring-2 focus:ring-[var(--clr-primary)]"
            placeholder="Enter password"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-[var(--clr-primary)] text-white py-2 rounded-full hover:bg-[var(--clr-primary-dark)] disabled:opacity-50"
        >
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>

      {/* SIGNUP LINK FOR CUSTOMER */}
      {!isAdminLogin && (
        <div className="mt-4 text-center">
          <p className="text-gray-600">
            Don't have an account?{" "}
            <Link to="/signup" className="text-[var(--clr-primary-dark)] hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      )}
    </div>
  );
}
