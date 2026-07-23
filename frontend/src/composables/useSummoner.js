import { ref } from "vue";
import { apiGet } from "../services/api";

// Encapsulates summoner-search state + the debounce/cache logic so the
// component stays declarative. Reusable and unit-testable in isolation.
export function useSummoner() {
  const region = ref("EUW");
  const riotId = ref(""); // "name#tag"
  const profile = ref(null);
  const error = ref("");
  const loading = ref(false);

  const cache = new Map(); // protects the rate-limited Riot API from repeats
  let debounceTimer = null;

  function onInput() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(search, 400);
  }

  async function search() {
    error.value = "";
    profile.value = null;

    const raw = riotId.value.trim();
    if (!raw.includes("#")) {
      if (raw) error.value = "Enter your Riot ID as name#tag";
      return;
    }

    const [name, tag] = raw.split("#");
    const key = `${region.value}:${name}#${tag}`;
    if (cache.has(key)) {
      profile.value = cache.get(key);
      return;
    }

    loading.value = true;
    try {
      const path = `/api/summoner/${region.value}/${encodeURIComponent(name)}/${encodeURIComponent(tag)}`;
      const data = await apiGet(path);
      cache.set(key, data);
      profile.value = data;
    } catch (e) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  }

  return { region, riotId, profile, error, loading, onInput, search };
}
