<script setup>
import ChampionPicker from "./ChampionPicker.vue";
import { useDraft } from "../composables/useDraft";

const { role, championPool, allyPicks, enemyBans, suggestions, loading, error, submit } =
  useDraft();

const ROLES = ["TOP", "JUNGLE", "MID", "BOT", "SUPPORT"];
</script>

<template>
  <section class="draft">
    <h2>Draft assistant</h2>

    <label class="role">
      Role
      <select v-model="role" aria-label="Role">
        <option v-for="r in ROLES" :key="r">{{ r }}</option>
      </select>
    </label>

    <ChampionPicker v-model="championPool" label="Your champion pool" />
    <ChampionPicker v-model="allyPicks" label="Allied picks" />
    <ChampionPicker v-model="enemyBans" label="Enemy bans" />

    <button type="button" class="go" :disabled="loading" @click="submit">
      {{ loading ? "Thinking…" : "Suggest a pick" }}
    </button>

    <p v-if="error" class="error" role="alert">{{ error }}</p>

    <ol v-if="suggestions" class="suggestions">
      <li v-for="s in suggestions" :key="s.champion">
        <strong>{{ s.champion }}</strong>
        <span class="conf">({{ s.confidence }} confidence)</span>
        <p>{{ s.reason }}</p>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.draft {
  margin-top: 2.5rem;
  border-top: 1px solid #d9e0e8;
  padding-top: 1.5rem;
}
.role {
  display: block;
  font-weight: 600;
  margin-bottom: 0.75rem;
}
.role select {
  margin-left: 0.5rem;
  padding: 0.4rem;
  border: 1px solid #d9e0e8;
  border-radius: 6px;
}
.go {
  margin-top: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  color: #fff;
  background: #1f4e79;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.go:disabled {
  opacity: 0.6;
  cursor: default;
}
.error {
  color: #b00020;
}
.suggestions {
  margin-top: 1rem;
  padding-left: 1.2rem;
}
.suggestions li {
  margin-bottom: 0.75rem;
}
.conf {
  color: #5b6674;
  margin-left: 0.4rem;
  font-size: 0.9rem;
}
</style>
