from __future__ import annotations

import json
from base64 import b64decode, b64encode
from typing import Literal

import itsdangerous
from itsdangerous.exc import BadSignature
from starlette.datastructures import MutableHeaders, Secret
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RememberMeSessionMiddleware:
    """Signed cookie sessions with an opt-in persistent cookie lifetime."""

    def __init__(
        self,
        app: ASGIApp,
        secret_key: str | Secret,
        session_cookie: str = "session",
        remembered_max_age: int = 30 * 24 * 60 * 60,
        session_max_age: int = 12 * 60 * 60,
        path: str = "/",
        same_site: Literal["lax", "strict", "none"] = "lax",
        https_only: bool = False,
        domain: str | None = None,
    ) -> None:
        self.app = app
        self.signer = itsdangerous.TimestampSigner(str(secret_key))
        self.session_cookie = session_cookie
        self.remembered_max_age = remembered_max_age
        self.session_max_age = session_max_age
        self.path = path
        self.security_flags = "httponly; samesite=" + same_site
        if https_only:
            self.security_flags += "; secure"
        if domain is not None:
            self.security_flags += f"; domain={domain}"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        initial_session_was_empty = True

        if self.session_cookie in connection.cookies:
            data = connection.cookies[self.session_cookie].encode("utf-8")
            try:
                data = self.signer.unsign(data, max_age=self.remembered_max_age)
                scope["session"] = json.loads(b64decode(data))
                if not isinstance(scope["session"], dict):
                    raise BadSignature("Invalid session")
                if not scope["session"].get("remember_me", False):
                    self.signer.unsign(connection.cookies[self.session_cookie], max_age=self.session_max_age)
                initial_session_was_empty = False
            except (BadSignature, ValueError, TypeError):
                scope["session"] = {}
        else:
            scope["session"] = {}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                if scope["session"]:
                    session = scope["session"]
                    data = b64encode(json.dumps(session).encode("utf-8"))
                    signed_data = self.signer.sign(data).decode("utf-8")
                    max_age = (
                        f"Max-Age={self.remembered_max_age}; "
                        if session.get("remember_me", False)
                        else ""
                    )
                    headers = MutableHeaders(scope=message)
                    headers.append(
                        "Set-Cookie",
                        f"{self.session_cookie}={signed_data}; path={self.path}; "
                        f"{max_age}{self.security_flags}",
                    )
                elif not initial_session_was_empty:
                    headers = MutableHeaders(scope=message)
                    headers.append(
                        "Set-Cookie",
                        f"{self.session_cookie}=null; path={self.path}; "
                        "expires=Thu, 01 Jan 1970 00:00:00 GMT; "
                        f"{self.security_flags}",
                    )
            await send(message)

        await self.app(scope, receive, send_wrapper)
