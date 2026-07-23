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
