import React, { useEffect, useState } from "react";
import DashboardLayout from "./DashboardLayout";
import { authHeader } from "../utils/auth";

interface User {
  id: number;
  username: string;
  permissions?: Record<string, boolean>;
  password?: string;
}

const PERMISSIONS = [
  { key: "can_manage_users", label: "User Management" },
  { key: "can_edit_settings", label: "Edit Settings" },
  { key: "can_reset_passwords", label: "Reset Passwords" },
];

function UserModal({
  user,
  open,
  onClose,
  onSave,
  onDelete,
  isNew,
  currentUser,
}: {
  user: User | null;
  open: boolean;
  onClose: () => void;
  onSave: (user: User & { password?: string; oldPassword?: string }) => void;
  onDelete?: (id: number) => void;
  isNew?: boolean;
  currentUser: User | null;
}) {
  const [username, setUsername] = useState(user?.username || "");
  const [permissions, setPermissions] = useState<Record<string, boolean>>(
    user?.permissions || {},
  );
  const [password, setPassword] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  useEffect(() => {
    setUsername(user?.username || "");
    if (user?.username === "admin") {
      const allPerms: Record<string, boolean> = {};
      PERMISSIONS.forEach((p) => {
        allPerms[p.key] = true;
      });
      setPermissions(allPerms);
    } else {
      setPermissions(user?.permissions || {});
    }
    setPassword("");
    setOldPassword("");
  }, [user, open]);
  if (!open) return null;
  const isAdmin = currentUser?.username === "admin";
  const canResetPasswords =
    isAdmin || currentUser?.permissions?.can_reset_passwords;
  const isSelf = currentUser?.id === user?.id;
  const showPasswordReset = isAdmin || canResetPasswords || (isSelf && !isNew);
  const requireOldPassword = isSelf && !isAdmin && !canResetPasswords && !isNew;
  const modalUser: User = {
    id: user?.id ?? 0,
    username,
    permissions,
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30">
      <div className="relative min-w-[320px] rounded bg-white p-6 shadow-lg">
        <button
          className="absolute right-2 top-2 text-gray-500"
          onClick={onClose}
        >
          ✕
        </button>
        <h2 className="mb-2 text-lg font-bold">
          {isNew ? "Add User" : "Edit User"}
        </h2>
        <div className="mb-2">
          <label className="block text-sm">Username</label>
          <input
            className="w-full border px-2 py-1"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={user?.username === "admin" || !isNew}
          />
        </div>
        {!isNew && (
          <div className="mb-2 text-xs text-gray-500">ID: {user?.id}</div>
        )}
        {isNew && (
          <div className="mb-2">
            <label className="block text-sm">Password</label>
            <input
              className="w-full border px-2 py-1"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter password"
            />
          </div>
        )}
        {showPasswordReset && !isNew && (
          <div className="mb-2">
            {requireOldPassword && (
              <>
                <label className="block text-sm">Current Password</label>
                <input
                  className="mb-2 w-full border px-2 py-1"
                  type="password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  placeholder="Enter current password"
                />
              </>
            )}
            <label className="block text-sm">New Password</label>
            <input
              className="w-full border px-2 py-1"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={
                requireOldPassword
                  ? "Enter new password"
                  : "Leave empty if not changing"
              }
            />
          </div>
        )}
        {(user?.username !== "admin" || isNew) && (
          <div className="mb-2">
            <div className="mb-1 text-sm">Permissions</div>
            <div className="flex gap-4">
              {PERMISSIONS.map((p) => (
                <label key={p.key} className="flex items-center gap-1">
                  <input
                    type="checkbox"
                    checked={!!permissions[p.key]}
                    onChange={() =>
                      setPermissions((prev) => ({
                        ...prev,
                        [p.key]: !prev[p.key],
                      }))
                    }
                    disabled={user?.username === "admin"}
                  />
                  {p.label}
                </label>
              ))}
            </div>
          </div>
        )}
        <div className="mt-2 flex gap-2">
          <button
            className="rounded bg-blue-600 px-4 py-1 text-white"
            onClick={() =>
              onSave({
                ...modalUser,
                password: password || undefined,
                oldPassword: oldPassword || undefined,
              })
            }
            disabled={isNew && !password}
          >
            {isNew ? "Add" : "Save"}
          </button>
          {!isNew &&
            onDelete &&
            user?.id !== undefined &&
            user?.username !== "admin" && (
              <button
                className="rounded bg-red-600 px-4 py-1 text-white"
                onClick={() => {
                  if (window.confirm("Delete user?")) onDelete(user.id);
                }}
                type="button"
              >
                Delete User
              </button>
            )}
        </div>
      </div>
    </div>
  );
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalUser, setModalUser] = useState<User | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalIsNew, setModalIsNew] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/users", { headers: authHeader() || {} });
      if (!res.ok) throw new Error("Failed to fetch users");
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

  useEffect(() => {
    setUsers((prevUsers) =>
      prevUsers.map((u) => {
        if (u.username === "admin") {
          const allPerms: Record<string, boolean> = {};
          PERMISSIONS.forEach((p) => {
            allPerms[p.key] = true;
          });
          return { ...u, permissions: allPerms };
        }
        return u;
      }),
    );
  }, [loading]);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      const token = authHeader();
      if (!token) return;
      const res = await fetch("/api/users/me", { headers: token });
      if (res.ok) {
        const data = await res.json();
        setCurrentUser(data);
      }
    };
    fetchCurrentUser();
  }, []);

  const handleSaveUser = async (user: User & { password?: string }) => {
    setError(null);
    if (modalIsNew) {
      try {
        const res = await fetch("/api/users", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(authHeader() || {}),
          },
          body: JSON.stringify({
            username: user.username,
            password: user.password || "password",
            permissions: user.permissions,
          }),
        });
        if (!res.ok) throw new Error("Failed to add user");
        setModalOpen(false);
        setModalUser(null);
        setModalIsNew(false);
        fetchUsers();
      } catch (e: any) {
        setError(e.message);
      }
    } else {
      try {
        const isAdmin = user.username === "admin";
        const body: any = { username: user.username };
        if (!isAdmin) body.permissions = user.permissions;
        if (user.password) body.password = user.password;
        const res = await fetch(`/api/users/${user.id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            ...(authHeader() || {}),
          },
          body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error("Failed to update user");
        setModalOpen(false);
        setModalUser(null);
        setModalIsNew(false);
        fetchUsers();
      } catch (e: any) {
        setError(e.message);
      }
    }
  };

  const handleDeleteUser = async (id: number) => {
    setError(null);
    try {
      const res = await fetch(`/api/users/${id}`, {
        method: "DELETE",
        headers: authHeader() || {},
      });
      if (!res.ok) throw new Error("Failed to delete user");
      setModalOpen(false);
      setModalUser(null);
      setModalIsNew(false);
      fetchUsers();
    } catch (e: any) {
      setError(e.message);
    }
  };

  if (!currentUser?.permissions?.can_manage_users) {
    return (
      <DashboardLayout>
        <div className="text-red-600">
          You do not have permission to view this page.
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="mx-auto max-w-xl p-4">
        <h1 className="mb-4 text-2xl font-bold">User Management</h1>
        <button
          className="mb-4 rounded bg-blue-600 px-4 py-1 text-white"
          onClick={() => {
            setModalUser({ id: 0, username: "", permissions: {} });
            setModalOpen(true);
            setModalIsNew(true);
          }}
        >
          Add User
        </button>
        {error && <div className="mb-2 text-red-600">{error}</div>}
        {loading ? (
          <div>Loading users...</div>
        ) : (
          <ul className="divide-y">
            {users.map((user) => (
              <li
                key={user.id}
                className="cursor-pointer border-b py-2 hover:bg-gray-50"
                onClick={() => {
                  setModalUser(user);
                  setModalOpen(true);
                  setModalIsNew(false);
                }}
              >
                <span>{user.username}</span>
              </li>
            ))}
          </ul>
        )}
        <UserModal
          user={modalUser}
          open={modalOpen}
          onClose={() => {
            setModalOpen(false);
            setModalUser(null);
            setModalIsNew(false);
          }}
          onSave={handleSaveUser}
          onDelete={handleDeleteUser}
          isNew={modalIsNew}
          currentUser={currentUser}
        />
      </div>
    </DashboardLayout>
  );
}
