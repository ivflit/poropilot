<script setup>
import { computed, onMounted, ref, watch } from "vue";
import ProfileColumn from "./components/ProfileColumn.vue";
import DraftAssistant from "./components/DraftAssistant.vue";
import MultiSearch from "./components/MultiSearch.vue";
import TierList from "./components/TierList.vue";
import AuthModal from "./components/AuthModal.vue";
import PrivacyPolicy from "./components/PrivacyPolicy.vue";
import { useSummoner } from "./composables/useSummoner";
import { useConfig } from "./composables/useConfig";
import { useTheme } from "./composables/useTheme";
import { useSession } from "./composables/useSession";

const { region, riotId, queue, profile, pool, error, loading, poolLoading, onInput, search } =
  useSummoner();
const { aiEnabled, authEnabled, ddragonVersion, load } = useConfig();
const { theme, toggle } = useTheme();
const { user, isLoggedIn, logout, restore } = useSession();

const showAuth = ref(false);
const showPrivacy = ref(false);

// Champion names from the analysed pool, for seeding the draft assistant.
const poolChampionNames = computed(() =>
  pool.value?.top?.map((c) => c.champion_name) ?? [],
);

const REGIONS = ["EUW", "EUNE", "NA", "KR", "BR", "JP", "OCE", "TR", "RU", "LAN", "LAS"];

// When the user logs in and has a linked Riot ID, open their profile automatically.
watch(user, (u) => {
  if (u?.riot_name && u?.riot_tag && u?.riot_region) {
    region.value = u.riot_region;
    riotId.value = `${u.riot_name}#${u.riot_tag}`;
    search();
  }
});

onMounted(async () => {
  await load();
  if (authEnabled.value) await restore();
});
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
        <div class="header-actions">
          <template v-if="authEnabled">
            <div v-if="isLoggedIn" class="user-pill">
              <span class="user-email">{{ user.email }}</span>
              <button class="logout-btn" type="button" @click="logout">Log out</button>
            </div>
            <button v-else class="login-btn" type="button" @click="showAuth = true">Log in</button>
          </template>
          <button class="theme-toggle" type="button" aria-label="Toggle theme" @click="toggle">
            <span>{{ theme === "dark" ? "☀️" : "🌙" }}</span>{{ theme === "dark" ? "Light" : "Dark" }}
          </button>
        </div>
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
            :ai-enabled="aiEnabled"
          />
        </Transition>
        <div class="right-col">
          <DraftAssistant v-if="aiEnabled" :pool-champions="poolChampionNames" />
          <MultiSearch :version="ddragonVersion" />
          <TierList v-if="aiEnabled" />
        </div>
      </div>

      <footer class="site-footer">
        <div>
          PoroPilot isn't endorsed by Riot Games and doesn't reflect the views of Riot Games or
          anyone officially involved in producing League of Legends.
        </div>
        <div>
          Champion art © Riot Games · Data via Data Dragon.
          · <a href="#" class="footer-link" @click.prevent="showPrivacy = true">Privacy Policy</a>
        </div>
      </footer>
    </div>

    <AuthModal v-if="showAuth" @close="showAuth = false" />
    <PrivacyPolicy v-if="showPrivacy" @close="showPrivacy = false" />
  </div>
</template>
