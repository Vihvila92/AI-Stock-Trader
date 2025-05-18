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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${apiUrl}/api/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || 'Virhe adminin luonnissa');
      } else {
        onAdminCreated();
      }
    } catch (err) {
      setError('Verkkovirhe');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 320, margin: 'auto', padding: 32 }}>
      <h2>Luo admin-käyttäjä</h2>
      <div>
        <label>Käyttäjätunnus</label>
        <input value={username} disabled style={{ width: '100%' }} />
      </div>
      <div style={{ marginTop: 12 }}>
        <label>Salasana</label>
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={{ width: '100%' }} />
      </div>
      {error && <div style={{ color: 'red', marginTop: 12 }}>{error}</div>}
      <button type="submit" disabled={loading || !password} style={{ marginTop: 16, width: '100%' }}>
        {loading ? 'Luodaan...' : 'Luo admin'}
      </button>
    </form>
  );
}
