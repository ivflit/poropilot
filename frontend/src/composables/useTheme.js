import { ref } from "vue";

// Light/dark theme, persisted in localStorage. The initial value is set before
// first paint by a small script in index.html; here we just read and toggle it.
const KEY = "poropilot-theme";

export function useTheme() {
  const theme = ref(document.documentElement.getAttribute("data-theme") || "light");

  function toggle() {
    theme.value = theme.value === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", theme.value);
    localStorage.setItem(KEY, theme.value);
  }

  return { theme, toggle };
}
