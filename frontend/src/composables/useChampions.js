import { ref } from "vue";
import { apiGet } from "../services/api";

// Module-level cache so the champion map is fetched once for the whole app,
// no matter how many components use it. A failed fetch degrades gracefully —
// lookups then fall back to the raw champion id.
let cache = null;
let inflight = null;

export function useChampions() {
  const champions = ref(cache ?? {});
  const ready = ref(cache !== null);

  async function load() {
    if (cache) {
      champions.value = cache;
      ready.value = true;
      return;
    }
    try {
      if (!inflight) inflight = apiGet("/api/champions");
      cache = await inflight;
      champions.value = cache;
    } catch {
      cache = null;
      inflight = null; // allow a later retry
    } finally {
      ready.value = true;
    }
  }

  function lookup(championId) {
    return champions.value[championId] ?? null;
  }

  return { champions, ready, load, lookup };
}
