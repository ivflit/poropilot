<script setup>
import { onMounted } from "vue";
import { useSummoner } from "../composables/useSummoner";
import { useChampions } from "../composables/useChampions";

const { region, riotId, profile, error, loading, onInput } = useSummoner();
const { load: loadChampions, lookup } = useChampions();

onMounted(loadChampions);

const QUEUE_LABELS = {
  RANKED_SOLO_5x5: "Solo/Duo",
  RANKED_FLEX_SR: "Flex",
};
const queueLabel = (queueType) => QUEUE_LABELS[queueType] ?? queueType;
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

      <h3>Ranked</h3>
      <ul v-if="profile.ranked.length" class="ranked">
        <li v-for="r in profile.ranked" :key="r.queueType">
          {{ queueLabel(r.queueType) }}: {{ r.tier }} {{ r.rank }} —
          {{ r.leaguePoints }} LP ({{ r.wins }}W / {{ r.losses }}L)
        </li>
      </ul>
      <p v-else class="muted">Unranked</p>

      <h3>Top champions</h3>
      <ul class="champs">
        <li v-for="m in profile.top_masteries" :key="m.champion_id" class="champ">
          <img
            v-if="lookup(m.champion_id)"
            :src="lookup(m.champion_id).image_url"
            :alt="lookup(m.champion_id).name"
            width="32"
            height="32"
          />
          <span class="name">{{ lookup(m.champion_id)?.name ?? `Champion ${m.champion_id}` }}</span>
          <span class="pts">{{ m.points.toLocaleString() }} pts · M{{ m.level }}</span>
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
.ranked {
  list-style: none;
  padding: 0;
}
.champs {
  list-style: none;
  padding: 0;
}
.champ {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
}
.champ img {
  border-radius: 4px;
}
.champ .name {
  font-weight: 600;
}
.champ .pts {
  color: #5b6674;
  margin-left: auto;
}
</style>
