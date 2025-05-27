import React, { useState, useEffect } from "react";
import { setToken } from "../utils/auth";
import { useRouter } from "next/router";
import { useAppearance, getAppearanceValue } from "../utils/AppearanceContext";

interface Props {
  onLogin: () => void;
}

export default function Login({ onLogin }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { appearance, loading: appearanceLoading } = useAppearance();

  const logoUrl = getAppearanceValue(appearance, "logo_url");
  const isValidLogo = typeof logoUrl === "string" && logoUrl.trim().length > 0;
  const siteName = getAppearanceValue(
    appearance,
    "site_name",
    "Management System",
  );
  const loginBg = getAppearanceValue(
    appearance,
    "login_background_color",
    "#f9fafb",
  );
  const boxBg = getAppearanceValue(appearance, "login_box_color", "#fff");
  const textColor = getAppearanceValue(
    appearance,
    "login_text_color",
    "#111827",
  );

  useEffect(() => {
    // Jos käyttäjiä ei ole, ohjataan adminin luontiin
    fetch("/api/users")
      .then((res) => (res.ok ? res.json() : []))
      .then((users) => {
        if (Array.isArray(users) && users.length === 0) {
          router.replace("/AdminSetup");
        }
      });
  }, [router]);

  if (appearanceLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          background: loginBg,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ color: "#888" }}>Loading...</div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username, password }),
      });
      if (!res.ok) {
        setError("Incorrect username or password");
        setLoading(false);
        return;
      }
      const data = await res.json();
      setToken(data.access_token);
      // Ohjataan suoraan dashboardiin kirjautumisen jälkeen
      router.replace("/dashboard");
    } catch (err) {
      setError("Login error");
    }
    setLoading(false);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: loginBg,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <main
        className="max-w-md mx-auto rounded shadow p-6 mt-8"
        style={{
          background: boxBg,
          color: textColor,
          width: 400,
          boxShadow: "0 2px 16px 0 #0001",
          borderRadius: 12,
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          {isValidLogo ? (
            <img
              src={logoUrl}
              alt="Logo"
              style={{ maxWidth: 120, maxHeight: 80, margin: "0 auto" }}
            />
          ) : (
            <span style={{ fontWeight: 700, fontSize: 28 }}>{siteName}</span>
          )}
        </div>
        <form
          onSubmit={handleSubmit}
          style={{ maxWidth: 320, margin: "auto", padding: 0 }}
        >
          <h2
            style={{
              textAlign: "center",
              fontWeight: 700,
              fontSize: 24,
              marginBottom: 24,
            }}
          >
            Login
          </h2>
          <div style={{ marginBottom: 20 }}>
            <label
              style={{ display: "block", marginBottom: 6, fontWeight: 500 }}
            >
              Username
            </label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{
                width: "100%",
                padding: 10,
                borderRadius: 6,
                border: "1px solid #d1d5db",
                background: "#f3f4f6",
                color: textColor,
                fontSize: 16,
                outline: "none",
              }}
            />
          </div>
          <div style={{ marginBottom: 20 }}>
            <label
              style={{ display: "block", marginBottom: 6, fontWeight: 500 }}
            >
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: "100%",
                padding: 10,
                borderRadius: 6,
                border: "1px solid #d1d5db",
                background: "#f3f4f6",
                color: textColor,
                fontSize: 16,
                outline: "none",
              }}
            />
          </div>
          {error && (
            <div style={{ color: "red", marginTop: 12, marginBottom: 8 }}>
              {error}
            </div>
          )}
          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: 8,
              width: "100%",
              background: "#2563eb",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              padding: 12,
              fontWeight: 600,
              fontSize: 16,
              boxShadow: "0 1px 4px #0001",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
      </main>
    </div>
  );
}
