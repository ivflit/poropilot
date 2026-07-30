import { ref } from "vue";
import { apiGet, apiPut, apiDelete } from "../services/api";
import { useSession } from "./useSession";

// Cached presets keyed by role — shared across the app.
const pools = ref({});
const loaded = ref(false);

export function useSavedPools() {
  const { isLoggedIn } = useSession();

  async function fetchAll() {
    if (!isLoggedIn.value) return;
    try {
      const list = await apiGet("/api/me/pools");
      const map = {};
      for (const p of list) map[p.role] = p.champions;
      pools.value = map;
      loaded.value = true;
    } catch {
      pools.value = {};
    }
  }

  async function save(role, champions) {
    await apiPut(`/api/me/pools/${role}`, { champions });
    pools.value = { ...pools.value, [role]: [...champions] };
  }

  async function remove(role) {
    await apiDelete(`/api/me/pools/${role}`);
    const copy = { ...pools.value };
    delete copy[role];
    pools.value = copy;
  }

  function getPool(role) {
    return pools.value[role] ?? null;
  }

  return { pools, loaded, fetchAll, save, remove, getPool };
}
