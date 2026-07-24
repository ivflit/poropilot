import { ref } from "vue";
import { apiGet } from "../services/api";

// Reads server feature flags (e.g. whether AI is configured) so the UI can hide
// features that aren't available. Defaults to "off" if the check fails.
export function useConfig() {
  const aiEnabled = ref(false);

  async function load() {
    try {
      const cfg = await apiGet("/api/config");
      aiEnabled.value = !!cfg.ai_enabled;
    } catch {
      aiEnabled.value = false;
    }
  }

  return { aiEnabled, load };
}
