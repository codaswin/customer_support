"""Support Threads: persistence, reading, and follow-ups."""

from tests.conftest import FALLBACK, FORM


def start(client):
    return client.post("/requests", json=FORM).json()["thread_id"]


def test_thread_survives_restart(make_client):
    thread_id = start(make_client("IT", "Try reinstalling the app.", db="x.db"))
    restarted = make_client(db="x.db")
    r = restarted.get(f"/threads/{thread_id}")
    assert r.status_code == 200
    assert r.json()["messages"][-1]["text"] == "Try reinstalling the app."


def test_follow_up_is_answered_by_the_same_specialist_without_redelegation(make_client):
    # Only one Manager label is scripted: a second Delegation would consume "Second answer."
    client = make_client("HR", "First answer.", "Second answer.")
    thread_id = start(client)
    r = client.post(f"/threads/{thread_id}/messages", json={"message": "And how many seats?"})
    assert r.json() == {"specialist": "HR", "answer": "Second answer."}
    thread = client.get(f"/threads/{thread_id}").json()
    assert [m["sender"] for m in thread["messages"]] == ["customer", "HR", "customer", "HR"]


def test_follow_up_survives_restart(make_client):
    client = make_client("HR", "First answer.", "Second answer.", db="x.db")
    thread_id = start(client)
    client.post(f"/threads/{thread_id}/messages", json={"message": "More?"})
    assert len(make_client(db="x.db").get(f"/threads/{thread_id}").json()["messages"]) == 4


def test_follow_up_on_no_fit_thread_gets_the_fallback_number_again(make_client):
    client = make_client("NONE")
    thread_id = start(client)
    r = client.post(f"/threads/{thread_id}/messages", json={"message": "Please?"})
    assert FALLBACK in r.json()["answer"]


def test_thread_stops_accepting_follow_ups_at_the_cap(make_client, monkeypatch):
    monkeypatch.setattr("support.app.MAX_THREAD_MESSAGES", 4)
    client = make_client("HR", "a1", "a2", "a3")
    thread_id = start(client)
    assert client.post(f"/threads/{thread_id}/messages", json={"message": "one"}).status_code == 200
    assert client.post(f"/threads/{thread_id}/messages", json={"message": "two"}).status_code == 429
