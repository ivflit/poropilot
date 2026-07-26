import { ref, watch } from "vue";
import { apiGet } from "../services/api";

// Encapsulates summoner-search state + the debounce/cache logic so the
// component stays declarative. Reusable and unit-testable in isolation.
export function useSummoner() {
  const region = ref("EUW");
  const riotId = ref(""); // "name#tag"
  const queue = ref("all"); // "all" | "solo" | "flex"
  const profile = ref(null);
  const pool = ref(null);
  const error = ref("");
  const loading = ref(false);
  const poolLoading = ref(false);

  const profileCache = new Map(); // protects the rate-limited Riot API from repeats
  const poolCache = new Map(); // keyed by queue too — filters mustn't share numbers
  let searched = null; // the {name, tag, region} currently on screen
  let debounceTimer = null;

  function onInput() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(search, 400);
  }

  async function search() {
    error.value = "";
    profile.value = null;
    pool.value = null;
    searched = null;

    const raw = riotId.value.trim();
    if (!raw.includes("#")) {
      if (raw) error.value = "Enter your Riot ID as name#tag";
      return;
    }

    const [name, tag] = raw.split("#");
    const key = `${region.value}:${name}#${tag}`;

    if (profileCache.has(key)) {
      profile.value = profileCache.get(key);
    } else {
      loading.value = true;
      try {
        profile.value = await apiGet(summonerPath(name, tag));
        profileCache.set(key, profile.value);
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    }

    if (!profile.value) return;
    searched = { name, tag, region: region.value };
    await loadPool();
  }

  // The champion pool is best-effort — a failure here must not hide the profile.
  async function loadPool() {
    if (!searched) return;

    const { name, tag, region: searchedRegion } = searched;
    const key = `${searchedRegion}:${name}#${tag}:${queue.value}`;
    if (poolCache.has(key)) {
      pool.value = poolCache.get(key);
      return;
    }

    poolLoading.value = true;
    try {
      const result = await apiGet(poolPath(name, tag, searchedRegion));
      poolCache.set(key, result);
      pool.value = result;
    } catch {
      pool.value = null;
    } finally {
      poolLoading.value = false;
    }
  }

  // Switching the filter re-reads the pool but leaves the profile on screen —
  // only the queue-dependent numbers change.
  watch(queue, () => {
    pool.value = null;
    loadPool();
  });

  const summonerPath = (name, tag) =>
    `/api/summoner/${region.value}/${encodeURIComponent(name)}/${encodeURIComponent(tag)}`;
  const poolPath = (name, tag, searchedRegion) =>
    `/api/pool/${searchedRegion}/${encodeURIComponent(name)}/${encodeURIComponent(tag)}` +
    `?queue=${queue.value}`;

  return { region, riotId, queue, profile, pool, error, loading, poolLoading, onInput, search };
}
