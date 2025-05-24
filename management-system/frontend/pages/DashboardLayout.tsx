import Link from "next/link";
import React, { useEffect, useState, useRef } from "react";
import { getToken } from "../utils/auth";
import { useAppearance, getAppearanceValue } from '../utils/AppearanceContext';

interface User {
  id: number;
  username: string;
  permissions?: Record<string, boolean>;
}

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard", perm: null },
];

const ADMIN_MENU = [
  { href: "/users", label: "Users", perm: "can_manage_users" },
  { href: "/settings", label: "Settings", perm: "can_edit_settings" },
  { href: "/maintenance", label: "Maintenance", perm: "can_see_maintenance" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [adminMenuOpen, setAdminMenuOpen] = useState(false);
  const closeTimeout = useRef<NodeJS.Timeout | null>(null);
  const { appearance, loading: appearanceLoading } = useAppearance();

  // Kaikki ulkoasuasetukset kannasta ja theme huomioiden
  const logoUrl = getAppearanceValue(appearance, 'logo_url');
  const isValidLogo = typeof logoUrl === 'string' && logoUrl.trim().length > 0 && !logoUrl.startsWith('{');
  const siteName = getAppearanceValue(appearance, 'site_name', 'Management System');
  const navBg = getAppearanceValue(appearance, 'login_box_color', 'bg-blue-700');
  const navText = getAppearanceValue(appearance, 'login_text_color', 'text-white');
  const pageBg = getAppearanceValue(appearance, 'login_background_color', 'bg-gray-100');

  const handleMouseEnter = () => {
    if (closeTimeout.current) clearTimeout(closeTimeout.current);
    setAdminMenuOpen(true);
  };
  const handleMouseLeave = () => {
    closeTimeout.current = setTimeout(() => setAdminMenuOpen(false), 150);
  };

  useEffect(() => {
    const fetchUser = async () => {
      const token = getToken();
      if (!token) {
        setLoading(false);
        return;
      }
      const res = await fetch("/api/users/me", { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      }
      setLoading(false);
    };
    fetchUser();
  }, []);

  if (loading || appearanceLoading) {
    return (
      <div className={`min-h-screen ${pageBg} flex items-center justify-center`}>
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  // Filter admin menu links by permissions
  const adminMenuLinks = ADMIN_MENU.filter(link =>
    user && (link.perm === null || (link.perm && user.permissions?.[link.perm]))
  );

  return (
    <div className={`min-h-screen ${pageBg}`}>
      {/* Main navigation bar */}
      <nav className={`${navBg} ${navText} px-6 py-4 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          {isValidLogo ? (
            <img src={logoUrl} alt="Logo" className="h-8 w-8 object-contain" />
          ) : (
            <span className="font-bold text-xl">{siteName}</span>
          )}
        </div>
        <div className="space-x-4 flex items-center">
          {NAV_LINKS.map(link => (
            <Link key={link.href} href={link.href} className="hover:underline">{link.label}</Link>
          ))}
          {adminMenuLinks.length > 0 && (
            <div
              className="relative inline-block"
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
            >
              <button className="hover:underline focus:outline-none">Admin</button>
              {adminMenuOpen && (
                <div className="absolute right-0 bg-white text-black mt-2 rounded shadow-lg min-w-[160px] z-50">
                  {adminMenuLinks.map(link => (
                    <Link key={link.href} href={link.href} className="block px-4 py-2 hover:bg-gray-100">{link.label}</Link>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </nav>
      {/* Main content */}
      <main className="max-w-4xl mx-auto py-8 px-4">
        {children}
      </main>
    </div>
  );
}
