<script setup>
import { onMounted } from "vue";
import ProfileColumn from "./components/ProfileColumn.vue";
import DraftAssistant from "./components/DraftAssistant.vue";
import { useSummoner } from "./composables/useSummoner";
import { useConfig } from "./composables/useConfig";
import { useTheme } from "./composables/useTheme";

const { region, riotId, queue, profile, pool, error, loading, poolLoading, onInput, search } =
  useSummoner();
const { aiEnabled, ddragonVersion, load } = useConfig();
const { theme, toggle } = useTheme();

const REGIONS = ["EUW", "EUNE", "NA", "KR", "BR", "JP", "OCE", "TR", "RU", "LAN", "LAS"];

// Ranked solo and flex are different games — blending them (and ARAM) makes the
// win-rates meaningless, so the stats below can be narrowed to one queue.
const QUEUES = [
  { value: "all", label: "All queues" },
  { value: "solo", label: "Ranked solo/duo" },
  { value: "flex", label: "Ranked flex" },
];

onMounted(load);
</script>

<template>
  <div class="page">
    <div class="container">
      <header class="app-header">
        <div class="brand">
          <div class="brand-icon">🐾</div>
          <div>
            <h1>PoroPilot</h1>
            <p class="tagline">Your League companion — profile, champ pool &amp; AI draft help.</p>
          </div>
        </div>
        <button class="theme-toggle" type="button" aria-label="Toggle theme" @click="toggle">
          <span>{{ theme === "dark" ? "☀️" : "🌙" }}</span>{{ theme === "dark" ? "Light" : "Dark" }}
        </button>
      </header>

      <div class="search-bar">
        <div class="region-wrap">
          <select v-model="region" aria-label="Region">
            <option v-for="r in REGIONS" :key="r">{{ r }}</option>
          </select>
          <span class="chev">▾</span>
        </div>
        <input
          v-model="riotId"
          aria-label="Riot ID"
          placeholder="name#tag"
          @input="onInput"
          @keyup.enter="search"
        />
        <button class="search-btn" type="button" @click="search">Search</button>
        <p v-if="error" class="search-error" role="alert"><span>⚠</span>{{ error }}</p>
      </div>

      <div v-if="profile" class="queue-seg" role="group" aria-label="Filter matches by queue">
        <button
          v-for="q in QUEUES"
          :key="q.value"
          type="button"
          class="queue-btn"
          :class="{ active: queue === q.value }"
          :aria-pressed="queue === q.value"
          @click="queue = q.value"
        >
          {{ q.label }}
        </button>
      </div>

      <div class="columns">
        <Transition name="col">
          <ProfileColumn
            v-if="loading || profile"
            :profile="profile"
            :pool="pool"
            :loading="loading"
            :pool-loading="poolLoading"
            :queue="queue"
            :version="ddragonVersion"
          />
        </Transition>
        <DraftAssistant v-if="aiEnabled" />
      </div>

      <footer class="site-footer">
        <div>
          PoroPilot isn't endorsed by Riot Games and doesn't reflect the views of Riot Games or
          anyone officially involved in producing League of Legends.
        </div>
        <div>Champion art © Riot Games · Data via Data Dragon.</div>
      </footer>
    </div>
  </div>
</template>
