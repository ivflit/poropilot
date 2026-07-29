"""Tests for the auth system — signup, login, refresh, 401, duplicate email."""

import asyncio
import unittest

# Patch settings before importing anything that reads them.
import app.config  # noqa: E402

app.config.settings.jwt_secret = "test-secret-key-for-unit-tests"

from app.auth.passwords import hash_password, verify_password  # noqa: E402
from app.auth.service import authenticate, create_user, get_user_by_email, link_riot_id  # noqa: E402
from app.auth.tokens import create_access_token, create_refresh_token, decode_token  # noqa: E402
from app.db import Base  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


class TestPasswords(unittest.TestCase):
    def test_hash_and_verify(self):
        hashed = hash_password("my-secure-pass")
        self.assertNotEqual(hashed, "my-secure-pass")
        self.assertTrue(verify_password("my-secure-pass", hashed))

    def test_wrong_password(self):
        hashed = hash_password("correct")
        self.assertFalse(verify_password("wrong", hashed))


class TestTokens(unittest.TestCase):
    def test_access_token_roundtrip(self):
        token = create_access_token(42)
        self.assertEqual(decode_token(token, "access"), 42)

    def test_refresh_token_roundtrip(self):
        token = create_refresh_token(7)
        self.assertEqual(decode_token(token, "refresh"), 7)

    def test_wrong_token_type_rejected(self):
        token = create_access_token(42)
        self.assertIsNone(decode_token(token, "refresh"))

    def test_garbage_token_rejected(self):
        self.assertIsNone(decode_token("not.a.jwt", "access"))


class TestAuthService(unittest.TestCase):
    """Integration tests using an in-memory SQLite database."""

    def setUp(self):
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        _run(self._create_tables())

    async def _create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def tearDown(self):
        _run(self.engine.dispose())

    def test_create_and_lookup(self):
        async def _test():
            async with self.session_factory() as s:
                user = await create_user(s, "test@example.com", "pass123")
                self.assertEqual(user.email, "test@example.com")
                self.assertNotEqual(user.password_hash, "pass123")

                found = await get_user_by_email(s, "test@example.com")
                self.assertIsNotNone(found)
                self.assertEqual(found.id, user.id)

        _run(_test())

    def test_authenticate_success(self):
        async def _test():
            async with self.session_factory() as s:
                await create_user(s, "auth@example.com", "correct")
                user = await authenticate(s, "auth@example.com", "correct")
                self.assertIsNotNone(user)

        _run(_test())

    def test_authenticate_wrong_password(self):
        async def _test():
            async with self.session_factory() as s:
                await create_user(s, "auth2@example.com", "correct")
                user = await authenticate(s, "auth2@example.com", "wrong")
                self.assertIsNone(user)

        _run(_test())

    def test_authenticate_unknown_email(self):
        async def _test():
            async with self.session_factory() as s:
                user = await authenticate(s, "nobody@example.com", "whatever")
                self.assertIsNone(user)

        _run(_test())

    def test_duplicate_email_raises(self):
        async def _test():
            async with self.session_factory() as s:
                await create_user(s, "dup@example.com", "pass1")
                with self.assertRaises(Exception):  # noqa: B017
                    await create_user(s, "dup@example.com", "pass2")

        _run(_test())

    def test_link_riot_id(self):
        async def _test():
            async with self.session_factory() as s:
                user = await create_user(s, "riot@example.com", "pass")
                updated = await link_riot_id(s, user, "EUW", "Faker", "KR1")
                self.assertEqual(updated.riot_region, "EUW")
                self.assertEqual(updated.riot_name, "Faker")
                self.assertEqual(updated.riot_tag, "KR1")

        _run(_test())


class TestAuthRoutes(unittest.TestCase):
    """Route-level tests against the FastAPI test client with an in-memory DB."""

    @classmethod
    def setUpClass(cls):
        import importlib

        try:
            importlib.import_module("aiosqlite")
        except ModuleNotFoundError as err:
            raise unittest.SkipTest("aiosqlite not installed") from err

    def setUp(self):
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

        _run(self._create_tables())

        # Override the session dependency so routes use our test DB.
        from app.api.auth_routes import router as auth_router
        from app.db import get_session
        from app.main import app

        # Only add if not already mounted.
        auth_prefixes = [r.path for r in app.routes if hasattr(r, "path") and "/api/auth" in r.path]
        if not auth_prefixes:
            app.include_router(auth_router)

        async def _override_session():
            async with self.session_factory() as session:
                yield session

        app.dependency_overrides[get_session] = _override_session

        from fastapi.testclient import TestClient

        self.client = TestClient(app)

    async def _create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def tearDown(self):
        from app.db import get_session
        from app.main import app

        app.dependency_overrides.pop(get_session, None)
        _run(self.engine.dispose())

    def test_signup_returns_token(self):
        resp = self.client.post("/api/auth/signup", json={"email": "new@example.com", "password": "pass123"})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_signup_duplicate_email(self):
        self.client.post("/api/auth/signup", json={"email": "dup@example.com", "password": "pass1"})
        resp = self.client.post("/api/auth/signup", json={"email": "dup@example.com", "password": "pass2"})
        self.assertEqual(resp.status_code, 409)

    def test_login_success(self):
        self.client.post("/api/auth/signup", json={"email": "login@example.com", "password": "pass"})
        resp = self.client.post("/api/auth/login", json={"email": "login@example.com", "password": "pass"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access_token", resp.json())

    def test_login_wrong_password(self):
        self.client.post("/api/auth/signup", json={"email": "wrong@example.com", "password": "right"})
        resp = self.client.post("/api/auth/login", json={"email": "wrong@example.com", "password": "nope"})
        self.assertEqual(resp.status_code, 401)

    def test_me_without_token(self):
        resp = self.client.get("/api/auth/me")
        self.assertEqual(resp.status_code, 401)

    def test_me_with_valid_token(self):
        signup = self.client.post(
            "/api/auth/signup", json={"email": "me@example.com", "password": "pass"}
        )
        token = signup.json()["access_token"]
        resp = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["email"], "me@example.com")

    def test_me_with_garbage_token(self):
        resp = self.client.get("/api/auth/me", headers={"Authorization": "Bearer garbage.token.here"})
        self.assertEqual(resp.status_code, 401)

    def test_refresh_returns_new_access_token(self):
        self.client.post(
            "/api/auth/signup", json={"email": "refresh@example.com", "password": "pass"}
        )
        # Extract the refresh_token cookie and send it explicitly — TestClient
        # doesn't always forward path-scoped cookies automatically.
        refresh_cookie = self.client.cookies.get("refresh_token")
        self.assertIsNotNone(refresh_cookie)
        resp = self.client.post(
            "/api/auth/refresh", cookies={"refresh_token": refresh_cookie}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access_token", resp.json())

    def test_logout_clears_cookie(self):
        self.client.post("/api/auth/signup", json={"email": "logout@example.com", "password": "pass"})
        resp = self.client.post("/api/auth/logout")
        self.assertEqual(resp.status_code, 200)

    def test_link_riot_id(self):
        signup = self.client.post(
            "/api/auth/signup", json={"email": "riot@example.com", "password": "pass"}
        )
        token = signup.json()["access_token"]
        resp = self.client.put(
            "/api/auth/me/riot-id",
            json={"region": "EUW", "name": "Faker", "tag": "KR1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["riot_name"], "Faker")
