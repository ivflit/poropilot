<script setup>
import { onMounted } from "vue";
import SummonerSearch from "./components/SummonerSearch.vue";
import DraftAssistant from "./components/DraftAssistant.vue";
import { useConfig } from "./composables/useConfig";
import { useTheme } from "./composables/useTheme";

const { aiEnabled, load } = useConfig();
const { theme, toggle } = useTheme();

onMounted(load);
</script>

<template>
  <main>
    <header class="app-header">
      <div>
        <h1>PoroPilot 🐾</h1>
        <p class="tagline">
          Your League of Legends companion — profile, champ pool &amp; AI draft help.
        </p>
      </div>
      <button class="theme-toggle" type="button" aria-label="Toggle theme" @click="toggle">
        {{ theme === "dark" ? "☀️" : "🌙" }}
      </button>
    </header>

    <SummonerSearch />
    <DraftAssistant v-if="aiEnabled" />
  </main>
</template>
