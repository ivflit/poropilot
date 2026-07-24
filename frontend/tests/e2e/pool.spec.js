import { test, expect } from "@playwright/test";

const CHAMPIONS = {
  266: { champion_id: 266, name: "Aatrox", title: "the Darkin Blade", image_url: "http://x/Aatrox.png" },
};

const PROFILE = {
  riot_id: "Faker#KR1",
  region: "KR",
  level: 500,
  profile_icon_id: 1,
  ranked: [],
  top_masteries: [{ champion_id: 266, points: 123456, level: 7 }],
};

const POOL = {
  total_games: 2,
  champions: [],
  top: [
    {
      champion_id: 266,
      champion_name: "Aatrox",
      games: 2,
      wins: 1,
      win_rate: 0.5,
      avg_kda: 3.0,
      avg_cs_per_min: 7.5,
      form_score: 0.42,
    },
  ],
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
  await page.route("**/api/summoner/**", (route) => route.fulfill({ json: PROFILE }));
  await page.route("**/api/pool/**", (route) => route.fulfill({ json: POOL }));
});

test("shows recent form (win-rate) for the player's top champions", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Riot ID").fill("Faker#KR1");

  const pool = page.locator(".pool");
  await expect(pool).toContainText("Aatrox");
  await expect(pool).toContainText("50%");
  await expect(pool).toContainText("1W");
});
