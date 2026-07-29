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

      <div class="columns">
        <Transition name="col">
          <ProfileColumn
            v-if="loading || profile"
            :profile="profile"
            :pool="pool"
            :loading="loading"
            :pool-loading="poolLoading"
            v-model:queue="queue"
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
