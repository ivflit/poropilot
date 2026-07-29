import { test, expect } from "@playwright/test";

const CONFIG = { ai_enabled: false, auth_enabled: true, ddragon_version: "14.1.1" };
const TOKEN = { access_token: "test-token", token_type: "bearer" };
const USER = { id: 1, email: "test@example.com", riot_region: null, riot_name: null, riot_tag: null };

test.beforeEach(async ({ page }) => {
  // Config reports auth enabled.
  await page.route("**/api/config", (route) => route.fulfill({ json: CONFIG }));
  // Block the session restore so tests start logged out.
  await page.route("**/api/auth/refresh", (route) =>
    route.fulfill({ status: 401, json: { detail: "No refresh token" } }),
  );
  await page.route("**/api/champions", (route) => route.fulfill({ json: {} }));
});

test("shows the Log in button when auth is enabled", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Log in" })).toBeVisible();
});

test("hides the Log in button when auth is disabled", async ({ page }) => {
  await page.route("**/api/config", (route) =>
    route.fulfill({ json: { ...CONFIG, auth_enabled: false } }),
  );
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Log in" })).toBeHidden();
});

test("log in → shows user email in header → log out", async ({ page }) => {
  // Mock signup/login and me endpoints.
  await page.route("**/api/auth/login", (route) => route.fulfill({ json: TOKEN }));
  await page.route("**/api/auth/me", (route) => route.fulfill({ json: USER }));
  await page.route("**/api/auth/logout", (route) =>
    route.fulfill({ json: { detail: "Logged out" } }),
  );

  await page.goto("/");

  // Open modal and log in.
  await page.getByRole("button", { name: "Log in" }).click();
  await page.getByLabel("Email").fill("test@example.com");
  await page.getByLabel("Password").fill("password123");
  await page.locator(".auth-submit").click();

  // Should see the user email in the header now.
  await expect(page.locator(".user-email")).toHaveText("test@example.com");
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();

  // Log out.
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page.getByRole("button", { name: "Log in" })).toBeVisible();
  await expect(page.locator(".user-email")).toBeHidden();
});

test("sign up flow works", async ({ page }) => {
  await page.route("**/api/auth/signup", (route) => route.fulfill({ json: TOKEN, status: 201 }));
  await page.route("**/api/auth/me", (route) => route.fulfill({ json: USER }));

  await page.goto("/");
  await page.getByRole("button", { name: "Log in" }).click();
  // Switch to sign up.
  await page.getByRole("button", { name: "Sign up" }).click();

  await page.getByLabel("Email").fill("new@example.com");
  await page.getByLabel("Password").fill("password123");
  await page.locator(".auth-submit").click();

  await expect(page.locator(".user-email")).toHaveText("test@example.com");
});

test("shows an error on bad credentials", async ({ page }) => {
  await page.route("**/api/auth/login", (route) =>
    route.fulfill({ status: 401, json: { detail: "Invalid email or password" } }),
  );

  await page.goto("/");
  await page.getByRole("button", { name: "Log in" }).click();
  await page.getByLabel("Email").fill("wrong@example.com");
  await page.getByLabel("Password").fill("wrongpassword");
  await page.locator(".auth-submit").click();

  await expect(page.locator(".auth-error")).toHaveText("Invalid email or password");
});

test("the app works fine when logged out", async ({ page }) => {
  const PROFILE = {
    riot_id: "Faker#KR1",
    region: "KR",
    level: 500,
    profile_icon_id: 1,
    ranked: [],
    top_masteries: [],
  };
  await page.route("**/api/summoner/**", (route) => route.fulfill({ json: PROFILE }));

  await page.goto("/");
  await page.getByLabel("Riot ID").fill("Faker#KR1");

  await expect(page.locator(".profile")).toContainText("Faker#KR1");
});
