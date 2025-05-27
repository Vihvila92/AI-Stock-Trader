import DashboardLayout from "./DashboardLayout";
import { useEffect, useState } from "react";
import { authHeader } from "../utils/auth";
import { useRouter } from "next/router";

export default function Dashboard() {
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [checking, setChecking] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const fetchCurrentUser = async () => {
      const token = authHeader();
      if (!token) {
        setChecking(false);
        return;
      }
      const res = await fetch("/api/users/me", { headers: token });
      if (res.ok) {
        const data = await res.json();
        setCurrentUser(data);
        setChecking(false);
      } else if (res.status === 401) {
        // Ei kirjautunut, tarkista onko käyttäjiä olemassa
        const usersRes = await fetch("/api/users");
        if (usersRes.ok) {
          const users = await usersRes.json();
          if (Array.isArray(users) && users.length === 0) {
            router.replace("/AdminSetup");
          } else {
            router.replace("/Login");
          }
        } else {
          router.replace("/Login");
        }
      } else {
        setChecking(false);
      }
    };
    fetchCurrentUser();
  }, [router]);

  if (checking) {
    return (
      <DashboardLayout>
        <div>Loading...</div>
      </DashboardLayout>
    );
  }

  if (!currentUser) {
    return null;
  }

  return (
    <DashboardLayout>
      <h2 className="text-2xl font-semibold mb-4">Dashboard</h2>
      <div className="bg-white rounded-lg shadow p-6">
        {/* This is the main dashboard page. */}
        <p>Welcome to the management system dashboard.</p>
      </div>
    </DashboardLayout>
  );
}
