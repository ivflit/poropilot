<script setup>
import { useSummoner } from "../composables/useSummoner";

const { region, riotId, profile, error, loading, onInput } = useSummoner();
</script>

<template>
  <div class="search">
    <div class="row">
      <select v-model="region" aria-label="Region">
        <option>EUW</option>
        <option>EUNE</option>
        <option>NA</option>
        <option>KR</option>
        <option>BR</option>
        <option>JP</option>
        <option>OCE</option>
        <option>TR</option>
        <option>RU</option>
        <option>LAN</option>
        <option>LAS</option>
      </select>
      <input
        v-model="riotId"
        @input="onInput"
        placeholder="name#tag"
        aria-label="Riot ID"
      />
    </div>

    <p v-if="loading" class="muted">Loading…</p>
    <p v-if="error" class="error" role="alert">{{ error }}</p>

    <section v-if="profile" class="profile">
      <h2>{{ profile.riot_id }}</h2>
      <p>Region {{ profile.region }} · Level {{ profile.level }}</p>
      <h3>Top champions</h3>
      <ul>
        <li v-for="m in profile.top_masteries" :key="m.champion_id">
          Champion {{ m.champion_id }} — {{ m.points.toLocaleString() }} pts (M{{ m.level }})
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.row {
  display: flex;
  gap: 0.5rem;
}
select,
input {
  padding: 0.5rem;
  font-size: 1rem;
  border: 1px solid #d9e0e8;
  border-radius: 6px;
}
input {
  flex: 1;
}
.muted {
  color: #5b6674;
}
.error {
  color: #b00020;
}
.profile {
  margin-top: 1.5rem;
}
</style>
