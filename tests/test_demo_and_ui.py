"""Demo mode (no API key) and the web form."""

import pytest
from fastapi.testclient import TestClient

from support.app import create_app
from support.demo import DemoModelClient
from tests.conftest import FORM


@pytest.fixture
def ask(tmp_path):
    client = TestClient(create_app(DemoModelClient(), tmp_path / "d.db"))
    return lambda message: client.post("/requests", json={**FORM, "message": message}).json()


@pytest.mark.parametrize(
    ("message", "specialist"),
    [
        ("How do I get a refund?", "Billing"),
        ("How do I add seats?", "HR"),
        ("The app crashes on start", "IT"),
        ("What is the weather today?", None),
    ],
)
def test_demo_mode_routes_requests(ask, message, specialist):
    assert ask(message)["specialist"] == specialist


def test_demo_mode_answers_from_the_knowledge_base(ask):
    assert "within 30 days" in ask("How do I get a refund?")["answer"]


def test_demo_mode_admits_when_the_knowledge_base_has_no_answer(ask):
    assert "don't know" in ask("Which error colour theme exists?")["answer"]


def test_web_form_is_served_at_the_root(make_client):
    r = make_client().get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert '<form id="request-form"' in r.text
