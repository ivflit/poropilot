<script setup>
import { ref, watch } from "vue";
import { apiGet } from "../services/api";
import { useChampions } from "../composables/useChampions";

const { lookupName } = useChampions();

const role = ref("MID");
const data = ref(null);
const loading = ref(false);
const error = ref("");

const ROLES = [
  { value: "TOP", label: "Top" },
  { value: "JUNGLE", label: "Jungle" },
  { value: "MID", label: "Mid" },
  { value: "ADC", label: "ADC" },
  { value: "SUPPORT", label: "Support" },
];

const TIER_COLORS = { S: "var(--error)", A: "var(--good)", B: "var(--accent)", C: "var(--muted)" };

const champIcon = (name) => lookupName(name)?.image_url ?? null;

async function loadTierList() {
  loading.value = true;
  error.value = "";
  data.value = null;
  try {
    data.value = await apiGet(`/api/tier-list?role=${role.value}`);
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

watch(role, loadTierList, { immediate: true });
</script>

<template>
  <div class="card tier-card">
    <div class="card-head">
      <h3>Tier list</h3>
      <span class="card-sub">AI-generated</span>
    </div>

    <div class="tier-roles" role="group" aria-label="Select role">
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

    <p v-if="loading" class="pool-note">Generating tier list…</p>
    <p v-else-if="error" class="pool-note tier-error">{{ error }}</p>

    <div v-else-if="data" class="tier-list">
      <div v-for="t in data.tiers" :key="t.tier" class="tier-row">
        <div class="tier-badge" :style="{ background: TIER_COLORS[t.tier] || 'var(--muted)' }">
          {{ t.tier }}
        </div>
        <div class="tier-champs">
          <div v-for="c in t.champions" :key="c.name" class="tier-champ">
            <img v-if="champIcon(c.name)" class="tier-icon" :src="champIcon(c.name)" :alt="c.name" />
            <div class="tier-champ-info">
              <span class="tier-champ-name">{{ c.name }}</span>
              <span class="tier-reason">{{ c.reason }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
