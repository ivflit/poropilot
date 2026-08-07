import { test, expect } from "@playwright/test";

test("home page renders the search UI", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /PoroPilot/ })).toBeVisible();
  await expect(page.getByLabel("Riot ID")).toBeVisible();
  await expect(page.locator(".search-bar").getByLabel("Region")).toBeVisible();
});

test("shows a hint when the Riot ID has no tag", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Riot ID").fill("noTagHere");
  await expect(page.getByRole("alert")).toContainText("name#tag");
});
