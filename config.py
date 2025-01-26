#!/usr/bin/env python3
import json
import os

import dotenv

dotenv.load_dotenv()

__all__ = ["DefaultConfig", "config"]


class DefaultConfig:
    PORT = int(os.environ.get("PORT", "8080"))
    ACTIVITY_API = os.environ.get("ACTIVITY_API", "")
    VALID_X_SHARED_SECRET_TOKEN = os.environ.get("VALID_X_SHARED_SECRET_TOKEN", "")
    VALID_X_WEBHOOK_SHARED_SECRET = os.environ.get("VALID_X_WEBHOOK_SHARED_SECRET", "")
    HMAC_KEYS = json.loads(os.environ.get("HMAC_KEYS", "{}"))
    _valid_tokens: list[str]

    def __init__(self):
        self._valid_tokens = list([t.strip() for t in self.VALID_X_SHARED_SECRET_TOKEN.lower().split(",")])

    def is_valid_token(self, token: str) -> bool:
        return token.lower() in self._valid_tokens

    def get_key_by_name(self, key_name: str | None) -> bytes:
        secret_as_bytes: bytes = self.HMAC_KEYS.get(key_name, self.VALID_X_WEBHOOK_SHARED_SECRET).encode(
            "utf-8"
        )
        return secret_as_bytes


config = DefaultConfig()
