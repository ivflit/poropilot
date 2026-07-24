import { ref } from "vue";
import { apiPost } from "../services/api";

// Holds the draft-board state and talks to the AI draft endpoint.
export function useDraft() {
  const role = ref("MID");
  const championPool = ref([]);
  const allyPicks = ref([]);
  const enemyBans = ref([]);
  const enemyPicks = ref([]);

  const suggestions = ref(null);
  const loading = ref(false);
  const error = ref("");

  async function submit() {
    error.value = "";
    suggestions.value = null;
    loading.value = true;
    try {
      const data = await apiPost("/api/draft", {
        role: role.value,
        champion_pool: championPool.value,
        ally_picks: allyPicks.value,
        enemy_bans: enemyBans.value,
        enemy_picks: enemyPicks.value,
      });
      suggestions.value = data.suggestions;
    } catch (e) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  }

  return {
    role,
    championPool,
    allyPicks,
    enemyBans,
    enemyPicks,
    suggestions,
    loading,
    error,
    submit,
  };
}
