<script setup>
import { ref, watch, computed } from "vue";
import { apiGet } from "../services/api";
import { useChampions } from "../composables/useChampions";

const props = defineProps({
  region: { type: String, required: true },
  name: { type: String, required: true },
  tag: { type: String, required: true },
  queue: { type: String, default: "all" },
});

const { lookupName } = useChampions();

const matches = ref([]);
const aggregate = ref(null);
const loading = ref(false);
const totalFetched = ref(0);
const loadingMore = ref(false);

const role = ref("all");
const result = ref("all");
const sort = ref("newest");
const championFilter = ref("");
const opponentFilter = ref("");
const showAdvanced = ref(false);
const expanded = ref(null);

const ROLES = [
  { value: "all", label: "All" },
  { value: "TOP", label: "Top" },
  { value: "JUNGLE", label: "Jng" },
  { value: "MIDDLE", label: "Mid" },
  { value: "BOTTOM", label: "ADC" },
  { value: "UTILITY", label: "Sup" },
];

const RESULTS = [
  { value: "all", label: "All" },
  { value: "win", label: "W" },
  { value: "loss", label: "L" },
];

const SORTS = [
  { value: "newest", label: "Newest First" },
  { value: "oldest", label: "Oldest First" },
  { value: "cs_min", label: "CS/Min (High)" },
  { value: "dmg_min", label: "DMG/Min (High)" },
];

const ROLE_LABELS = {
  TOP: "Top", JUNGLE: "Jng", MIDDLE: "Mid", BOTTOM: "ADC", UTILITY: "Sup",
};

const champIcon = (name) => lookupName(name)?.image_url ?? null;

function timeAgo(epoch) {
  const diff = Math.floor(Date.now() / 1000) - epoch;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function kdaStr(m) {
  return `${m.kills}/${m.deaths}/${m.assists}`;
}

function kdaRatio(m) {
  return ((m.kills + m.assists) / Math.max(m.deaths, 1)).toFixed(2);
}

function buildPath() {
  const base = `/api/history/${props.region}/${encodeURIComponent(props.name)}/${encodeURIComponent(props.tag)}`;
  const params = new URLSearchParams();
  params.set("queue", props.queue);
  params.set("role", role.value);
  params.set("result", result.value);
  params.set("sort", sort.value);
  if (championFilter.value.trim()) params.set("champion", championFilter.value.trim());
  if (opponentFilter.value.trim()) params.set("opponent", opponentFilter.value.trim());
  return `${base}?${params}`;
}

async function loadMatches() {
  loading.value = true;
  matches.value = [];
  aggregate.value = null;
  expanded.value = null;
  try {
    const data = await apiGet(`${buildPath()}&count=20&start=0`);
    matches.value = data.matches;
    aggregate.value = data.aggregate;
    totalFetched.value = data.total_fetched;
  } catch {
    matches.value = [];
  } finally {
    loading.value = false;
  }
}

async function loadMore() {
  loadingMore.value = true;
  try {
    const data = await apiGet(`${buildPath()}&count=10&start=${matches.value.length}`);
    matches.value.push(...data.matches);
    totalFetched.value = data.total_fetched;
  } catch {
    // silently fail
  } finally {
    loadingMore.value = false;
  }
}

const canLoadMore = computed(() => matches.value.length < totalFetched.value);

function toggleExpand(matchId) {
  expanded.value = expanded.value === matchId ? null : matchId;
}

function team(participants, teamId) {
  return participants.filter((p) => p.team_id === teamId);
}

const winPct = computed(() => aggregate.value ? Math.round(aggregate.value.win_rate * 100) : 0);

// SVG ring parameters.
const RING_R = 36;
const RING_C = 2 * Math.PI * RING_R;
const ringOffset = computed(() => RING_C - (RING_C * winPct.value) / 100);

watch(() => [props.region, props.name, props.tag, props.queue], loadMatches, { immediate: true });
watch([role, result, sort, championFilter, opponentFilter], loadMatches);
</script>

<template>
  <div class="card history-card">
    <div class="card-head">
      <h3>Match history</h3>
    </div>

    <div class="history-filters">
      <div class="filter-group" role="group" aria-label="Filter by role">
        <button
          v-for="r in ROLES"
          :key="r.value"
          type="button"
          class="filter-btn"
          :class="{ active: role === r.value }"
          @click="role = r.value"
        >
          {{ r.label }}
        </button>
      </div>
      <div class="filter-group" role="group" aria-label="Filter by result">
        <button
          v-for="r in RESULTS"
          :key="r.value"
          type="button"
          class="filter-btn"
          :class="{ active: result === r.value }"
          @click="result = r.value"
        >
          {{ r.label }}
        </button>
      </div>
      <select v-model="sort" class="sort-select" aria-label="Sort order">
        <option v-for="s in SORTS" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>
      <button type="button" class="adv-toggle" @click="showAdvanced = !showAdvanced">
        {{ showAdvanced ? "Hide filters" : "Filters" }}
      </button>
    </div>

    <div v-if="showAdvanced" class="adv-filters">
      <div class="adv-field">
        <label class="adv-label">Champion</label>
        <input v-model.lazy="championFilter" class="adv-input" placeholder="e.g. Ahri" />
      </div>
      <div class="adv-field">
        <label class="adv-label">Opponent</label>
        <input v-model.lazy="opponentFilter" class="adv-input" placeholder="e.g. Zed" />
      </div>
      <button
        v-if="championFilter || opponentFilter"
        type="button"
        class="adv-reset"
        @click="championFilter = ''; opponentFilter = ''"
      >
        Reset
      </button>
    </div>

    <div v-if="aggregate && (aggregate.wins + aggregate.losses) > 0" class="agg-card">
      <div class="agg-ring-wrap">
        <svg class="agg-ring" viewBox="0 0 80 80">
          <circle cx="40" cy="40" :r="RING_R" class="agg-ring-bg" />
          <circle
            cx="40" cy="40" :r="RING_R" class="agg-ring-fill"
            :stroke-dasharray="RING_C" :stroke-dashoffset="ringOffset"
            :style="{ stroke: winPct >= 50 ? 'var(--good)' : 'var(--gold)' }"
          />
        </svg>
        <span class="agg-ring-pct" :style="{ color: winPct >= 50 ? 'var(--good)' : 'var(--gold)' }">{{ winPct }}%</span>
      </div>
      <div class="agg-wl">
        <span class="agg-record">{{ aggregate.wins }}W {{ aggregate.losses }}L</span>
        <span class="agg-games">{{ aggregate.wins + aggregate.losses }} games</span>
      </div>
      <div class="agg-kda">
        <span class="agg-kda-avg">{{ aggregate.avg_kills }} / <span class="agg-deaths">{{ aggregate.avg_deaths }}</span> / {{ aggregate.avg_assists }}</span>
        <span class="agg-kda-ratio">{{ aggregate.kda_ratio }} KDA</span>
      </div>
    </div>

    <p v-if="loading" class="pool-note">Loading match history…</p>
    <p v-else-if="!matches.length" class="pool-note">No matches found.</p>

    <div v-else class="history-list">
      <div
        v-for="m in matches"
        :key="m.match_id"
        class="history-row"
        :class="{ win: m.win, loss: !m.win }"
      >
        <button type="button" class="history-main" @click="toggleExpand(m.match_id)">
          <div class="h-result-bar" :class="m.win ? 'bar-win' : 'bar-loss'"></div>
          <img v-if="champIcon(m.champion)" class="h-icon" :src="champIcon(m.champion)" :alt="m.champion" />
          <div class="h-champ-col">
            <span class="h-champ">{{ m.champion }}</span>
            <span class="h-role">{{ ROLE_LABELS[m.role] || m.role }}</span>
          </div>
          <div class="h-vs" v-if="m.opponent_champion">
            <span class="h-vs-label">vs</span>
            <img v-if="champIcon(m.opponent_champion)" class="h-icon-sm" :src="champIcon(m.opponent_champion)" :alt="m.opponent_champion" />
            <span class="h-opponent">{{ m.opponent_champion }}</span>
          </div>
          <div class="h-kda-col">
            <span class="h-kda">{{ kdaStr(m) }}</span>
            <span class="h-kda-ratio">{{ kdaRatio(m) }} KDA</span>
          </div>
          <div class="h-stat">
            <span class="h-stat-val">{{ m.cs }}</span>
            <span class="h-stat-label">{{ m.cs_per_min }} CS/m</span>
          </div>
          <div class="h-stat">
            <span class="h-stat-val">{{ m.damage.toLocaleString() }}</span>
            <span class="h-stat-label">{{ Math.round(m.damage_per_min) }} DPM</span>
          </div>
          <div class="h-meta">
            <span class="h-duration">{{ m.duration_min }}m</span>
            <span class="h-ago">{{ timeAgo(m.game_start) }}</span>
          </div>
        </button>

        <div v-if="expanded === m.match_id" class="history-detail">
          <div class="teams-row">
            <div class="team-col team-blue">
              <div class="team-header">Blue Team</div>
              <div v-for="(p, i) in team(m.participants, 100)" :key="i" class="team-player-row">
                <img v-if="champIcon(p.champion)" class="h-icon-xs" :src="champIcon(p.champion)" :alt="p.champion" />
                <span class="tp-name">{{ p.champion }}</span>
                <span class="tp-kda">{{ p.kills }}/{{ p.deaths }}/{{ p.assists }}</span>
                <span class="tp-stat">{{ p.cs }} CS</span>
                <span class="tp-stat">{{ p.damage.toLocaleString() }} DMG</span>
              </div>
            </div>
            <div class="team-col team-red">
              <div class="team-header">Red Team</div>
              <div v-for="(p, i) in team(m.participants, 200)" :key="i" class="team-player-row">
                <img v-if="champIcon(p.champion)" class="h-icon-xs" :src="champIcon(p.champion)" :alt="p.champion" />
                <span class="tp-name">{{ p.champion }}</span>
                <span class="tp-kda">{{ p.kills }}/{{ p.deaths }}/{{ p.assists }}</span>
                <span class="tp-stat">{{ p.cs }} CS</span>
                <span class="tp-stat">{{ p.damage.toLocaleString() }} DMG</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <button
        v-if="canLoadMore"
        type="button"
        class="load-more-btn"
        :disabled="loadingMore"
        @click="loadMore"
      >
        {{ loadingMore ? "Loading…" : "Load more" }}
      </button>
    </div>
  </div>
</template>
