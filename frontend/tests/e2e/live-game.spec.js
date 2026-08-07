import { test, expect } from "@playwright/test";

const CHAMPIONS = {
  103: { champion_id: 103, name: "Ahri", title: "Fox", image_url: "http://x/Ahri.png" },
  238: { champion_id: 238, name: "Zed", title: "Shadow", image_url: "http://x/Zed.png" },
};

const PROFILE = {
  riot_id: "Player#TAG",
  region: "EUW",
  level: 200,
  profile_icon_id: 1,
  ranked: [],
  top_masteries: [],
};

const POOL = { queue: "all", total_games: 0, champions: [], top: [] };

const LIVE_IN_GAME = {
  in_game: true,
  game_mode: "CLASSIC",
  game_length_sec: 300,
  participants: [
    { champion_id: 103, champion_name: "Ahri", team_id: 100, riot_id: "Player#TAG", rank: "GOLD I 50 LP" },
    { champion_id: 238, champion_name: "Zed", team_id: 200, riot_id: "Enemy#EUW", rank: null },
  ],
};

const LIVE_NOT_IN_GAME = { in_game: false, game_mode: "", game_length_sec: 0, participants: [] };

test.describe("live game - in game", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/config", (route) =>
      route.fulfill({ json: { ai_enabled: false, auth_enabled: false, ddragon_version: "14.1.1" } }),
    );
    await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
    await page.route("**/api/summoner/**", (route) => route.fulfill({ json: PROFILE }));
    await page.route("**/api/pool/**", (route) => route.fulfill({ json: POOL }));
    await page.route("**/api/history/**", (route) =>
      route.fulfill({ json: { matches: [], total_fetched: 0, aggregate: { wins: 0, losses: 0, win_rate: 0, avg_kills: 0, avg_deaths: 0, avg_assists: 0, kda_ratio: 0 } } }),
    );
    await page.route("**/api/live/**", (route) => route.fulfill({ json: LIVE_IN_GAME }));
  });

  test("shows live game with participants", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Riot ID").fill("Player#TAG");

    const card = page.locator(".live-card");
    await expect(card).toBeVisible();
    await expect(card).toContainText("CLASSIC");
    await expect(card).toContainText("Ahri");
    await expect(card).toContainText("Zed");
    await expect(card).toContainText("Player#TAG");
  });

  test("shows rank for participants", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Riot ID").fill("Player#TAG");
    await expect(page.locator(".live-card")).toContainText("G I 50 LP");
  });

  test("shows Unranked for participants without rank", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Riot ID").fill("Player#TAG");
    await expect(page.locator(".live-card")).toContainText("Unranked");
  });
});

test.describe("live game - not in game", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/config", (route) =>
      route.fulfill({ json: { ai_enabled: false, auth_enabled: false, ddragon_version: "14.1.1" } }),
    );
    await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
    await page.route("**/api/summoner/**", (route) => route.fulfill({ json: PROFILE }));
    await page.route("**/api/pool/**", (route) => route.fulfill({ json: POOL }));
    await page.route("**/api/history/**", (route) =>
      route.fulfill({ json: { matches: [], total_fetched: 0, aggregate: { wins: 0, losses: 0, win_rate: 0, avg_kills: 0, avg_deaths: 0, avg_assists: 0, kda_ratio: 0 } } }),
    );
    await page.route("**/api/live/**", (route) => route.fulfill({ json: LIVE_NOT_IN_GAME }));
  });

  test("shows not in game message", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Riot ID").fill("Player#TAG");
    await expect(page.locator(".live-card")).toContainText("Not currently in a game");
  });
});
