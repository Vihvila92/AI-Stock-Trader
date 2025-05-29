// Simple JWT auth util for frontend
export function setToken(token: string) {
  localStorage.setItem("access_token", token);
}

export function getToken(): string | null {
  return localStorage.getItem("access_token");
}

export function removeToken() {
  localStorage.removeItem("access_token");
}

export function authHeader(): Record<string, string> | undefined {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : undefined;
}
