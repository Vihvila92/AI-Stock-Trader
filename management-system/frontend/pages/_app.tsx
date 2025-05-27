import "../styles/globals.css";
import type { AppProps } from "next/app";
import React from "react";
import { useRouter } from "next/router";
import { useEffect } from "react";
import { getToken } from "../utils/auth";
import { AppearanceProvider } from "../utils/AppearanceContext";

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  useEffect(() => {
    // Älä redirectaa jos ollaan jo Login- tai AdminSetup-sivulla
    const publicRoutes = ["/Login", "/AdminSetup"];
    if (!getToken() && !publicRoutes.includes(router.pathname)) {
      // Tarkista onko käyttäjiä olemassa
      fetch("/api/users")
        .then((res) => (res.ok ? res.json() : []))
        .then((users) => {
          if (Array.isArray(users) && users.length === 0) {
            router.replace("/AdminSetup");
          } else {
            router.replace("/Login");
          }
        })
        .catch(() => router.replace("/Login"));
    }
  }, [router.pathname]);
  return (
    <AppearanceProvider>
      <Component {...pageProps} />
    </AppearanceProvider>
  );
}
