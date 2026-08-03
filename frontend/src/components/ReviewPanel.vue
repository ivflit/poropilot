<script setup>
import { ref, watch } from "vue";
import { apiGet } from "../services/api";
import { useChampions } from "../composables/useChampions";

const props = defineProps({
  region: { type: String, required: true },
  name: { type: String, required: true },
  tag: { type: String, required: true },
  queue: { type: String, default: "solo" },
});

const { lookupName } = useChampions();

const matches = ref([]);
const matchesLoading = ref(false);
const selectedMatch = ref(null);
const review = ref(null);
const reviewLoading = ref(false);
const reviewError = ref("");

const champIcon = (name) => lookupName(name)?.image_url ?? null;

async function loadMatches() {
  matchesLoading.value = true;
  matches.value = [];
  selectedMatch.value = null;
  review.value = null;
  try {
    const q = props.queue === "all" ? "solo" : props.queue;
    matches.value = await apiGet(
      `/api/matches/${props.region}/${encodeURIComponent(props.name)}/${encodeURIComponent(props.tag)}?queue=${q}`,
    );
  } catch {
    matches.value = [];
  } finally {
    matchesLoading.value = false;
  }
}

async function selectMatch(m) {
  if (selectedMatch.value === m.match_id) {
    selectedMatch.value = null;
    review.value = null;
    return;
  }
  selectedMatch.value = m.match_id;
  review.value = null;
  reviewError.value = "";
  reviewLoading.value = true;
  try {
    review.value = await apiGet(
      `/api/review/${props.region}/${encodeURIComponent(props.name)}/${encodeURIComponent(props.tag)}/${m.match_id}`,
    );
  } catch (e) {
    reviewError.value = e.message;
  } finally {
    reviewLoading.value = false;
  }
}

watch(() => [props.region, props.name, props.tag, props.queue], loadMatches, { immediate: true });
</script>

<template>
  <div class="card review-card">
    <div class="card-head">
      <h3>Post-game review</h3>
      <span class="card-sub">AI coaching</span>
    </div>

    <p v-if="matchesLoading" class="pool-note">Loading recent games…</p>
    <p v-else-if="!matches.length" class="pool-note">No ranked games to review.</p>

    <div v-else class="match-list">
      <button
        v-for="m in matches"
        :key="m.match_id"
        type="button"
        class="match-row"
        :class="{ selected: selectedMatch === m.match_id, win: m.win, loss: !m.win }"
        @click="selectMatch(m)"
      >
        <img v-if="champIcon(m.champion)" class="match-icon" :src="champIcon(m.champion)" :alt="m.champion" />
        <div class="match-info">
          <span class="match-champ">{{ m.champion }}</span>
          <span class="match-kda">{{ m.kills }}/{{ m.deaths }}/{{ m.assists }}</span>
        </div>
        <span class="match-result">{{ m.win ? "Win" : "Loss" }}</span>
      </button>
    </div>

    <div v-if="reviewLoading" class="review-body">
      <p class="pool-note">Reviewing this game…</p>
    </div>

    <div v-else-if="reviewError" class="review-body">
      <p class="review-error">{{ reviewError }}</p>
    </div>

    <div v-else-if="review" class="review-body">
      <div class="review-verdict" :class="review.win ? 'verdict-win' : 'verdict-loss'">
        {{ review.verdict }}
      </div>

      <div class="review-section">
        <div class="section-label">What went wrong</div>
        <ul class="review-issues">
          <li v-for="(issue, i) in review.issues" :key="i" class="review-issue">
            <span class="issue-point">{{ issue.point }}</span>
            <span class="issue-stat">{{ issue.stat }}</span>
          </li>
        </ul>
      </div>

      <div class="review-section">
        <div class="section-label">Next game</div>
        <ul class="review-tips">
          <li v-for="(tip, i) in review.tips" :key="i">{{ tip }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>
