"""Shared helpers. Every test drives the HTTP interface with a scripted fake model."""

import pytest
from autogen_ext.models.replay import ReplayChatCompletionClient
from fastapi.testclient import TestClient

from support.app import create_app

FORM = {"name": "Ada", "email": "ada@example.com", "message": "My app crashes on start"}
FALLBACK = "+1-555-0199"


@pytest.fixture
def make_client(tmp_path):
    """make_client(*script, db="s.db") -> TestClient whose model replays `script` in order.

    Each model call consumes one entry: first the Manager's label, then the Specialist's reply.
    Reusing the same `db` simulates an app restart.
    """

    def build(*script, db="s.db"):
        model = ReplayChatCompletionClient(list(script))
        client = TestClient(create_app(model, tmp_path / db, FALLBACK))
        client.model = model
        return client

    return build
