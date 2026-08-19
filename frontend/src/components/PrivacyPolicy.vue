<script setup>
defineEmits(["close"]);
</script>

<template>
  <div class="privacy-overlay" @click.self="$emit('close')">
    <div class="privacy-modal">
      <button class="close-btn" type="button" @click="$emit('close')">&times;</button>
      <h2>Privacy Policy</h2>
      <p class="updated">Last updated: August 2026</p>

      <h3>What we collect</h3>
      <p>
        If you create an account, we store your <strong>email address</strong>,
        a <strong>hashed password</strong> (we never store your plain password),
        and optionally your <strong>linked Riot ID</strong> and
        <strong>saved champion pools</strong>.
      </p>

      <h3>Cookies</h3>
      <p>
        We use a single <strong>HTTP-only secure cookie</strong> to keep you
        logged in (a refresh token). We do not use tracking cookies, analytics,
        or any third-party cookies.
      </p>

      <h3>How we use your data</h3>
      <p>
        Your data is used solely to provide PoroPilot's features: logging you
        in, loading your profile automatically, and saving your champion pool
        presets. We do not sell, share, or monetise your data in any way.
      </p>

      <h3>Third-party services</h3>
      <p>
        We send requests to the <strong>Riot Games API</strong> and
        <strong>Anthropic Claude API</strong> on your behalf to fetch game data
        and power AI features. No personal data from your account is sent to
        these services — only Riot IDs and champion data needed for lookups.
      </p>

      <h3>Data retention</h3>
      <p>
        Your account data is kept for as long as your account exists. You can
        delete your account at any time, which removes all associated data.
      </p>

      <h3>Contact</h3>
      <p>
        Questions? Open an issue on the
        <a href="https://github.com/ivflit/poropilot" target="_blank" rel="noopener">
          GitHub repository</a>.
      </p>
    </div>
  </div>
</template>

<style scoped>
.privacy-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.privacy-modal {
  background: var(--card-bg, #1e2328);
  color: var(--text, #a09b8c);
  border: 1px solid var(--border, #3c3c41);
  border-radius: 12px;
  padding: 2rem;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 0.75rem;
  right: 1rem;
  background: none;
  border: none;
  color: var(--text, #a09b8c);
  font-size: 1.5rem;
  cursor: pointer;
}

h2 {
  color: var(--heading, #c89b3c);
  margin-top: 0;
}

h3 {
  color: var(--heading, #c89b3c);
  margin-top: 1.25rem;
  margin-bottom: 0.25rem;
}

p {
  line-height: 1.5;
  margin-top: 0.25rem;
}

.updated {
  font-size: 0.85rem;
  opacity: 0.7;
}

a {
  color: var(--link, #c89b3c);
}
</style>
