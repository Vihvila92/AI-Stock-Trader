import DashboardLayout from "./DashboardLayout";
import { useState, useEffect } from "react";
import { authHeader } from "../utils/auth";
import { useRouter } from "next/router";
import { useAppearance, getAppearanceValue } from "../utils/AppearanceContext";

interface Setting {
  key: string;
  value: string;
  label?: string;
  category?: string;
  type?: string;
  enum?: any; // voi olla string TAI array
}

// Utility: Format category name nicely
function formatCategoryName(cat: string) {
  if (!cat) return "";
  // Replace underscores with spaces, split to words
  let words = cat.replace(/_/g, " ").split(" ");
  words = words.map((w) => {
    if (["api", "id", "url", "ip"].includes(w.toLowerCase()))
      return w.toUpperCase();
    return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();
  });
  return words.join(" ");
}

// Kovakoodattu välilehtien järjestys
const CATEGORY_ORDER = [
  "general",
  "appearance",
  "trading",
  "notifications",
  "security",
  "advanced",
];

export default function Settings() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<string>("");
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [settings, setSettings] = useState<Setting[]>([]);
  const [loading, setLoading] = useState(true);
  const [edited, setEdited] = useState<{ [key: string]: string }>({});
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string>("");
  const { refresh, appearance } = useAppearance();

  useEffect(() => {
    const fetchCurrentUser = async () => {
      const token = authHeader();
      if (!token) {
        router.replace("/Login");
        return;
      }
      const res = await fetch("/api/users/me", { headers: token });
      if (res.status === 401) {
        router.replace("/Login");
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setCurrentUser(data);
      }
    };
    fetchCurrentUser();
  }, [router]);

  useEffect(() => {
    const fetchSettings = async () => {
      setLoading(true);
      const token = authHeader();
      if (!token) return;
      const res = await fetch("/api/settings", { headers: token });
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
        // Set first tab as active by default
        const categories = Array.from(
          new Set(data.map((s: Setting) => s.category || "general")),
        );
        if (categories.length > 0) {
          setActiveTab(String(categories[0]));
        } else {
          setActiveTab("general");
        }
      }
      setLoading(false);
    };
    fetchSettings();
  }, [currentUser]);

  if (!currentUser?.permissions?.can_edit_settings) {
    return (
      <DashboardLayout>
        <div className="text-red-600">
          You do not have permission to view this page.
        </div>
      </DashboardLayout>
    );
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div>Loading settings...</div>
      </DashboardLayout>
    );
  }

  // Kerää kategoriat: kaikki uniikit, ei null/tyhjää, pakota string
  const categories = Array.from(
    new Set(settings.map((s) => String(s.category ?? ""))),
  ).filter(Boolean);

  // Järjestä: ensin CATEGORY_ORDER-mukaiset, loput aakkosissa
  categories.sort((a, b) => {
    const ia = CATEGORY_ORDER.indexOf(a);
    const ib = CATEGORY_ORDER.indexOf(b);
    if (ia === -1 && ib === -1) return a.localeCompare(b);
    if (ia === -1) return 1;
    if (ib === -1) return -1;
    return ia - ib;
  });

  // Fallback: jos activeTab ei löydy kategorioista, näytetään ensimmäinen
  const shownTab = categories.includes(activeTab)
    ? activeTab
    : categories[0] || "";

  // Helper: parse enum always to array
  function parseEnum(enumVal: any): any[] {
    if (!enumVal) return [];
    if (Array.isArray(enumVal)) return enumVal;
    if (typeof enumVal === "string") {
      try {
        const arr = JSON.parse(enumVal);
        return Array.isArray(arr) ? arr : [];
      } catch {
        return [];
      }
    }
    return [];
  }

  // Handle input change
  const handleInputChange = (key: string, value: string) => {
    setEdited((prev) => ({ ...prev, [key]: value }));
  };

  // Save all edited settings for the current tab
  const handleSave = async () => {
    setSaving(true);
    setSaveStatus("");
    const token = authHeader();
    const tabSettings = settings.filter(
      (s) => (s.category || "general") === activeTab,
    );
    let success = true;
    for (const setting of tabSettings) {
      if (
        edited[setting.key] !== undefined &&
        edited[setting.key] !== setting.value
      ) {
        const res = await fetch(
          `/api/settings/${encodeURIComponent(setting.key)}`,
          {
            method: "PUT",
            headers: { ...token, "Content-Type": "application/json" },
            body: JSON.stringify({ value: edited[setting.key] }),
          },
        );
        if (!res.ok) success = false;
      }
    }
    setSaving(false);
    setSaveStatus(
      success ? "Settings saved!" : "Failed to save some settings.",
    );
    // Refresh settings from backend
    if (success) {
      setEdited({});
      await refresh(); // Päivitä appearance-asetukset contextiin
      const res = await fetch("/api/settings", { headers: token });
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
      }
      // Pakotettu reload
      window.location.reload();
    }
  };

  return (
    <DashboardLayout>
      <h2 className="text-2xl font-semibold mb-4">Settings</h2>
      <div className="bg-white rounded-lg shadow p-6">
        {/* Tab navigation */}
        <div className="border-b mb-4">
          <nav className="flex space-x-4" aria-label="Tabs">
            {categories.map((cat) => (
              <button
                key={cat}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors duration-150 focus:outline-none ${
                  shownTab === cat
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-blue-600"
                }`}
                onClick={() => setActiveTab(cat)}
              >
                {formatCategoryName(cat)}
              </button>
            ))}
          </nav>
        </div>
        {/* Tab content */}
        <div>
          {settings
            .filter((s) => String(s.category) === shownTab)
            .map((setting) => {
              // Enum-tyyppinen asetus
              const enumOptions = parseEnum(setting.enum);
              if (setting.type === "enum" && enumOptions.length > 0) {
                const lang =
                  typeof navigator !== "undefined" &&
                  navigator.language?.startsWith("fi")
                    ? "fi"
                    : "en";
                return (
                  <div key={setting.key} className="mb-6">
                    <label
                      className="font-semibold block mb-1"
                      htmlFor={setting.key}
                    >
                      {setting.label || setting.key}
                    </label>
                    <select
                      id={setting.key}
                      className="border rounded px-3 py-2 w-full text-gray-800"
                      value={
                        edited[setting.key] !== undefined
                          ? edited[setting.key]
                          : (setting.value ?? "")
                      }
                      onChange={(e) =>
                        handleInputChange(setting.key, e.target.value)
                      }
                      disabled={saving}
                    >
                      {enumOptions.map((opt: any) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label?.[lang] || opt.label?.en || opt.value}
                        </option>
                      ))}
                    </select>
                  </div>
                );
              }
              // Logo-url erikoiskäsittely (kuva, url, upload)
              if (setting.key === "logo_url") {
                let logoUrl = edited[setting.key];
                if (logoUrl === undefined) {
                  try {
                    const parsed = JSON.parse(setting.value);
                    logoUrl = parsed.value || "";
                  } catch {
                    logoUrl = setting.value;
                  }
                }
                return (
                  <div key={setting.key} className="mb-6">
                    <label
                      className="font-semibold block mb-1"
                      htmlFor={setting.key}
                    >
                      {setting.label || setting.key}
                    </label>
                    <div>
                      {logoUrl ? (
                        <div className="mb-2">
                          <img
                            src={logoUrl}
                            alt="Logo"
                            style={{
                              maxWidth: 120,
                              maxHeight: 80,
                              background: "#fff",
                              border: "1px solid #eee",
                              padding: 4,
                            }}
                          />
                        </div>
                      ) : null}
                      <input
                        id={setting.key}
                        type="text"
                        className="border rounded px-3 py-2 w-full text-gray-800 mb-2"
                        value={
                          edited[setting.key] !== undefined
                            ? edited[setting.key]
                            : (() => {
                                try {
                                  const parsed = JSON.parse(setting.value);
                                  return parsed.value !== undefined
                                    ? String(parsed.value)
                                    : setting.value;
                                } catch {
                                  return setting.value;
                                }
                              })()
                        }
                        onChange={(e) =>
                          handleInputChange(setting.key, e.target.value)
                        }
                        disabled={saving}
                        placeholder="https://... tai /logo.png"
                      />
                      <input
                        type="file"
                        accept="image/*"
                        className="mt-1"
                        disabled={saving}
                        onChange={async (e) => {
                          const file = e.target.files?.[0];
                          if (!file) return;
                          const formData = new FormData();
                          formData.append("file", file);
                          const filename = `/logo_uploaded_${Date.now()}.${file.name
                            .split(".")
                            .pop()}`;
                          try {
                            const res = await fetch("/api/upload", {
                              method: "POST",
                              body: formData,
                            });
                            if (res.ok) {
                              handleInputChange(setting.key, filename);
                            } else {
                              alert("Upload failed");
                            }
                          } catch {
                            alert("Upload not supported in this environment.");
                          }
                        }}
                      />
                      <div className="text-xs text-gray-500 mt-1">
                        Voit antaa suoran url:n tai ladata logon (vain
                        dev-ympäristössä).
                      </div>
                    </div>
                  </div>
                );
              }
              // Muut asetukset
              return (
                <div key={setting.key} className="mb-6">
                  <label
                    className="font-semibold block mb-1"
                    htmlFor={setting.key}
                  >
                    {setting.label || setting.key}
                  </label>
                  <input
                    id={setting.key}
                    type={
                      setting.type === "password"
                        ? "password"
                        : setting.type === "number"
                          ? "number"
                          : "text"
                    }
                    className="border rounded px-3 py-2 w-full text-gray-800"
                    value={
                      edited[setting.key] !== undefined
                        ? edited[setting.key]
                        : (() => {
                            try {
                              const parsed = JSON.parse(setting.value);
                              return parsed.value !== undefined
                                ? String(parsed.value)
                                : setting.value;
                            } catch {
                              return setting.value;
                            }
                          })()
                    }
                    onChange={(e) =>
                      handleInputChange(setting.key, e.target.value)
                    }
                    disabled={saving}
                  />
                </div>
              );
            })}
          <button
            className="bg-blue-600 text-white px-6 py-2 rounded shadow hover:bg-blue-700 disabled:opacity-50"
            onClick={handleSave}
            disabled={saving || Object.keys(edited).length === 0}
          >
            {saving ? "Saving..." : "Save"}
          </button>
          {saveStatus && (
            <div className="mt-2 text-green-600">{saveStatus}</div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
