import { test, expect } from "@playwright/test";

const CONFIG = { ai_enabled: true, auth_enabled: true, ddragon_version: "14.1.1" };
const TOKEN = { access_token: "test-token", token_type: "bearer" };
const USER = { id: 1, email: "test@example.com", riot_region: null, riot_name: null, riot_tag: null };

const CHAMPIONS = {
  266: { champion_id: 266, name: "Aatrox", title: "the Darkin Blade", image_url: "http://x/Aatrox.png" },
  238: { champion_id: 238, name: "Zed", title: "the Master of Shadows", image_url: "http://x/Zed.png" },
  103: { champion_id: 103, name: "Ahri", title: "the Nine-Tailed Fox", image_url: "http://x/Ahri.png" },
};

// Mutable pool store so we can verify save/load roundtrips.
let savedPools = {};

test.beforeEach(async ({ page }) => {
  savedPools = {};

  await page.route("**/api/config", (route) => route.fulfill({ json: CONFIG }));
  await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
  await page.route("**/api/auth/refresh", (route) =>
    route.fulfill({ json: TOKEN }),
  );
  await page.route("**/api/auth/me", (route) => route.fulfill({ json: USER }));

  // Saved pools CRUD mock.
  await page.route("**/api/me/pools", (route) => {
    if (route.request().method() === "GET") {
      const list = Object.entries(savedPools).map(([role, champions]) => ({ role, champions }));
      return route.fulfill({ json: list });
    }
  });
  await page.route("**/api/me/pools/*", (route) => {
    const url = route.request().url();
    const role = url.split("/").pop();
    if (route.request().method() === "PUT") {
      const body = route.request().postDataJSON();
      savedPools[role] = body.champions;
      return route.fulfill({ json: { role, champions: body.champions } });
    }
    if (route.request().method() === "DELETE") {
      delete savedPools[role];
      return route.fulfill({ status: 204, body: "" });
    }
  });
});

test("save a pool preset, switch role and back, pool auto-loads", async ({ page }) => {
  await page.goto("/");

  // Wait for the draft board to render (AI enabled, auth restore complete).
  await expect(page.locator(".draft-body")).toBeVisible();

  // Type a champion into the pool picker.
  const poolPicker = page.locator(".draft-body .picker").first();
  await poolPicker.getByPlaceholder("Search a champion…").fill("Aatrox");
  await poolPicker.getByText("Aatrox").click();

  // Save as MID pool.
  await page.getByRole("button", { name: "Save as MID pool" }).click();

  // Switch to TOP.
  await page.locator(".role-btn", { hasText: "TOP" }).click();

  // Pool should be empty (no TOP preset).
  await expect(poolPicker.locator(".chip")).toBeHidden();

  // Switch back to MID — pool should auto-load.
  await page.locator(".role-btn", { hasText: "MID" }).click();
  await expect(poolPicker.locator(".chip")).toContainText("Aatrox");
});

test("the save button is disabled when the pool is empty", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Save as MID pool" })).toBeDisabled();
});

test("logged-out users do not see the save button", async ({ page }) => {
  await page.route("**/api/auth/refresh", (route) =>
    route.fulfill({ status: 401, json: { detail: "No refresh token" } }),
  );
  await page.goto("/");
  await expect(page.getByRole("button", { name: /Save as .+ pool/ })).toBeHidden();
});

test("seed from profile copies champion names into the pool picker", async ({ page }) => {
  const PROFILE = {
    riot_id: "Faker#KR1",
    region: "KR",
    level: 500,
    profile_icon_id: 1,
    ranked: [],
    top_masteries: [{ champion_id: 266, points: 100000, level: 7 }],
  };
  const POOL = {
    queue: "all",
    total_games: 5,
    champions: [],
    top: [
      { champion_id: 266, champion_name: "Aatrox", games: 5, wins: 3, win_rate: 0.6, avg_kda: 3, avg_cs_per_min: 7, form_score: 0.5 },
    ],
  };
  await page.route("**/api/summoner/**", (route) => route.fulfill({ json: PROFILE }));
  await page.route("**/api/pool/**", (route) => route.fulfill({ json: POOL }));

  await page.goto("/");
  await page.getByLabel("Riot ID").fill("Faker#KR1");

  // Wait for profile to load, then seed.
  await expect(page.locator(".profile")).toContainText("Faker#KR1");
  await page.getByRole("button", { name: "Seed from profile" }).click();

  const poolPicker = page.locator(".draft-body .picker").first();
  await expect(poolPicker.locator(".chip")).toContainText("Aatrox");
});

test("roles with saved presets show a visual indicator", async ({ page }) => {
  savedPools = { MID: ["Ahri"] };
  await page.goto("/");

  // Wait for the draft body to render and presets to load.
  await expect(page.locator(".draft-body")).toBeVisible();

  const midBtn = page.getByRole("button", { name: "MID", exact: true });
  await expect(midBtn).toHaveClass(/has-preset/);

  const topBtn = page.getByRole("button", { name: "TOP", exact: true });
  await expect(topBtn).not.toHaveClass(/has-preset/);
});
