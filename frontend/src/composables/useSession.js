import { ref, computed } from "vue";
import { apiGet, apiPost, apiPut, setAccessToken } from "../services/api";

// Shared reactive state — one session for the whole app.
const user = ref(null);
const loading = ref(false);

const isLoggedIn = computed(() => !!user.value);

export function useSession() {
  async function signup(email, password) {
    const { access_token } = await apiPost("/api/auth/signup", { email, password });
    setAccessToken(access_token);
    user.value = await apiGet("/api/auth/me");
  }

  async function login(email, password) {
    const { access_token } = await apiPost("/api/auth/login", { email, password });
    setAccessToken(access_token);
    user.value = await apiGet("/api/auth/me");
  }

  async function logout() {
    await apiPost("/api/auth/logout", {});
    setAccessToken(null);
    user.value = null;
  }

  async function refresh() {
    try {
      const { access_token } = await apiPost("/api/auth/refresh", {});
      setAccessToken(access_token);
      user.value = await apiGet("/api/auth/me");
    } catch {
      setAccessToken(null);
      user.value = null;
    }
  }

  async function linkRiotId(region, name, tag) {
    user.value = await apiPut("/api/auth/me/riot-id", { region, name, tag });
  }

  // Try to restore the session from the refresh cookie on app load.
  async function restore() {
    loading.value = true;
    await refresh();
    loading.value = false;
  }

  return { user, loading, isLoggedIn, signup, login, logout, refresh, linkRiotId, restore };
}
