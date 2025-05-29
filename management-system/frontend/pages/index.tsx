import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { getToken } from "../utils/auth";
import Login from "./Login";
import Dashboard from "./dashboard";

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setIsAuthenticated(!!getToken());
  }, []);

  if (!isAuthenticated) {
    return <Login onLogin={() => router.replace("/dashboard")} />;
  }

  return <Dashboard />;
}
