// Thin API layer — single place for the base URL and error handling.
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function apiGet(path) {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${resp.status})`);
  }
  return resp.json();
}

export async function apiPost(path, payload) {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${resp.status})`);
  }
  return resp.json();
}
