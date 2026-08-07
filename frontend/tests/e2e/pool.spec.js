import { test, expect } from "@playwright/test";

const CHAMPIONS = {
  266: { champion_id: 266, name: "Aatrox", title: "the Darkin Blade", image_url: "http://x/Aatrox.png" },
  103: { champion_id: 103, name: "Ahri", title: "the Nine-Tailed Fox", image_url: "http://x/Ahri.png" },
  238: { champion_id: 238, name: "Zed", title: "the Master of Shadows", image_url: "http://x/Zed.png" },
  64: { champion_id: 64, name: "LeeSin", title: "the Blind Monk", image_url: "http://x/LeeSin.png" },
  222: { champion_id: 222, name: "Jinx", title: "the Loose Cannon", image_url: "http://x/Jinx.png" },
  412: { champion_id: 412, name: "Thresh", title: "the Chain Warden", image_url: "http://x/Thresh.png" },
};

const PROFILE = {
  riot_id: "Faker#KR1",
  region: "KR",
  level: 500,
  profile_icon_id: 1,
  ranked: [],
  top_masteries: [{ champion_id: 266, points: 123456, level: 7 }],
};

const champ = (id, name, games, wins, kda) => ({
  champion_id: id, champion_name: name, games, wins, win_rate: wins / games,
  avg_kda: kda, avg_cs_per_min: 7.5, form_score: 0.42,
});

const ALL_CHAMPS = [
  champ(266, "Aatrox", 8, 5, 3.2),
  champ(103, "Ahri", 6, 4, 4.1),
  champ(238, "Zed", 4, 2, 2.8),
  champ(64, "LeeSin", 3, 2, 3.5),
  champ(222, "Jinx", 2, 1, 2.0),
  champ(412, "Thresh", 1, 1, 5.0),
];

const POOL = {
  total_games: 24,
  champions: ALL_CHAMPS,
  top: ALL_CHAMPS.slice(0, 5),
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
  await page.route("**/api/summoner/**", (route) => route.fulfill({ json: PROFILE }));
  await page.route("**/api/pool/**", (route) => route.fulfill({ json: POOL }));
  await page.route("**/api/history/**", (route) =>
    route.fulfill({ json: { matches: [], total_fetched: 0, aggregate: { wins: 0, losses: 0, win_rate: 0, avg_kills: 0, avg_deaths: 0, avg_assists: 0, kda_ratio: 0 } } }),
  );
});

test("shows recent form (win-rate and KDA) for the player's top champions", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Riot ID").fill("Faker#KR1");

  const pool = page.locator(".pool");
  await expect(pool).toContainText("Aatrox");
  await expect(pool).toContainText("63%");
  await expect(pool).toContainText("3.2 KDA");
  await expect(pool).toContainText("8g");
});

test("show all toggle reveals all champions", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Riot ID").fill("Faker#KR1");

  const pool = page.locator(".pool");
  // Initially top 5 shown, Thresh (6th) not visible.
  await expect(pool).toContainText("Aatrox");
  await expect(pool).not.toContainText("Thresh");

  // Click "Show all 6".
  await page.getByRole("button", { name: "Show all 6" }).click();
  await expect(pool).toContainText("Thresh");

  // Toggle back.
  await page.getByRole("button", { name: "Show top 5" }).click();
  await expect(pool).not.toContainText("Thresh");
});
