from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from remember_me_session import RememberMeSessionMiddleware


def make_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(
        RememberMeSessionMiddleware,
        secret_key="test-secret",
        session_cookie="test_session",
        remembered_max_age=30 * 24 * 60 * 60,
    )

    @app.post("/login/{remember_me}")
    async def login(request: Request, remember_me: bool):
        request.session["user_id"] = 1
        request.session["remember_me"] = remember_me
        return {"status": "success"}

    @app.get("/me")
    async def me(request: Request):
        return {"user_id": request.session.get("user_id")}

    return TestClient(app)


def test_regular_login_uses_a_browser_session_cookie():
    with make_client() as client:
        response = client.post("/login/false")

        cookie = response.headers["set-cookie"].lower()
        assert "max-age" not in cookie
        assert "httponly" in cookie
        assert client.get("/me").json() == {"user_id": 1}


def test_remembered_login_uses_a_30_day_cookie():
    with make_client() as client:
        response = client.post("/login/true")

        cookie = response.headers["set-cookie"].lower()
        assert "max-age=2592000" in cookie
        assert "httponly" in cookie
        assert client.get("/me").json() == {"user_id": 1}


def test_browser_session_cookie_still_expires_on_the_server():
    from unittest.mock import patch
    with make_client() as client:
        with patch("itsdangerous.TimestampSigner.get_timestamp", return_value=1_000_000):
            client.post("/login/false")
        with patch("itsdangerous.TimestampSigner.get_timestamp", return_value=1_000_000 + 12 * 3600 + 1):
            assert client.get("/me").json() == {"user_id": None}


def test_remembered_session_is_valid_beyond_the_browser_session_limit():
    from unittest.mock import patch
    with make_client() as client:
        with patch("itsdangerous.TimestampSigner.get_timestamp", return_value=1_000_000):
            client.post("/login/true")
        with patch("itsdangerous.TimestampSigner.get_timestamp", return_value=1_000_000 + 13 * 3600):
            assert client.get("/me").json() == {"user_id": 1}
