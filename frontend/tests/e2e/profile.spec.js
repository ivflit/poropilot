import { test, expect } from "@playwright/test";

const CHAMPIONS = {
  266: {
    champion_id: 266,
    name: "Aatrox",
    title: "the Darkin Blade",
    image_url: "https://ddragon.leagueoflegends.com/cdn/14.1.1/img/champion/Aatrox.png",
  },
};

const PROFILE = {
  riot_id: "Faker#KR1",
  region: "KR",
  level: 500,
  profile_icon_id: 1,
  ranked: [
    {
      queueType: "RANKED_SOLO_5x5",
      tier: "CHALLENGER",
      rank: "I",
      leaguePoints: 1200,
      wins: 400,
      losses: 300,
    },
  ],
  top_masteries: [{ champion_id: 266, points: 123456, level: 7 }],
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
});

test("renders champion name, icon and ranked standing", async ({ page }) => {
  await page.route("**/api/summoner/**", (route) => route.fulfill({ json: PROFILE }));
  await page.goto("/");
  await page.getByLabel("Riot ID").fill("Faker#KR1");

  const profile = page.locator(".profile");
  await expect(profile.getByText("Aatrox")).toBeVisible();
  await expect(profile.getByRole("img", { name: "Aatrox" })).toBeVisible();
  await expect(profile.getByText(/Solo\/Duo/)).toBeVisible();
  await expect(profile.getByText(/CHALLENGER I/)).toBeVisible();
});

test("shows Unranked for a player with no ranked entries", async ({ page }) => {
  await page.route("**/api/summoner/**", (route) =>
    route.fulfill({ json: { ...PROFILE, ranked: [] } }),
  );
  await page.goto("/");
  await page.getByLabel("Riot ID").fill("New#EUW");

  await expect(page.locator(".profile").getByText("Unranked")).toBeVisible();
});
