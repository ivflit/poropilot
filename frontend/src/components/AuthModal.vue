<script setup>
import { ref } from "vue";
import { useSession } from "../composables/useSession";

const emit = defineEmits(["close"]);

const { signup, login } = useSession();

const mode = ref("login"); // "login" | "signup"
const email = ref("");
const password = ref("");
const error = ref("");
const submitting = ref(false);

async function submit() {
  error.value = "";
  submitting.value = true;
  try {
    if (mode.value === "signup") {
      await signup(email.value, password.value);
    } else {
      await login(email.value, password.value);
    }
    emit("close");
  } catch (e) {
    error.value = e.message;
  } finally {
    submitting.value = false;
  }
}

function switchMode() {
  mode.value = mode.value === "login" ? "signup" : "login";
  error.value = "";
}
</script>

<template>
  <div class="auth-backdrop" @click.self="emit('close')">
    <div class="auth-modal card" role="dialog" aria-label="Sign in">
      <h2>{{ mode === "login" ? "Log in" : "Sign up" }}</h2>

      <form class="auth-form" @submit.prevent="submit">
        <input
          v-model="email"
          type="email"
          placeholder="Email"
          aria-label="Email"
          required
          autocomplete="email"
        />
        <input
          v-model="password"
          type="password"
          placeholder="Password"
          aria-label="Password"
          required
          autocomplete="current-password"
          minlength="6"
        />

        <p v-if="error" class="auth-error" role="alert">{{ error }}</p>

        <button class="auth-submit" type="submit" :disabled="submitting">
          {{ submitting ? "..." : mode === "login" ? "Log in" : "Sign up" }}
        </button>
      </form>

      <p class="auth-switch">
        {{ mode === "login" ? "No account?" : "Already have an account?" }}
        <button type="button" class="auth-switch-btn" @click="switchMode">
          {{ mode === "login" ? "Sign up" : "Log in" }}
        </button>
      </p>
    </div>
  </div>
</template>
