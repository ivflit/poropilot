<script setup>
import { ref, computed } from "vue";
import { apiPost } from "../services/api";
import { useChampions } from "../composables/useChampions";

const props = defineProps({
  version: { type: String, default: null },
});

const { lookupName } = useChampions();

const input = ref("");
const region = ref("EUW");
const players = ref([]);
const loading = ref(false);
const error = ref("");

const REGIONS = ["EUW", "EUNE", "NA", "KR", "BR", "JP", "OCE", "TR", "RU", "LAN", "LAS"];

const TIER_SHORT = {
  IRON: "I", BRONZE: "B", SILVER: "S", GOLD: "G", PLATINUM: "P", EMERALD: "E",
  DIAMOND: "D", MASTER: "M", GRANDMASTER: "GM", CHALLENGER: "C",
};
const RANK_NUM = { I: "1", II: "2", III: "3", IV: "4" };
const titleCase = (s) => (s ? s[0] + s.slice(1).toLowerCase() : s);

function parseIds() {
  return input.value
    .split(/[\n,]+/)
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 5);
}

const parsedCount = computed(() => parseIds().length);

async function search() {
  const ids = parseIds();
  if (!ids.length) return;
  loading.value = true;
  error.value = "";
  players.value = [];
  try {
    const data = await apiPost("/api/multi-search", { region: region.value, riot_ids: ids });
    players.value = data.players;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function rankStr(player) {
  const entry = player.ranked?.find((e) => e.queueType === "RANKED_SOLO_5x5") ?? player.ranked?.[0];
  if (!entry) return "Unranked";
  const short = (TIER_SHORT[entry.tier] ?? "?") + (RANK_NUM[entry.rank] ?? "");
  const games = (entry.wins ?? 0) + (entry.losses ?? 0);
  const pct = games ? Math.round((entry.wins / games) * 100) : 0;
  return `${titleCase(entry.tier)} ${entry.rank} · ${entry.leaguePoints} LP · ${pct}% (${games}g)`;
}

function rankShort(player) {
  const entry = player.ranked?.find((e) => e.queueType === "RANKED_SOLO_5x5") ?? player.ranked?.[0];
  if (!entry) return null;
  return (TIER_SHORT[entry.tier] ?? "?") + (RANK_NUM[entry.rank] ?? "");
}

function avatarUrl(player) {
  return props.version && player.profile_icon_id
    ? `https://ddragon.leagueoflegends.com/cdn/${props.version}/img/profileicon/${player.profile_icon_id}.png`
    : null;
}

const champIcon = (name) => lookupName(name)?.image_url ?? null;
const pct = (wr) => Math.round(wr * 100);
</script>

<template>
  <div class="card multi-card">
    <div class="card-head">
      <h3>Multi-search</h3>
      <span class="card-sub">Paste your lobby</span>
    </div>

    <div class="multi-input-row">
      <div class="region-wrap region-wrap--multi">
        <select v-model="region" aria-label="Region">
          <option v-for="r in REGIONS" :key="r">{{ r }}</option>
        </select>
        <span class="chev">▾</span>
      </div>
      <textarea
        v-model="input"
        class="multi-textarea"
        placeholder="name#tag (one per line or comma-separated)"
        rows="3"
        aria-label="Summoner names"
      ></textarea>
    </div>

    <button
      type="button"
      class="multi-search-btn"
      :disabled="!parsedCount || loading"
      @click="search"
    >
      {{ loading ? "Searching…" : `Search ${parsedCount} player${parsedCount !== 1 ? "s" : ""}` }}
    </button>

    <p v-if="error" class="multi-error">{{ error }}</p>

    <div v-if="players.length" class="multi-results">
      <div
        v-for="p in players"
        :key="p.riot_id"
        class="multi-player"
        :class="{ 'multi-notfound': !p.found }"
      >
        <template v-if="p.found">
          <div class="mp-header">
            <img v-if="avatarUrl(p)" class="mp-avatar" :src="avatarUrl(p)" :alt="p.riot_id" />
            <div class="mp-id">
              <span class="mp-name">{{ p.riot_id }}</span>
              <span class="mp-rank">{{ rankStr(p) }}</span>
            </div>
            <div v-if="rankShort(p)" class="mp-badge">{{ rankShort(p) }}</div>
          </div>
          <div v-if="p.top_champions.length" class="mp-champs">
            <div v-for="c in p.top_champions" :key="c.champion_id" class="mp-champ">
              <img v-if="champIcon(c.champion_name)" class="mp-champ-icon" :src="champIcon(c.champion_name)" :alt="c.champion_name" />
              <span class="mp-champ-name">{{ c.champion_name }}</span>
              <span class="mp-champ-wr" :style="{ color: pct(c.win_rate) >= 50 ? 'var(--good)' : 'var(--gold)' }">{{ pct(c.win_rate) }}%</span>
              <span class="mp-champ-games">{{ c.games }}g</span>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="mp-header">
            <div class="mp-id">
              <span class="mp-name">{{ p.riot_id }}</span>
              <span class="mp-rank mp-not-found-label">Not found</span>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
