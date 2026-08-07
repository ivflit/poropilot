<script setup>
import { computed, onMounted, ref } from "vue";
import ReviewPanel from "./ReviewPanel.vue";
import MatchHistory from "./MatchHistory.vue";
import { useChampions } from "../composables/useChampions";

const QUEUES = [
  { value: "all", label: "All queues" },
  { value: "solo", label: "Ranked solo/duo" },
  { value: "flex", label: "Ranked flex" },
];

const props = defineProps({
  profile: { type: Object, default: null },
  pool: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  poolLoading: { type: Boolean, default: false },
  queue: { type: String, default: "all" },
  version: { type: String, default: null },
  aiEnabled: { type: Boolean, default: false },
});

const emit = defineEmits(["update:queue"]);

const { load, lookup } = useChampions();
onMounted(load);

const TIER_SHORT = {
  IRON: "I", BRONZE: "B", SILVER: "S", GOLD: "G", PLATINUM: "P", EMERALD: "E",
  DIAMOND: "D", MASTER: "M", GRANDMASTER: "GM", CHALLENGER: "C",
};
const RANK_NUM = { I: "1", II: "2", III: "3", IV: "4" };

// The rank badge follows the queue filter: asking for flex and being shown your
// solo rank would be its own kind of lie. "All" keeps solo as the headline rank.
const QUEUE_TYPES = { solo: "RANKED_SOLO_5x5", flex: "RANKED_FLEX_SR" };
const QUEUE_LABELS = { RANKED_SOLO_5x5: "Solo / Duo", RANKED_FLEX_SR: "Flex 5v5" };
const QUEUE_NAMES = { all: "all queues", solo: "ranked solo/duo", flex: "ranked flex" };

const rankedEntry = computed(() => {
  const entries = props.profile?.ranked ?? [];
  const wanted = QUEUE_TYPES[props.queue] ?? "RANKED_SOLO_5x5";
  const match = entries.find((e) => e.queueType === wanted);
  if (match) return match;
  // A filtered view shows nothing rather than another queue's rank; unfiltered
  // falls back to whatever ranked data exists.
  return props.queue === "all" ? (entries[0] ?? null) : null;
});

const queueName = computed(() => QUEUE_NAMES[props.queue] ?? props.queue);

const titleCase = (s) => (s ? s[0] + s.slice(1).toLowerCase() : s);

const rank = computed(() => {
  const e = rankedEntry.value;
  if (!e) return null;
  const games = (e.wins ?? 0) + (e.losses ?? 0);
  return {
    short: (TIER_SHORT[e.tier] ?? "?") + (RANK_NUM[e.rank] ?? ""),
    full: `${titleCase(e.tier)} ${e.rank} — ${e.leaguePoints} LP`,
    winPct: games ? Math.round((e.wins / games) * 100) : 0,
    wl: `${e.wins}W / ${e.losses}L`,
    queueLabel: QUEUE_LABELS[e.queueType] ?? "Ranked",
  };
});

const avatarUrl = computed(() =>
  props.version && props.profile?.profile_icon_id
    ? `https://ddragon.leagueoflegends.com/cdn/${props.version}/img/profileicon/${props.profile.profile_icon_id}.png`
    : null,
);

const championName = (id) => lookup(id)?.name ?? `Champion ${id}`;
const championIcon = (id) => lookup(id)?.image_url ?? null;
const pct = (wr) => Math.round(wr * 100);
const barColor = (p) => (p >= 50 ? "var(--good)" : "var(--gold)");

const riotName = computed(() => props.profile?.riot_id?.split("#")[0] ?? "");
const riotTag = computed(() => props.profile?.riot_id?.split("#")[1] ?? "");

const showAllChamps = ref(false);
const displayedChamps = computed(() => {
  if (!props.pool) return [];
  return showAllChamps.value ? props.pool.champions : props.pool.top;
});
const hasMoreChamps = computed(() =>
  props.pool && props.pool.champions.length > props.pool.top.length,
);
</script>

<template>
  <section class="profile">
    <div v-if="loading" class="card loading-card">Loading summoner…</div>

    <template v-else-if="profile">
      <div class="pcard">
        <div class="pcard-banner"></div>
        <div class="pcard-body">
          <div class="pcard-id">
            <img v-if="avatarUrl" class="avatar" :src="avatarUrl" :alt="profile.riot_id" />
            <div v-else class="avatar avatar-fallback">🐾</div>
            <div class="pcard-name">
              <h2>{{ profile.riot_id }}</h2>
              <div class="p-sub">{{ profile.region }} · Level {{ profile.level }}</div>
            </div>
          </div>

          <div v-if="rank" class="rank-row">
            <div class="rank-badge">{{ rank.short }}</div>
            <div class="rank-meta">
              <div class="rank-queue">{{ rank.queueLabel }}</div>
              <div class="rank-full">{{ rank.full }}</div>
            </div>
            <div class="rank-right">
              <div class="winpct" :style="{ color: rank.winPct >= 50 ? 'var(--good)' : 'var(--muted)' }">
                {{ rank.winPct }}%
              </div>
              <div class="wl">{{ rank.wl }}</div>
            </div>
          </div>
          <div v-else class="rank-row rank-unranked">Unranked in {{ queueName }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <h3>Recent form</h3>
          <div class="queue-seg" role="group" aria-label="Filter matches by queue">
            <button
              v-for="q in QUEUES"
              :key="q.value"
              type="button"
              class="queue-btn"
              :class="{ active: queue === q.value }"
              :aria-pressed="queue === q.value"
              @click="emit('update:queue', q.value)"
            >
              {{ q.label }}
            </button>
          </div>
        </div>

        <Transition name="form-swap" mode="out-in">
          <p v-if="poolLoading" key="loading" class="pool-note">Loading recent games…</p>
          <p v-else-if="!pool" key="unavailable" class="pool-note">Recent form is unavailable right now.</p>
          <p v-else-if="!pool.top.length" key="empty" class="pool-note">
            No games in {{ queueName }} — try another filter.
          </p>

          <div v-else key="list">
            <ul class="pool">
              <li v-for="c in displayedChamps" :key="c.champion_id" class="f-row">
                <img class="f-icon" :src="championIcon(c.champion_id)" :alt="c.champion_name" />
                <div class="f-main">
                  <div class="f-top">
                    <span class="f-name">{{ c.champion_name }}</span>
                    <span class="f-wg">{{ c.games }}g · {{ c.avg_kda.toFixed(1) }} KDA</span>
                  </div>
                  <div class="bar">
                    <div
                      class="bar-fill"
                      :style="{ width: pct(c.win_rate) + '%', background: barColor(pct(c.win_rate)) }"
                    ></div>
                  </div>
                </div>
                <div class="f-pct" :style="{ color: barColor(pct(c.win_rate)) }">{{ pct(c.win_rate) }}%</div>
              </li>
            </ul>
            <button
              v-if="hasMoreChamps"
              type="button"
              class="show-all-btn"
              @click="showAllChamps = !showAllChamps"
            >
              {{ showAllChamps ? "Show top 5" : `Show all ${pool.champions.length}` }}
            </button>
          </div>
        </Transition>
      </div>

      <ReviewPanel
        v-if="aiEnabled && riotName"
        :region="profile.region"
        :name="riotName"
        :tag="riotTag"
        :queue="queue"
      />

      <MatchHistory
        v-if="riotName"
        :region="profile.region"
        :name="riotName"
        :tag="riotTag"
        :queue="queue"
      />

      <div class="card">
        <div class="card-head">
          <h3>Champion mastery</h3>
          <span class="card-sub">All time · Top {{ profile.top_masteries.length }}</span>
        </div>
        <div class="rows">
          <div v-for="m in profile.top_masteries" :key="m.champion_id" class="m-row">
            <img class="m-icon" :src="championIcon(m.champion_id)" :alt="championName(m.champion_id)" />
            <div class="m-main">
              <div class="m-name">{{ championName(m.champion_id) }}</div>
              <div class="m-pts">{{ m.points.toLocaleString() }} pts</div>
            </div>
            <div class="m-badge">🔷 M{{ m.level }}</div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>
