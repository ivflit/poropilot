import { test, expect } from "@playwright/test";

const CHAMPIONS = {
  103: { champion_id: 103, name: "Ahri", title: "Fox", image_url: "http://x/Ahri.png" },
  238: { champion_id: 238, name: "Zed", title: "Shadow", image_url: "http://x/Zed.png" },
};

const TIER_LIST = {
  role: "MID",
  patch: "14.1.1",
  tiers: [
    { tier: "S", champions: [{ name: "Ahri", reason: "Strong roaming mid laner" }] },
    { tier: "A", champions: [{ name: "Zed", reason: "High kill pressure in lane" }] },
  ],
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/config", (route) =>
    route.fulfill({ json: { ai_enabled: true, auth_enabled: false, ddragon_version: "14.1.1" } }),
  );
  await page.route("**/api/champions", (route) => route.fulfill({ json: CHAMPIONS }));
  await page.route("**/api/tier-list**", (route) => route.fulfill({ json: TIER_LIST }));
});

test("tier list panel is visible when AI is enabled", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".tier-card")).toBeVisible();
  await expect(page.locator(".tier-card")).toContainText("Tier list");
});

test("shows tier badges and champions", async ({ page }) => {
  await page.goto("/");
  const card = page.locator(".tier-card");
  await expect(card.locator(".tier-badge")).toHaveCount(2);
  await expect(card).toContainText("Ahri");
  await expect(card).toContainText("Strong roaming mid laner");
  await expect(card).toContainText("Zed");
});

test("role buttons switch the tier list", async ({ page }) => {
  await page.goto("/");
  const card = page.locator(".tier-card");
  await card.getByRole("button", { name: "Top" }).click();
  // The mock returns the same data, but the button should be active
  await expect(card.getByRole("button", { name: "Top" })).toHaveClass(/active/);
});

test("tier list hidden when AI is disabled", async ({ page }) => {
  await page.route("**/api/config", (route) =>
    route.fulfill({ json: { ai_enabled: false, auth_enabled: false, ddragon_version: "14.1.1" } }),
  );
  await page.goto("/");
  await expect(page.locator(".tier-card")).toHaveCount(0);
});
