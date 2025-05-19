import React, { useEffect, useState } from 'react';

interface User {
  id: number;
  username: string;
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [newUsername, setNewUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Hae käyttäjät backendistä
  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/users');
      if (!res.ok) throw new Error('Käyttäjien haku epäonnistui');
      const data = await res.json();
      setUsers(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Lisää uusi käyttäjä
  const addUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: newUsername }),
      });
      if (!res.ok) throw new Error('Käyttäjän lisäys epäonnistui');
      setNewUsername('');
      fetchUsers();
    } catch (e: any) {
      setError(e.message);
    }
  };

  // Poista käyttäjä
  const deleteUser = async (id: number) => {
    setError(null);
    try {
      const res = await fetch(`/api/users/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Käyttäjän poisto epäonnistui');
      fetchUsers();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Käyttäjien hallinta</h1>
      <form onSubmit={addUser} className="flex gap-2 mb-4">
        <input
          className="border px-2 py-1 flex-1"
          value={newUsername}
          onChange={e => setNewUsername(e.target.value)}
          placeholder="Uusi käyttäjänimi"
          required
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-1 rounded">Lisää</button>
      </form>
      {error && <div className="text-red-600 mb-2">{error}</div>}
      {loading ? (
        <div>Ladataan käyttäjiä...</div>
      ) : (
        <ul className="divide-y">
          {users.map(user => (
            <li key={user.id} className="flex justify-between items-center py-2">
              <span>{user.username}</span>
              <button
                onClick={() => deleteUser(user.id)}
                className="text-red-600 hover:underline"
              >
                Poista
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
