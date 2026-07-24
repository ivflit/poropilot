<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useChampions } from "../composables/useChampions";

// Search-as-you-type champion picker: filter by name, pick from icon results,
// selections become removable chips. Two-way bound via v-model (array of names).
const props = defineProps({
  modelValue: { type: Array, required: true },
  label: { type: String, required: true },
});
const emit = defineEmits(["update:modelValue"]);

const { champions, load } = useChampions();
onMounted(load);

const query = ref("");
const activeIndex = ref(0);

const allChampions = computed(() =>
  Object.values(champions.value).sort((a, b) => a.name.localeCompare(b.name)),
);

const matches = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return [];
  return allChampions.value
    .filter((c) => c.name.toLowerCase().includes(q) && !props.modelValue.includes(c.name))
    .slice(0, 8);
});

// Reset the keyboard highlight to the top whenever the results change.
watch(query, () => {
  activeIndex.value = 0;
});

function iconFor(name) {
  return allChampions.value.find((c) => c.name === name)?.image_url ?? null;
}

function add(name) {
  if (name && !props.modelValue.includes(name)) {
    emit("update:modelValue", [...props.modelValue, name]);
  }
  query.value = "";
}

function move(delta) {
  if (!matches.value.length) return;
  const n = matches.value.length;
  activeIndex.value = (activeIndex.value + delta + n) % n; // wraps around
}

function select() {
  const c = matches.value[activeIndex.value];
  if (c) add(c.name);
}

function remove(name) {
  emit(
    "update:modelValue",
    props.modelValue.filter((n) => n !== name),
  );
}
</script>

<template>
  <div class="picker">
    <label class="picker-label">{{ label }}</label>

    <div class="search-box">
      <input
        v-model="query"
        :aria-label="label"
        type="text"
        placeholder="Search a champion…"
        autocomplete="off"
        @keydown.down.prevent="move(1)"
        @keydown.up.prevent="move(-1)"
        @keydown.enter.prevent="select"
      />
      <ul v-if="matches.length" class="results">
        <li
          v-for="(c, i) in matches"
          :key="c.champion_id"
          :class="{ active: i === activeIndex }"
        >
          <button type="button" @click="add(c.name)" @mouseenter="activeIndex = i">
            <img :src="c.image_url" alt="" width="28" height="28" />
            <span>{{ c.name }}</span>
          </button>
        </li>
      </ul>
    </div>

    <ul v-if="modelValue.length" class="chips">
      <li v-for="n in modelValue" :key="n" class="chip">
        <img v-if="iconFor(n)" :src="iconFor(n)" alt="" width="20" height="20" />
        {{ n }}
        <button type="button" :aria-label="`Remove ${n}`" @click="remove(n)">×</button>
      </li>
    </ul>
  </div>
</template>
