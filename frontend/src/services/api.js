// Thin API layer — single place for the base URL, auth headers, and error handling.
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

let _accessToken = null;

export function setAccessToken(token) {
  _accessToken = token;
}

export function getAccessToken() {
  return _accessToken;
}

function authHeaders() {
  if (!_accessToken) return {};
  return { Authorization: `Bearer ${_accessToken}` };
}

async function handleResponse(resp) {
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${resp.status})`);
  }
  return resp.json();
}

export async function apiGet(path) {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: authHeaders(),
    credentials: "include",
  });
  return handleResponse(resp);
}

export async function apiPost(path, payload) {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
    credentials: "include",
  });
  return handleResponse(resp);
}

export async function apiPut(path, payload) {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
    credentials: "include",
  });
  return handleResponse(resp);
}

export async function apiDelete(path) {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: authHeaders(),
    credentials: "include",
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${resp.status})`);
  }
}
