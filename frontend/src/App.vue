<script setup>
import SummonerSearch from "./components/SummonerSearch.vue";
import DraftAssistant from "./components/DraftAssistant.vue";
</script>

<template>
  <main>
    <h1>PoroPilot 🐾</h1>
    <p class="tagline">Your League of Legends companion — profile, champ pool &amp; AI draft help.</p>
    <SummonerSearch />
    <DraftAssistant />
  </main>
</template>

<style>
:root {
  font-family: system-ui, sans-serif;
  color: #1c2430;
}
main {
  max-width: 640px;
  margin: 3rem auto;
  padding: 0 1rem;
}
h1 {
  color: #1f4e79;
}
.tagline {
  color: #5b6674;
}
</style>
