import { test, expect } from "@playwright/test";

const CHAMPIONS = {
  266: { champion_id: 266, name: "Aatrox", title: "the Darkin Blade", image_url: "http://x/Aatrox.png" },
  64: { champion_id: 64, name: "LeeSin", title: "the Blind Monk", image_url: "http://x/LeeSin.png" },
};

const PROFILE = {
  riot_id: "Faker#KR1",
  region: "KR",
  level: 500,
  profile_icon_id: 1,
  ranked: [
    { queueType: "RANKED_SOLO_5x5", tier: "DIAMOND", rank: "II", leaguePoints: 42, wins: 60, losses: 40 },
    { queueType: "RANKED_FLEX_SR", tier: "GOLD", rank: "IV", leaguePoints: 11, wins: 5, losses: 15 },
  ],
  top_masteries: [{ champion_id: 266, points: 123456, level: 7 }],
};

const champion = (id, name, games, wins) => ({
  champion_id: id,
  champion_name: name,
  games,
  wins,
  win_rate: wins / games,
  avg_kda: 3.0,
  avg_cs_per_min: 7.5,
  form_score: 0.42,
});

// The same player, three different truths depending on the queue.
const POOLS = {
  all: { queue: "all", total_games: 10, champions: [], top: [champion(266, "Aatrox", 10, 8)] },
  solo: { queue: "solo", total_games: 4, champions: [], top: [champion(266, "Aatrox", 4, 2)] },
  flex: { queue: "flex", total_games: 2, champions: [], top: [champion(64, "LeeSin", 2, 1)] },
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
  await page.route("**/api/summoner/**", (route) => route.fulfill({ json: PROFILE }));
  await page.route("**/api/pool/**", (route) => {
    const queue = new URL(route.request().url()).searchParams.get("queue") ?? "all";
    return route.fulfill({ json: POOLS[queue] });
  });
  await page.route("**/api/history/**", (route) =>
    route.fulfill({ json: { matches: [], total_fetched: 0 } }),
  );
});

async function search(page) {
  await page.goto("/");
  await page.getByLabel("Riot ID").fill("Faker#KR1");
  await expect(page.locator(".pool")).toContainText("Aatrox");
}

test("the queue filter only appears once a profile is loaded", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("group", { name: "Filter matches by queue" })).toBeHidden();

  await page.getByLabel("Riot ID").fill("Faker#KR1");
  await expect(page.getByRole("group", { name: "Filter matches by queue" })).toBeVisible();
});

test("switching to ranked solo re-reads the champion pool for that queue", async ({ page }) => {
  await search(page);
  await expect(page.locator(".pool")).toContainText("80%"); // 8 of 10, all queues

  await page.getByRole("button", { name: "Ranked solo/duo" }).click();

  const pool = page.locator(".pool");
  await expect(pool).toContainText("50%"); // 2 of 4 in solo — the honest number
  await expect(pool).toContainText("2W · 4g");
});

test("switching to flex shows that queue's champions and rank", async ({ page }) => {
  await search(page);
  await expect(page.locator(".rank-queue")).toHaveText("Solo / Duo");

  await page.getByRole("button", { name: "Ranked flex" }).click();

  await expect(page.locator(".pool")).toContainText("LeeSin");
  // The rank badge follows the filter — flex is Gold IV, not the Diamond II solo rank.
  await expect(page.locator(".rank-queue")).toHaveText("Flex 5v5");
  await expect(page.locator(".rank-full")).toContainText("Gold IV");
});

test("the selected filter is marked as pressed", async ({ page }) => {
  await search(page);
  const all = page.getByRole("button", { name: "All queues" });
  const solo = page.getByRole("button", { name: "Ranked solo/duo" });

  await expect(all).toHaveAttribute("aria-pressed", "true");
  await solo.click();
  await expect(solo).toHaveAttribute("aria-pressed", "true");
  await expect(all).toHaveAttribute("aria-pressed", "false");
});

test("a queue with no games shows an empty state, not an error", async ({ page }) => {
  await page.route("**/api/pool/**", (route) => {
    const queue = new URL(route.request().url()).searchParams.get("queue") ?? "all";
    if (queue === "flex") {
      return route.fulfill({ json: { queue: "flex", total_games: 0, champions: [], top: [] } });
    }
    return route.fulfill({ json: POOLS[queue] });
  });

  await search(page);
  await page.getByRole("button", { name: "Ranked flex" }).click();

  await expect(page.getByText("No games in ranked flex")).toBeVisible();
  await expect(page.locator(".profile")).toContainText("Faker#KR1"); // profile stays put
});

test("switching the filter keeps the profile on screen", async ({ page }) => {
  await search(page);
  await page.getByRole("button", { name: "Ranked solo/duo" }).click();

  await expect(page.locator(".profile")).toContainText("Faker#KR1");
  await expect(page.locator(".profile")).toContainText("Level 500");
});

test("the queue filter lives inside the recent form card, adjacent to its content", async ({ page }) => {
  await search(page);

  // The filter group is a child of the same card that holds the pool list.
  const recentFormCard = page.locator(".card", { has: page.locator(".pool") });
  await expect(recentFormCard.getByRole("group", { name: "Filter matches by queue" })).toBeVisible();
  await expect(recentFormCard.locator("h3")).toHaveText("Recent form");
});

test("champion mastery is labelled as all-time data", async ({ page }) => {
  await search(page);

  const masteryCard = page.locator(".card", { has: page.locator(".m-row") });
  await expect(masteryCard.locator(".card-sub")).toContainText("All time");
});

test("recent form card appears before the mastery card in the DOM", async ({ page }) => {
  await search(page);

  // Both cards live inside .profile; recent form (with .pool) should come first.
  const cards = page.locator(".profile > .card");
  const firstCard = cards.first();
  await expect(firstCard.locator("h3")).toHaveText("Recent form");
});
