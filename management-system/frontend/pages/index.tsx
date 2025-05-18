import React, { useEffect, useState } from 'react';
import AdminSetup from './AdminSetup';
import Login from './Login';

interface User {
  id: number;
  username: string;
}

export default function Home() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSession(!!localStorage.getItem('session'));
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    fetch(`${apiUrl}/api/users`)
      .then(async res => {
        if (!res.ok) {
          const text = await res.text();
          setError(`API error: ${res.status} ${res.statusText} - ${text}`);
          console.error('API error:', res.status, res.statusText, text);
          setLoading(false);
          return null;
        }
        return res.json();
      })
      .then(data => {
        if (!data) return;
        if (Array.isArray(data)) {
          setUsers(data);
        } else {
          setUsers([]);
          setError('API did not return an array: ' + JSON.stringify(data));
          console.error('API did not return an array:', data);
        }
        setLoading(false);
      })
      .catch(err => {
        setError('Network or fetch error: ' + err);
        setLoading(false);
        console.error('Fetch error:', err);
      });
  }, []);

  if (loading) {
    return <main style={{ padding: 32 }}>
      <p>Loading...</p>
      <pre style={{ color: '#888', fontSize: 12 }}>
        NEXT_PUBLIC_API_URL: {process.env.NEXT_PUBLIC_API_URL || 'not set'}
      </pre>
    </main>;
  }

  if (error) {
    return <main style={{ padding: 32, color: 'red' }}>
      <h2>Virhe</h2>
      <pre>{error}</pre>
      <pre style={{ color: '#888', fontSize: 12 }}>
        NEXT_PUBLIC_API_URL: {process.env.NEXT_PUBLIC_API_URL || 'not set'}
      </pre>
      <button onClick={() => window.location.reload()}>Yritä uudelleen</button>
    </main>;
  }

  // Jos adminia ei ole, näytä adminin luonti
  const adminExists = users.some(u => u.username === 'admin');
  if (!adminExists) {
    return <AdminSetup onAdminCreated={() => window.location.reload()} />;
  }

  // Jos ei sessiota, näytä kirjautuminen
  if (!session) {
    return <Login onLogin={() => setSession(true)} />;
  }

  // Jos sessio, näytä pääsivu
  return (
    <main style={{ padding: 32 }}>
      <h1>Tervetuloa!</h1>
      <p>Olet kirjautunut sisään.</p>
      <ul>
        {users.map(user => (
          <li key={user.id}>{user.username}</li>
        ))}
      </ul>
    </main>
  );
}
