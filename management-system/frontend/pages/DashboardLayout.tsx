import { ReactNode } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-white shadow px-4 py-3 flex items-center justify-between">
        <h1 className="text-xl font-bold">AI Stock Trader</h1>
        <nav className="space-x-4">
          <a href="/dashboard" className="text-gray-700 hover:text-blue-600">Dashboard</a>
          {/* Ylläpito-valikko */}
          <div className="inline-block relative group">
            <button className="text-gray-700 hover:text-blue-600 focus:outline-none">Ylläpito ▾</button>
            <div className="absolute right-0 mt-2 w-40 bg-white border rounded shadow-lg opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity z-10">
              <a href="/users" className="block px-4 py-2 text-gray-700 hover:bg-gray-100">Käyttäjät</a>
              <a href="/settings" className="block px-4 py-2 text-gray-700 hover:bg-gray-100">Asetukset</a>
            </div>
          </div>
        </nav>
      </header>
      <main className="flex-1 p-6 max-w-5xl mx-auto w-full">
        {children}
      </main>
      <footer className="bg-white text-center text-xs text-gray-400 py-2 border-t">&copy; {new Date().getFullYear()} AI Stock Trader</footer>
    </div>
  );
}
