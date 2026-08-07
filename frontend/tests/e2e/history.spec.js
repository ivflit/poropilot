import { test, expect } from "@playwright/test";

const CHAMPIONS = {
  103: { champion_id: 103, name: "Ahri", title: "the Nine-Tailed Fox", image_url: "http://x/Ahri.png" },
  238: { champion_id: 238, name: "Zed", title: "the Master of Shadows", image_url: "http://x/Zed.png" },
  64: { champion_id: 64, name: "LeeSin", title: "the Blind Monk", image_url: "http://x/LeeSin.png" },
  22: { champion_id: 22, name: "Ashe", title: "the Frost Archer", image_url: "http://x/Ashe.png" },
};

const PROFILE = {
  riot_id: "Player#TAG",
  region: "EUW",
  level: 200,
  profile_icon_id: 1,
  ranked: [{ queueType: "RANKED_SOLO_5x5", tier: "GOLD", rank: "I", leaguePoints: 75, wins: 30, losses: 20 }],
  top_masteries: [{ champion_id: 103, points: 50000, level: 6 }],
};

const POOL = { queue: "all", total_games: 3, champions: [], top: [] };

const now = Math.floor(Date.now() / 1000);

const HISTORY = {
  total_fetched: 3,
  aggregate: { wins: 2, losses: 1, win_rate: 0.6667, avg_kills: 7.7, avg_deaths: 4.3, avg_assists: 9.7, kda_ratio: 5.31 },
  matches: [
    {
      match_id: "EUW1_001", champion: "Ahri", win: true, kills: 8, deaths: 2, assists: 10,
      cs: 210, cs_per_min: 7.0, damage: 22000, damage_per_min: 733, gold: 14000, vision_score: 30,
      role: "MIDDLE", opponent_champion: "Zed", queue_id: 420, duration_min: 30.0,
      game_start: now - 3600,
      participants: [
        { champion: "Ahri", team_id: 100 }, { champion: "LeeSin", team_id: 100 },
        { champion: "Ashe", team_id: 100 }, { champion: "Zed", team_id: 200 },
        { champion: "Ahri", team_id: 200 },
      ],
    },
    {
      match_id: "EUW1_002", champion: "Zed", win: false, kills: 3, deaths: 7, assists: 4,
      cs: 160, cs_per_min: 5.3, damage: 14000, damage_per_min: 467, gold: 10000, vision_score: 12,
      role: "MIDDLE", opponent_champion: "Ahri", queue_id: 420, duration_min: 30.0,
      game_start: now - 7200,
      participants: [
        { champion: "Zed", team_id: 100 }, { champion: "Ahri", team_id: 200 },
      ],
    },
    {
      match_id: "EUW1_003", champion: "LeeSin", win: true, kills: 12, deaths: 4, assists: 15,
      cs: 80, cs_per_min: 3.2, damage: 18000, damage_per_min: 720, gold: 13000, vision_score: 40,
      role: "JUNGLE", opponent_champion: "Ashe", queue_id: 420, duration_min: 25.0,
      game_start: now - 86400,
      participants: [
        { champion: "LeeSin", team_id: 100 }, { champion: "Ashe", team_id: 200 },
      ],
    },
  ],
};

const FILTERED_JUNGLE = {
  total_fetched: 1,
  aggregate: { wins: 1, losses: 0, win_rate: 1.0, avg_kills: 12, avg_deaths: 4, avg_assists: 15, kda_ratio: 6.75 },
  matches: [HISTORY.matches[2]],
};

const FILTERED_WINS = {
  total_fetched: 2,
  aggregate: { wins: 2, losses: 0, win_rate: 1.0, avg_kills: 10, avg_deaths: 3, avg_assists: 12.5, kda_ratio: 7.33 },
  matches: [HISTORY.matches[0], HISTORY.matches[2]],
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/config", (route) =>
    route.fulfill({ json: { ai_enabled: false, auth_enabled: false, ddragon_version: "14.1.1" } }),
  );
  await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
  await page.route("**/api/summoner/**", (route) => route.fulfill({ json: PROFILE }));
  await page.route("**/api/pool/**", (route) => route.fulfill({ json: POOL }));
  await page.route("**/api/history/**", (route) => {
    const url = new URL(route.request().url());
    const role = url.searchParams.get("role");
    const result = url.searchParams.get("result");
    if (role === "JUNGLE") return route.fulfill({ json: FILTERED_JUNGLE });
    if (result === "win") return route.fulfill({ json: FILTERED_WINS });
    return route.fulfill({ json: HISTORY });
  });
});

async function searchPlayer(page) {
  await page.goto("/");
  await page.getByLabel("Riot ID").fill("Player#TAG");
  await expect(page.locator(".profile")).toContainText("Player#TAG");
}

test("match history panel renders with matches", async ({ page }) => {
  await searchPlayer(page);
  const card = page.locator(".history-card");
  await expect(card).toBeVisible();
  await expect(card.locator(".history-row")).toHaveCount(3);
  await expect(card).toContainText("Ahri");
  await expect(card).toContainText("Zed");
  await expect(card).toContainText("LeeSin");
});

test("match row shows KDA, CS, damage, and duration", async ({ page }) => {
  await searchPlayer(page);
  const firstRow = page.locator(".history-row").first();
  await expect(firstRow).toContainText("8/2/10");
  await expect(firstRow).toContainText("210");
  await expect(firstRow).toContainText("22,000");
  await expect(firstRow).toContainText("30m");
});

test("match row shows opponent champion", async ({ page }) => {
  await searchPlayer(page);
  const firstRow = page.locator(".history-row").first();
  await expect(firstRow).toContainText("vs");
  await expect(firstRow).toContainText("Zed");
});

test("clicking a match expands to show participants", async ({ page }) => {
  await searchPlayer(page);
  await page.locator(".history-main").first().click();
  const detail = page.locator(".history-detail").first();
  await expect(detail).toBeVisible();
  await expect(detail.locator(".team-blue")).toBeVisible();
  await expect(detail.locator(".team-red")).toBeVisible();
});

test("role filter shows only matching matches", async ({ page }) => {
  await searchPlayer(page);
  const card = page.locator(".history-card");
  await card.locator(".filter-btn", { hasText: "Jng" }).click();
  await expect(card.locator(".history-row")).toHaveCount(1);
  await expect(card).toContainText("LeeSin");
});

test("result filter shows only wins", async ({ page }) => {
  await searchPlayer(page);
  const card = page.locator(".history-card");
  await card.getByRole("button", { name: "W" }).click();
  await expect(card.locator(".history-row")).toHaveCount(2);
});

test("aggregate stats card shows W/L, win%, and KDA", async ({ page }) => {
  await searchPlayer(page);
  const agg = page.locator(".agg-card");
  await expect(agg).toBeVisible();
  await expect(agg).toContainText("2W 1L");
  await expect(agg).toContainText("67%");
  await expect(agg).toContainText("5.31 KDA");
  await expect(agg).toContainText("3 games");
});

test("win and loss results are visually distinct", async ({ page }) => {
  await searchPlayer(page);
  const winBar = page.locator(".history-row").first().locator(".bar-win");
  const lossBar = page.locator(".history-row").nth(1).locator(".bar-loss");
  await expect(winBar).toBeVisible();
  await expect(lossBar).toBeVisible();
});
