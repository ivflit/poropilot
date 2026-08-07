import { test, expect } from "@playwright/test";

const CHAMPIONS = {
  103: { champion_id: 103, name: "Ahri", title: "the Nine-Tailed Fox", image_url: "http://x/Ahri.png" },
};

const MULTI_RESULT = {
  players: [
    {
      riot_id: "Player1#TAG",
      found: true,
      region: "EUW",
      level: 200,
      profile_icon_id: 1,
      ranked: [
        { queueType: "RANKED_SOLO_5x5", tier: "GOLD", rank: "I", leaguePoints: 75, wins: 30, losses: 20 },
      ],
      top_champions: [
        { champion_id: 103, champion_name: "Ahri", games: 10, wins: 7, win_rate: 0.7, avg_kda: 4.0, avg_cs_per_min: 7.0, form_score: 0.5 },
      ],
    },
    {
      riot_id: "Unknown#999",
      found: false,
    },
  ],
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/config", (route) =>
    route.fulfill({ json: { ai_enabled: false, auth_enabled: false, ddragon_version: "14.1.1" } }),
  );
  await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
  await page.route("**/api/multi-search", (route) => route.fulfill({ json: MULTI_RESULT }));
});

test("multi-search panel is visible on the page", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".multi-card")).toBeVisible();
  await expect(page.locator(".multi-card")).toContainText("Multi-search");
});

test("search returns player cards", async ({ page }) => {
  await page.goto("/");
  await page.locator(".multi-textarea").fill("Player1#TAG\nUnknown#999");
  await page.getByRole("button", { name: /Search 2 players/ }).click();

  const results = page.locator(".multi-player");
  await expect(results).toHaveCount(2);
});

test("found player shows rank and champions", async ({ page }) => {
  await page.goto("/");
  await page.locator(".multi-textarea").fill("Player1#TAG");
  await page.getByRole("button", { name: /Search 1 player/ }).click();

  const player = page.locator(".multi-player").first();
  await expect(player).toContainText("Player1#TAG");
  await expect(player).toContainText("Gold I");
  await expect(player).toContainText("Ahri");
  await expect(player).toContainText("70%");
});

test("not found player shows label", async ({ page }) => {
  await page.goto("/");
  await page.locator(".multi-textarea").fill("Player1#TAG\nUnknown#999");
  await page.getByRole("button", { name: /Search 2 players/ }).click();

  const notFound = page.locator(".multi-notfound").first();
  await expect(notFound).toContainText("Not found");
});

test("search button is disabled with empty input", async ({ page }) => {
  await page.goto("/");
  const btn = page.locator(".multi-search-btn");
  await expect(btn).toBeDisabled();
});
