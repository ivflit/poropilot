import { ref } from "vue";
import { apiGet } from "../services/api";

// Encapsulates summoner-search state + the debounce/cache logic so the
// component stays declarative. Reusable and unit-testable in isolation.
export function useSummoner() {
  const region = ref("EUW");
  const riotId = ref(""); // "name#tag"
  const profile = ref(null);
  const pool = ref(null);
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
    pool.value = null;

    const raw = riotId.value.trim();
    if (!raw.includes("#")) {
      if (raw) error.value = "Enter your Riot ID as name#tag";
      return;
    }

    const [name, tag] = raw.split("#");
    const key = `${region.value}:${name}#${tag}`;

    if (cache.has(key)) {
      profile.value = cache.get(key);
    } else {
      loading.value = true;
      try {
        profile.value = await apiGet(summonerPath(name, tag));
        cache.set(key, profile.value);
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    }

    // The champion pool is best-effort — a failure here must not hide the profile.
    if (profile.value) {
      try {
        pool.value = await apiGet(poolPath(name, tag));
      } catch {
        pool.value = null;
      }
    }
  }

  const summonerPath = (name, tag) =>
    `/api/summoner/${region.value}/${encodeURIComponent(name)}/${encodeURIComponent(tag)}`;
  const poolPath = (name, tag) =>
    `/api/pool/${region.value}/${encodeURIComponent(name)}/${encodeURIComponent(tag)}`;

  return { region, riotId, profile, pool, error, loading, onInput, search };
}
