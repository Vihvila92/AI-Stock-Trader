import React, { useState } from 'react';

interface Props {
  onAdminCreated: () => void;
}

export default function AdminSetup({ onAdminCreated }: Props) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      // Käytetään aina suhteellista polkua, jotta nginx-proxy toimii
      const res = await fetch(`/api/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || 'Error creating admin');
      } else {
        // Ohjataan kirjautumisruutuun adminin luonnin jälkeen
        window.location.replace('/Login');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
      <main className="max-w-md mx-auto bg-white rounded shadow p-6 mt-8">
        <form onSubmit={handleSubmit} style={{ maxWidth: 320, margin: 'auto', padding: 32 }}>
          <h2 className="text-xl font-bold mb-4">Create Admin User</h2>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Username</label>
            <input value={username} disabled className="w-full border border-gray-300 rounded px-3 py-2 bg-gray-100 text-gray-600" />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required className="w-full border border-gray-300 rounded px-3 py-2" />
          </div>
          {error && <div style={{ color: 'red', marginTop: 12 }}>{error}</div>}
          <button type="submit" disabled={loading || !password} className="w-full bg-blue-600 text-white rounded py-2 mt-2 font-semibold hover:bg-blue-700 transition-colors">
            {loading ? 'Creating...' : 'Create Admin'}
          </button>
        </form>
      </main>
  );
}
