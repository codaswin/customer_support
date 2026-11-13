from autogen_ext.models.replay import ReplayChatCompletionClient
from fastapi.testclient import TestClient

from support.app import create_app

FORM = {"name": "Ada", "email": "ada@example.com", "message": "My app crashes on start"}


def client(db, *script):
    return TestClient(create_app(ReplayChatCompletionClient(list(script)), db))


def test_request_is_answered_by_it_specialist(tmp_path):
    c = client(tmp_path / "s.db", "IT", "Try reinstalling the app.")
    r = c.post("/requests", json=FORM)
    assert r.status_code == 200
    body = r.json()
    assert body["specialist"] == "IT"
    assert body["answer"] == "Try reinstalling the app."
    assert body["thread_id"]


def test_support_thread_survives_restart(tmp_path):
    db = tmp_path / "s.db"
    first = client(db, "IT", "Try reinstalling the app.")
    thread_id = first.post("/requests", json=FORM).json()["thread_id"]
    second = client(db)  # fresh app, same database
    r = second.get(f"/threads/{thread_id}")
    assert r.status_code == 200
    assert r.json()["messages"][-1]["text"] == "Try reinstalling the app."


def test_each_specialist_is_chosen_for_its_domain(tmp_path):
    for label, text in [("HR", "Add two seats."), ("Billing", "Refund issued.")]:
        c = client(tmp_path / f"{label}.db", label, text)
        body = c.post("/requests", json=FORM).json()
        assert body["specialist"] == label
        assert body["answer"] == text


def test_request_fitting_two_domains_goes_to_exactly_one_specialist(tmp_path):
    c = client(tmp_path / "s.db", "Billing", "Your invoice is corrected.")
    body = c.post("/requests", json=FORM).json()
    thread = c.get(f"/threads/{body['thread_id']}").json()
    assert body["specialist"] == "Billing"
    assert [m["sender"] for m in thread["messages"]] == ["customer", "Billing"]
