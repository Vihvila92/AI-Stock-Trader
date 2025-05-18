import React, { useState } from 'react';

interface Props {
  onLogin: () => void;
}

export default function Login({ onLogin }: Props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Dummy login, replace with real API call and session logic
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    // TODO: implement real authentication
    if (username && password) {
      // Simulate login success
      localStorage.setItem('session', '1');
      onLogin();
    } else {
      setError('Täytä käyttäjätunnus ja salasana');
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 320, margin: 'auto', padding: 32 }}>
      <h2>Kirjaudu sisään</h2>
      <div>
        <label>Käyttäjätunnus</label>
        <input value={username} onChange={e => setUsername(e.target.value)} required style={{ width: '100%' }} />
      </div>
      <div style={{ marginTop: 12 }}>
        <label>Salasana</label>
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={{ width: '100%' }} />
      </div>
      {error && <div style={{ color: 'red', marginTop: 12 }}>{error}</div>}
      <button type="submit" disabled={loading} style={{ marginTop: 16, width: '100%' }}>
        {loading ? 'Kirjaudutaan...' : 'Kirjaudu'}
      </button>
    </form>
  );
}
