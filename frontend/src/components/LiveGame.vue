<script setup>
import { ref, watch } from "vue";
import { apiGet } from "../services/api";
import { useChampions } from "../composables/useChampions";

const props = defineProps({
  region: { type: String, required: true },
  name: { type: String, required: true },
  tag: { type: String, required: true },
  version: { type: String, default: null },
});

const { lookupName } = useChampions();

const data = ref(null);
const loading = ref(false);
const error = ref("");

const champIcon = (name) => lookupName(name)?.image_url ?? null;

const TIER_SHORT = {
  IRON: "I", BRONZE: "B", SILVER: "S", GOLD: "G", PLATINUM: "P", EMERALD: "E",
  DIAMOND: "D", MASTER: "M", GRANDMASTER: "GM", CHALLENGER: "C",
};

function shortRank(rank) {
  if (!rank) return null;
  for (const [tier, short] of Object.entries(TIER_SHORT)) {
    if (rank.startsWith(tier)) return rank.replace(tier, short);
  }
  return rank;
}

function team(participants, teamId) {
  return participants.filter((p) => p.team_id === teamId);
}

function gameDuration(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

async function loadLive() {
  loading.value = true;
  error.value = "";
  data.value = null;
  try {
    data.value = await apiGet(
      `/api/live/${props.region}/${encodeURIComponent(props.name)}/${encodeURIComponent(props.tag)}`,
    );
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

watch(() => [props.region, props.name, props.tag], loadLive, { immediate: true });
</script>

<template>
  <div class="card live-card">
    <div class="card-head">
      <h3>Live game</h3>
      <button type="button" class="live-refresh" @click="loadLive" :disabled="loading">
        {{ loading ? "…" : "Refresh" }}
      </button>
    </div>

    <p v-if="loading" class="pool-note">Checking for active game…</p>
    <p v-else-if="error" class="pool-note">{{ error }}</p>
    <p v-else-if="!data || !data.in_game" class="pool-note">Not currently in a game.</p>

    <template v-else>
      <div class="live-meta">
        <span class="live-mode">{{ data.game_mode }}</span>
        <span class="live-time">{{ gameDuration(data.game_length_sec) }}</span>
      </div>

      <div class="live-teams">
        <div class="live-team live-blue">
          <div class="live-team-label">Blue Team</div>
          <div v-for="p in team(data.participants, 100)" :key="p.riot_id" class="live-player">
            <img v-if="champIcon(p.champion_name)" class="live-champ-icon" :src="champIcon(p.champion_name)" :alt="p.champion_name" />
            <div class="live-player-info">
              <span class="live-player-name">{{ p.riot_id }}</span>
              <span class="live-player-champ">{{ p.champion_name }}</span>
            </div>
            <span v-if="p.rank" class="live-rank">{{ shortRank(p.rank) }}</span>
            <span v-else class="live-rank live-unranked">Unranked</span>
          </div>
        </div>
        <div class="live-team live-red">
          <div class="live-team-label">Red Team</div>
          <div v-for="p in team(data.participants, 200)" :key="p.riot_id" class="live-player">
            <img v-if="champIcon(p.champion_name)" class="live-champ-icon" :src="champIcon(p.champion_name)" :alt="p.champion_name" />
            <div class="live-player-info">
              <span class="live-player-name">{{ p.riot_id }}</span>
              <span class="live-player-champ">{{ p.champion_name }}</span>
            </div>
            <span v-if="p.rank" class="live-rank">{{ shortRank(p.rank) }}</span>
            <span v-else class="live-rank live-unranked">Unranked</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
