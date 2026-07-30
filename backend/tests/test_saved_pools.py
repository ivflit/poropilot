"""Tests for the saved champion pool presets — CRUD + cross-user isolation."""

import asyncio
import unittest

import app.config

app.config.settings.jwt_secret = "test-secret-key-for-unit-tests"

from app.auth.tokens import create_access_token  # noqa: E402
from app.db import Base  # noqa: E402
from app.models import User  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


class TestSavedPoolRoutes(unittest.TestCase):
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
        _run(self._setup_db())

        from app.api.auth_routes import router as auth_router
        from app.api.pool_routes import router as pool_router
        from app.db import get_session
        from app.main import app

        # Mount routers if not already present.
        mounted = {r.path for r in app.routes if hasattr(r, "path")}
        if not any("/api/auth" in p for p in mounted):
            app.include_router(auth_router)
        if not any("/api/me/pools" in p for p in mounted):
            app.include_router(pool_router)

        async def _override_session():
            async with self.session_factory() as session:
                yield session

        app.dependency_overrides[get_session] = _override_session

        from fastapi.testclient import TestClient

        self.client = TestClient(app)

    async def _setup_db(self):
        from app.auth.passwords import hash_password

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # Seed two users for cross-user isolation tests.
        async with self.session_factory() as s:
            self.user_a = User(email="a@test.com", password_hash=hash_password("pass"))
            self.user_b = User(email="b@test.com", password_hash=hash_password("pass"))
            s.add_all([self.user_a, self.user_b])
            await s.commit()
            await s.refresh(self.user_a)
            await s.refresh(self.user_b)
        self.token_a = create_access_token(self.user_a.id)
        self.token_b = create_access_token(self.user_b.id)

    def tearDown(self):
        from app.db import get_session
        from app.main import app

        app.dependency_overrides.pop(get_session, None)
        _run(self.engine.dispose())

    def _auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    # ── CRUD ───────────────────────────────────────────────────────────────────

    def test_list_pools_empty(self):
        resp = self.client.get("/api/me/pools", headers=self._auth(self.token_a))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_save_and_list(self):
        self.client.put(
            "/api/me/pools/MID",
            json={"champions": ["Ahri", "Zed"]},
            headers=self._auth(self.token_a),
        )
        resp = self.client.get("/api/me/pools", headers=self._auth(self.token_a))
        pools = resp.json()
        self.assertEqual(len(pools), 1)
        self.assertEqual(pools[0]["role"], "MID")
        self.assertEqual(pools[0]["champions"], ["Ahri", "Zed"])

    def test_save_replaces_existing(self):
        self.client.put(
            "/api/me/pools/TOP",
            json={"champions": ["Darius"]},
            headers=self._auth(self.token_a),
        )
        self.client.put(
            "/api/me/pools/TOP",
            json={"champions": ["Garen", "Sett"]},
            headers=self._auth(self.token_a),
        )
        resp = self.client.get("/api/me/pools", headers=self._auth(self.token_a))
        pools = resp.json()
        self.assertEqual(len(pools), 1)
        self.assertEqual(pools[0]["champions"], ["Garen", "Sett"])

    def test_save_multiple_roles(self):
        self.client.put(
            "/api/me/pools/MID", json={"champions": ["Ahri"]}, headers=self._auth(self.token_a)
        )
        self.client.put(
            "/api/me/pools/TOP", json={"champions": ["Darius"]}, headers=self._auth(self.token_a)
        )
        resp = self.client.get("/api/me/pools", headers=self._auth(self.token_a))
        self.assertEqual(len(resp.json()), 2)

    def test_delete_pool(self):
        self.client.put(
            "/api/me/pools/MID", json={"champions": ["Ahri"]}, headers=self._auth(self.token_a)
        )
        resp = self.client.delete("/api/me/pools/MID", headers=self._auth(self.token_a))
        self.assertEqual(resp.status_code, 204)

        pools = self.client.get("/api/me/pools", headers=self._auth(self.token_a)).json()
        self.assertEqual(pools, [])

    def test_delete_nonexistent_is_silent(self):
        resp = self.client.delete("/api/me/pools/JUNGLE", headers=self._auth(self.token_a))
        self.assertEqual(resp.status_code, 204)

    def test_invalid_role_returns_422(self):
        resp = self.client.put(
            "/api/me/pools/ARAM", json={"champions": ["Lux"]}, headers=self._auth(self.token_a)
        )
        self.assertEqual(resp.status_code, 422)

    # ── Auth ───────────────────────────────────────────────────────────────────

    def test_unauthenticated_returns_401(self):
        resp = self.client.get("/api/me/pools")
        self.assertEqual(resp.status_code, 401)

    # ── Cross-user isolation ───────────────────────────────────────────────────

    def test_user_a_cannot_see_user_b_pools(self):
        self.client.put(
            "/api/me/pools/MID", json={"champions": ["Zed"]}, headers=self._auth(self.token_b)
        )
        resp = self.client.get("/api/me/pools", headers=self._auth(self.token_a))
        self.assertEqual(resp.json(), [])

    def test_user_a_cannot_delete_user_b_pools(self):
        self.client.put(
            "/api/me/pools/TOP", json={"champions": ["Garen"]}, headers=self._auth(self.token_b)
        )
        self.client.delete("/api/me/pools/TOP", headers=self._auth(self.token_a))
        # User B's pool should still be there.
        resp = self.client.get("/api/me/pools", headers=self._auth(self.token_b))
        self.assertEqual(len(resp.json()), 1)
