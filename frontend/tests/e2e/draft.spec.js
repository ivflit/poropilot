import { test, expect } from "@playwright/test";

const CHAMPIONS = {
  266: { champion_id: 266, name: "Aatrox", title: "the Darkin Blade", image_url: "http://x/Aatrox.png" },
  103: { champion_id: 103, name: "Ahri", title: "the Nine-Tailed Fox", image_url: "http://x/Ahri.png" },
};

const SUGGESTIONS = {
  suggestions: [
    { champion: "Ahri", reason: "Strong pick into the enemy bans.", confidence: "high", in_pool: true },
    { champion: "Syndra", reason: "Strong meta pick for this role.", confidence: "medium", in_pool: false },
  ],
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
});

test("suggests a pick from the draft board when AI is enabled", async ({ page }) => {
  await page.route("**/api/config", (route) => route.fulfill({ json: { ai_enabled: true } }));
  await page.route("**/api/draft", (route) => route.fulfill({ json: SUGGESTIONS }));
  await page.goto("/");

  await page.getByLabel("Role").selectOption("MID");
  await page.getByLabel("Your champion pool").selectOption("Ahri");
  await page.getByRole("button", { name: "Add" }).first().click();
  await page.getByRole("button", { name: "Suggest a pick" }).click();

  await expect(page.locator(".suggestions")).toContainText("Ahri");
  await expect(page.locator(".suggestions")).toContainText("Strong pick into the enemy bans.");
  await expect(page.locator(".suggestions")).toContainText("your pool");
  await expect(page.locator(".suggestions")).toContainText("meta pick");
});

test("hides the draft board when AI is disabled", async ({ page }) => {
  await page.route("**/api/config", (route) => route.fulfill({ json: { ai_enabled: false } }));
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Draft assistant" })).toHaveCount(0);
});
