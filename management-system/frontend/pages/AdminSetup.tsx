import React, { useState } from "react";

interface Props {
  onAdminCreated: () => void;
}

export default function AdminSetup({ onAdminCreated }: Props) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      // Always use relative path so nginx-proxy works
      const res = await fetch(`/api/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || "Error creating admin");
      } else {
        // Redirect to login screen after admin creation
        window.location.replace("/Login");
      }
    } catch (err) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto mt-8 max-w-md rounded bg-white p-6 shadow">
      <form
        onSubmit={handleSubmit}
        style={{ maxWidth: 320, margin: "auto", padding: 32 }}
      >
        <h2 className="mb-4 text-xl font-bold">Create Admin User</h2>
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium">Username</label>
          <input
            value={username}
            disabled
            className="w-full rounded border border-gray-300 bg-gray-100 px-3 py-2 text-gray-600"
          />
        </div>
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full rounded border border-gray-300 px-3 py-2"
          />
        </div>
        {error && <div style={{ color: "red", marginTop: 12 }}>{error}</div>}
        <button
          type="submit"
          disabled={loading || !password}
          className="mt-2 w-full rounded bg-blue-600 py-2 font-semibold text-white transition-colors hover:bg-blue-700"
        >
          {loading ? "Creating..." : "Create Admin"}
        </button>
      </form>
    </main>
  );
}
