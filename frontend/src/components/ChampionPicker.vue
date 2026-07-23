<script setup>
import { computed, onMounted, ref } from "vue";
import { useChampions } from "../composables/useChampions";

// A small reusable control: pick champions from a dropdown into a removable
// chip list. Two-way bound via v-model (an array of champion names).
const props = defineProps({
  modelValue: { type: Array, required: true },
  label: { type: String, required: true },
});
const emit = defineEmits(["update:modelValue"]);

const { champions, load } = useChampions();
onMounted(load);

const names = computed(() =>
  Object.values(champions.value)
    .map((c) => c.name)
    .sort(),
);

const selected = ref("");

function add() {
  const name = selected.value;
  if (name && !props.modelValue.includes(name)) {
    emit("update:modelValue", [...props.modelValue, name]);
  }
  selected.value = "";
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
    <div class="row">
      <select v-model="selected" :aria-label="label">
        <option value="">Select a champion…</option>
        <option v-for="n in names" :key="n" :value="n">{{ n }}</option>
      </select>
      <button type="button" :disabled="!selected" @click="add">Add</button>
    </div>
    <ul v-if="modelValue.length" class="chips">
      <li v-for="n in modelValue" :key="n" class="chip">
        {{ n }}
        <button type="button" :aria-label="`Remove ${n}`" @click="remove(n)">×</button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.picker {
  margin-bottom: 0.75rem;
}
.picker-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.25rem;
}
.row {
  display: flex;
  gap: 0.5rem;
}
select,
button {
  padding: 0.4rem;
  font-size: 0.95rem;
  border: 1px solid #d9e0e8;
  border-radius: 6px;
}
.chips {
  list-style: none;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.5rem;
}
.chip {
  background: #eef3f8;
  border-radius: 999px;
  padding: 0.1rem 0.6rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.chip button {
  border: none;
  background: none;
  cursor: pointer;
  padding: 0;
  color: #5b6674;
}
</style>
