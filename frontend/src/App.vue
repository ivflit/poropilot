<script setup>
import { onMounted } from "vue";
import SummonerSearch from "./components/SummonerSearch.vue";
import DraftAssistant from "./components/DraftAssistant.vue";
import { useConfig } from "./composables/useConfig";

const { aiEnabled, load } = useConfig();
onMounted(load);
</script>

<template>
  <main>
    <h1>PoroPilot 🐾</h1>
    <p class="tagline">Your League of Legends companion — profile, champ pool &amp; AI draft help.</p>
    <SummonerSearch />
    <DraftAssistant v-if="aiEnabled" />
  </main>
</template>
