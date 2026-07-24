<script setup>
import { computed, onMounted } from "vue";
import { useChampions } from "../composables/useChampions";

const props = defineProps({
  profile: { type: Object, default: null },
  pool: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  version: { type: String, default: null },
});

const { load, lookup } = useChampions();
onMounted(load);

const TIER_SHORT = {
  IRON: "I", BRONZE: "B", SILVER: "S", GOLD: "G", PLATINUM: "P", EMERALD: "E",
  DIAMOND: "D", MASTER: "M", GRANDMASTER: "GM", CHALLENGER: "C",
};
const RANK_NUM = { I: "1", II: "2", III: "3", IV: "4" };

const soloRank = computed(() => {
  const entries = props.profile?.ranked ?? [];
  return entries.find((e) => e.queueType === "RANKED_SOLO_5x5") ?? entries[0] ?? null;
});

const titleCase = (s) => (s ? s[0] + s.slice(1).toLowerCase() : s);

const rank = computed(() => {
  const e = soloRank.value;
  if (!e) return null;
  const games = (e.wins ?? 0) + (e.losses ?? 0);
  return {
    short: (TIER_SHORT[e.tier] ?? "?") + (RANK_NUM[e.rank] ?? ""),
    full: `${titleCase(e.tier)} ${e.rank} — ${e.leaguePoints} LP`,
    winPct: games ? Math.round((e.wins / games) * 100) : 0,
    wl: `${e.wins}W / ${e.losses}L`,
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
              <div class="rank-queue">Solo / Duo</div>
              <div class="rank-full">{{ rank.full }}</div>
            </div>
            <div class="rank-right">
              <div class="winpct" :style="{ color: rank.winPct >= 50 ? 'var(--good)' : 'var(--muted)' }">
                {{ rank.winPct }}%
              </div>
              <div class="wl">{{ rank.wl }}</div>
            </div>
          </div>
          <div v-else class="rank-row rank-unranked">Unranked</div>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <h3>Champion mastery</h3>
          <span class="card-sub">Top {{ profile.top_masteries.length }}</span>
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

      <div v-if="pool && pool.top.length" class="card">
        <h3 class="mb">Recent form</h3>
        <ul class="pool">
          <li v-for="c in pool.top" :key="c.champion_id" class="f-row">
            <img class="f-icon" :src="championIcon(c.champion_id)" :alt="c.champion_name" />
            <div class="f-main">
              <div class="f-top">
                <span class="f-name">{{ c.champion_name }}</span>
                <span class="f-wg">{{ c.wins }}W · {{ c.games }}g</span>
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
      </div>
    </template>
  </section>
</template>
