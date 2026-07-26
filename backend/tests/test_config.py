import unittest

from app.config import Settings


class CorsOriginParsingTests(unittest.TestCase):
    """CORS origins come from the environment when the frontend is hosted separately,
    so a plain comma-separated string has to work as well as pydantic's JSON list."""

    def test_defaults_to_the_vite_dev_server(self):
        self.assertEqual(Settings().cors_origins, ["http://localhost:5173"])

    def test_parses_a_comma_separated_list(self):
        settings = Settings(
            cors_origins="https://poropilot.netlify.app, https://poropilot.app"
        )
        self.assertEqual(
            settings.cors_origins,
            ["https://poropilot.netlify.app", "https://poropilot.app"],
        )

    def test_strips_trailing_slashes(self):
        # A browser's Origin header never has a trailing slash, so one in config
        # would silently stop every request from matching.
        settings = Settings(cors_origins="https://poropilot.app/")
        self.assertEqual(settings.cors_origins, ["https://poropilot.app"])

    def test_parses_a_json_list(self):
        settings = Settings(cors_origins='["https://a.example", "https://b.example"]')
        self.assertEqual(settings.cors_origins, ["https://a.example", "https://b.example"])

    def test_blank_means_no_origins(self):
        self.assertEqual(Settings(cors_origins="   ").cors_origins, [])

    def test_accepts_a_real_list(self):
        settings = Settings(cors_origins=["https://poropilot.app"])
        self.assertEqual(settings.cors_origins, ["https://poropilot.app"])

    def test_origin_regex_is_unset_by_default(self):
        self.assertIsNone(Settings().cors_origin_regex)

    def test_origin_regex_is_read_from_config(self):
        pattern = r"https://.*--poropilot\.netlify\.app"
        self.assertEqual(Settings(cors_origin_regex=pattern).cors_origin_regex, pattern)


class CorsMiddlewareTests(unittest.TestCase):
    def test_preview_origin_is_allowed_by_the_regex(self):
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://poropilot.netlify.app"],
            allow_origin_regex=r"https://.*--poropilot\.netlify\.app",
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/ping")
        def ping() -> dict[str, str]:
            return {"status": "ok"}

        client = TestClient(app)
        preview = "https://deploy-preview-7--poropilot.netlify.app"
        resp = client.get("/ping", headers={"Origin": preview})
        self.assertEqual(resp.headers["access-control-allow-origin"], preview)

        resp = client.get("/ping", headers={"Origin": "https://evil.example"})
        self.assertNotIn("access-control-allow-origin", resp.headers)


if __name__ == "__main__":
    unittest.main()
