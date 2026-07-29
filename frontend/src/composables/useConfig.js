import { ref } from "vue";
import { apiGet } from "../services/api";

// Reads server config: whether AI is enabled, and the current Data Dragon
// version (used to build profile-icon URLs). Degrades safely if the call fails.
export function useConfig() {
  const aiEnabled = ref(false);
  const authEnabled = ref(false);
  const ddragonVersion = ref(null);

  async function load() {
    try {
      const cfg = await apiGet("/api/config");
      aiEnabled.value = !!cfg.ai_enabled;
      authEnabled.value = !!cfg.auth_enabled;
      ddragonVersion.value = cfg.ddragon_version || null;
    } catch {
      aiEnabled.value = false;
      authEnabled.value = false;
      ddragonVersion.value = null;
    }
  }

  return { aiEnabled, authEnabled, ddragonVersion, load };
}
