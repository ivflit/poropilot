import { test, expect } from "@playwright/test";

const CHAMPIONS = {
  103: { champion_id: 103, name: "Ahri", title: "the Nine-Tailed Fox", image_url: "http://x/Ahri.png" },
};

const PROFILE = {
  riot_id: "Faker#KR1",
  region: "KR",
  level: 500,
  profile_icon_id: 1,
  ranked: [{ queueType: "RANKED_SOLO_5x5", tier: "DIAMOND", rank: "II", leaguePoints: 42, wins: 60, losses: 40 }],
  top_masteries: [{ champion_id: 103, points: 100000, level: 7 }],
};

const POOL = { queue: "solo", total_games: 5, champions: [], top: [] };

const MATCHES = [
  { match_id: "KR_001", champion: "Ahri", win: true, kills: 8, deaths: 2, assists: 10, queue_id: 420, duration_min: 28.5 },
  { match_id: "KR_002", champion: "Ahri", win: false, kills: 3, deaths: 7, assists: 4, queue_id: 420, duration_min: 32.1 },
];

const REVIEW = {
  match_id: "KR_002",
  champion: "Ahri",
  win: false,
  verdict: "Too many deaths in mid-game teamfights cost you the game",
  issues: [
    { point: "Died 7 times, most after laning phase", stat: "7 deaths in 32 minutes" },
    { point: "Low damage contribution despite mid lane role", stat: "14.2% damage share" },
  ],
  tips: [
    "Position further back in teamfights and wait for cooldowns",
    "Ward flanks before objective fights to avoid getting caught",
  ],
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/config", (route) =>
    route.fulfill({ json: { ai_enabled: true, auth_enabled: false, ddragon_version: "14.1.1" } }),
  );
  await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
  await page.route("**/api/summoner/**", (route) => route.fulfill({ json: PROFILE }));
  await page.route("**/api/pool/**", (route) => route.fulfill({ json: POOL }));
  await page.route("**/api/matches/**", (route) => route.fulfill({ json: MATCHES }));
  await page.route("**/api/review/**", (route) => route.fulfill({ json: REVIEW }));
});

async function searchPlayer(page) {
  await page.goto("/");
  await page.getByLabel("Riot ID").fill("Faker#KR1");
  await expect(page.locator(".profile")).toContainText("Faker#KR1");
}

test("review panel shows recent ranked games", async ({ page }) => {
  await searchPlayer(page);

  const panel = page.locator(".review-card");
  await expect(panel.locator("h3")).toHaveText("Post-game review");
  await expect(panel.locator(".match-row")).toHaveCount(2);
  await expect(panel.locator(".match-champ").first()).toHaveText("Ahri");
});

test("clicking a match shows the AI review", async ({ page }) => {
  await searchPlayer(page);

  // Click the second (lost) match.
  await page.locator(".match-row").nth(1).click();

  const reviewBody = page.locator(".review-body");
  await expect(reviewBody.locator(".review-verdict")).toContainText("Too many deaths");
  await expect(reviewBody.locator(".review-issue")).toHaveCount(2);
  await expect(reviewBody.locator(".issue-stat").first()).toContainText("7 deaths");
  await expect(reviewBody.locator(".review-tips li")).toHaveCount(2);
});

test("review panel is hidden when AI is disabled", async ({ page }) => {
  await page.route("**/api/config", (route) =>
    route.fulfill({ json: { ai_enabled: false, auth_enabled: false, ddragon_version: "14.1.1" } }),
  );

  await searchPlayer(page);
  await expect(page.locator(".review-card")).toBeHidden();
});

test("shows loading state while review is fetching", async ({ page }) => {
  // Delay the review response.
  await page.route("**/api/review/**", async (route) => {
    await new Promise((r) => setTimeout(r, 500));
    await route.fulfill({ json: REVIEW });
  });

  await searchPlayer(page);
  await page.locator(".match-row").first().click();

  await expect(page.locator(".review-body")).toContainText("Reviewing this game");
});

test("shows error when review fails", async ({ page }) => {
  await page.route("**/api/review/**", (route) =>
    route.fulfill({ status: 500, json: { detail: "AI service error" } }),
  );

  await searchPlayer(page);
  await page.locator(".match-row").first().click();

  await expect(page.locator(".review-error")).toContainText("AI service error");
});
