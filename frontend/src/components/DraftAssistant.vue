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
