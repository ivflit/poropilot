<script setup>
import { onMounted, watch } from "vue";
import ChampionPicker from "./ChampionPicker.vue";
import { useDraft } from "../composables/useDraft";
import { useChampions } from "../composables/useChampions";
import { useSession } from "../composables/useSession";
import { useSavedPools } from "../composables/useSavedPools";

const props = defineProps({
  poolChampions: { type: Array, default: () => [] },
});

const { role, championPool, allyPicks, enemyBans, enemyPicks, suggestions, loading, error, submit } =
  useDraft();
const { load, lookupName } = useChampions();
const { isLoggedIn } = useSession();
const { pools, fetchAll, save, getPool } = useSavedPools();

onMounted(load);

// When the user logs in (or the session restores), fetch their saved presets
// and load the one for the current role.
watch(isLoggedIn, async (loggedIn) => {
  if (loggedIn) {
    await fetchAll();
    loadPreset(role.value);
  }
}, { immediate: true });

// Auto-load the saved preset when the role changes.
watch(role, (r) => loadPreset(r));

function loadPreset(r) {
  if (!isLoggedIn.value) return;
  const saved = getPool(r);
  championPool.value = saved ? [...saved] : [];
}

async function savePreset() {
  await save(role.value, championPool.value);
}

function seedFromProfile() {
  if (props.poolChampions.length) {
    championPool.value = [...props.poolChampions];
  }
}

const ROLES = [
  { value: "TOP", label: "TOP" },
  { value: "JUNGLE", label: "JGL" },
  { value: "MID", label: "MID" },
  { value: "BOT", label: "BOT" },
  { value: "SUPPORT", label: "SUP" },
];

const CONF_BARS = { high: 3, medium: 2, low: 1 };
const CONF_COLOR = { high: "var(--good)", medium: "var(--gold)", low: "var(--muted)" };

const icon = (name) => lookupName(name)?.image_url ?? null;
const lit = (conf, i) => i < (CONF_BARS[conf] ?? 0);
const confColor = (conf) => CONF_COLOR[conf] ?? "var(--muted)";

const hasSavedPool = (r) => !!(pools.value && pools.value[r]);
</script>

<template>
  <section class="draft">
    <div class="draft-head">
      <div class="draft-badge">🧭</div>
      <div class="draft-title">
        <h2>Draft assistant</h2>
        <div class="draft-sub">AI pick suggestions from the live draft.</div>
      </div>
      <span class="ai-badge">AI</span>
    </div>

    <div class="draft-body">
      <div class="section-label">Your role</div>
      <div class="role-seg">
        <button
          v-for="r in ROLES"
          :key="r.value"
          type="button"
          class="role-btn"
          :class="{ active: role === r.value, 'has-preset': hasSavedPool(r.value) }"
          @click="role = r.value"
        >
          {{ r.label }}
        </button>
      </div>

      <div class="pickers">
        <ChampionPicker v-model="championPool" label="Your champion pool" dot="var(--gold)" />
        <ChampionPicker v-model="allyPicks" label="Allied picks" dot="var(--good)" />
        <ChampionPicker v-model="enemyBans" label="Enemy bans" dot="var(--error)" />
        <ChampionPicker v-model="enemyPicks" label="Enemy picks" dot="var(--accent-strong)" />
      </div>

      <div v-if="isLoggedIn || poolChampions.length" class="pool-actions">
        <button
          v-if="isLoggedIn"
          class="pool-action-btn"
          type="button"
          :disabled="!championPool.length"
          @click="savePreset"
        >
          Save as {{ role }} pool
        </button>
        <button
          v-if="poolChampions.length"
          class="pool-action-btn pool-action-seed"
          type="button"
          @click="seedFromProfile"
        >
          Seed from profile
        </button>
      </div>

      <button class="suggest-btn" type="button" :disabled="loading" @click="submit">
        <span>✨</span>{{ loading ? "Thinking…" : "Suggest a pick" }}
      </button>

      <p v-if="error" class="draft-error" role="alert">{{ error }}</p>

      <div v-if="suggestions" class="recs">
        <div class="section-label">Recommended picks · {{ role }}</div>
        <ol class="suggestions">
          <li v-for="(s, i) in suggestions" :key="s.champion" class="rec">
            <div class="rec-icon-wrap">
              <img v-if="icon(s.champion)" class="rec-icon" :src="icon(s.champion)" :alt="s.champion" />
              <div v-else class="rec-icon rec-icon-fallback"></div>
              <span class="rec-num">{{ i + 1 }}</span>
            </div>
            <div class="rec-main">
              <div class="rec-top">
                <span class="rec-name">{{ s.champion }}</span>
                <span class="tag" :class="s.in_pool ? 'tag-pool' : 'tag-meta'">
                  {{ s.in_pool ? "your pool" : "meta pick" }}
                </span>
              </div>
              <div class="rec-reason">{{ s.reason }}</div>
            </div>
            <div class="rec-conf">
              <div class="signal">
                <span
                  v-for="n in 3"
                  :key="n"
                  class="sbar"
                  :style="{ background: lit(s.confidence, n - 1) ? confColor(s.confidence) : 'var(--line)' }"
                ></span>
              </div>
              <div class="conf-label" :style="{ color: confColor(s.confidence) }">{{ s.confidence }}</div>
            </div>
          </li>
        </ol>
      </div>
    </div>
  </section>
</template>
