import React, { createContext, useContext, useEffect, useState } from "react";

export type AppearanceSettings = {
  login_background_color?: string;
  login_box_color?: string;
  login_text_color?: string;
  logo_url?: string;
  site_name?: string;
  theme?: "light" | "dark" | "system"; // theme voi olla myös 'system'
  [key: string]: any;
};

const AppearanceContext = createContext<{
  appearance: AppearanceSettings;
  loading: boolean;
  refresh: () => Promise<void>;
}>({
  appearance: {},
  loading: true,
  refresh: async () => {},
});

export const useAppearance = () => useContext(AppearanceContext);

// Utility: Palauta oikea arvo (esim. väri) nykyisen teeman ja kannan mukaan
export function getAppearanceValue(
  appearance: AppearanceSettings,
  key: string,
  fallback?: string,
): string {
  // theme: 'light', 'dark' tai 'system'
  let theme = appearance.theme || "light";
  if (theme === "system") {
    if (
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      theme = "dark";
    } else {
      theme = "light";
    }
  }
  if (theme === "dark" && appearance[`${key}_dark`]) {
    return appearance[`${key}_dark`];
  }
  if (theme === "light" && appearance[`${key}_light`]) {
    return appearance[`${key}_light`];
  }
  if (appearance[key]) return appearance[key];
  return fallback || "";
}

export const AppearanceProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [appearance, setAppearance] = useState<AppearanceSettings>({});
  const [loading, setLoading] = useState(true);
  const [systemTheme, setSystemTheme] = useState<"light" | "dark">("light");

  const fetchAppearance = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/settings?category=appearance");
      const data = await res.json();
      // data: [{ key, value, ... }]
      const obj: AppearanceSettings = {};
      for (const s of data) {
        // Jos value on objekti (esim. { value: "#fff" }), käytä valuea
        let v = s.value;
        if (typeof v === "string") {
          try {
            const parsed = JSON.parse(v);
            if (parsed && typeof parsed === "object" && "value" in parsed) {
              v = parsed.value;
            }
          } catch {}
        }
        obj[s.key] = v;
      }
      setAppearance({ ...obj });
    } catch (e) {
      setAppearance({});
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchAppearance();
  }, []);

  // Listen system theme if needed
  useEffect(() => {
    if (typeof window === "undefined") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => setSystemTheme(mq.matches ? "dark" : "light");
    handler();
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  // Theme tulee kannasta, mutta voidaan asettaa <html> classiin dynaamisesti
  useEffect(() => {
    // theme: 'light', 'dark' tai 'system'
    let theme = appearance.theme || "light";
    if (theme === "system") theme = systemTheme;
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [appearance.theme, systemTheme]);

  return (
    <AppearanceContext.Provider
      value={{ appearance, loading, refresh: fetchAppearance }}
    >
      {children}
    </AppearanceContext.Provider>
  );
};
