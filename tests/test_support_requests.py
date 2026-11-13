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


def test_request_fitting_no_specialist_gets_the_fallback_number(tmp_path):
    app = create_app(ReplayChatCompletionClient(["NONE"]), tmp_path / "s.db", "+1-555-0199")
    body = TestClient(app).post("/requests", json=FORM).json()
    assert body["specialist"] is None
    assert "+1-555-0199" in body["answer"]
    thread = TestClient(app).get(f"/threads/{body['thread_id']}").json()
    assert [m["sender"] for m in thread["messages"]] == ["customer", "Manager"]


def test_unrecognised_manager_label_is_treated_as_no_fit(tmp_path):
    c = client(tmp_path / "s.db", "Marketing")
    assert c.post("/requests", json=FORM).json()["specialist"] is None


def test_specialist_without_an_answer_says_so_and_gives_the_fallback_number(tmp_path):
    app = create_app(ReplayChatCompletionClient(["IT", "UNKNOWN"]), tmp_path / "s.db", "+1-555-0199")
    body = TestClient(app).post("/requests", json=FORM).json()
    assert body["specialist"] == "IT"
    assert "don't know" in body["answer"]
    assert "+1-555-0199" in body["answer"]


def test_each_specialist_is_given_only_its_own_knowledge_base(tmp_path):
    model = ReplayChatCompletionClient(["Billing", "Refund issued."])
    TestClient(create_app(model, tmp_path / "s.db")).post("/requests", json=FORM)
    specialist_prompt = model.create_calls[1]["messages"][0].content
    assert "Refunds are available within 30 days" in specialist_prompt
    assert "reinstall it" not in specialist_prompt


def test_follow_up_is_answered_by_the_same_specialist_without_redelegation(tmp_path):
    c = client(tmp_path / "s.db", "HR", "First answer.", "Second answer.")
    thread_id = c.post("/requests", json=FORM).json()["thread_id"]
    r = c.post(f"/threads/{thread_id}/messages", json={"message": "And how many seats?"})
    assert r.status_code == 200
    assert r.json() == {"specialist": "HR", "answer": "Second answer."}
    thread = c.get(f"/threads/{thread_id}").json()
    assert [m["sender"] for m in thread["messages"]] == ["customer", "HR", "customer", "HR"]


def test_follow_up_survives_restart(tmp_path):
    db = tmp_path / "s.db"
    first = client(db, "HR", "First answer.", "Second answer.")
    thread_id = first.post("/requests", json=FORM).json()["thread_id"]
    first.post(f"/threads/{thread_id}/messages", json={"message": "More?"})
    thread = client(db).get(f"/threads/{thread_id}").json()
    assert len(thread["messages"]) == 4


def test_follow_up_on_no_fit_thread_gets_the_fallback_number_again(tmp_path):
    app = create_app(ReplayChatCompletionClient(["NONE"]), tmp_path / "s.db", "+1-555-0199")
    c = TestClient(app)
    thread_id = c.post("/requests", json=FORM).json()["thread_id"]
    r = c.post(f"/threads/{thread_id}/messages", json={"message": "Please?"})
    assert "+1-555-0199" in r.json()["answer"]


def test_follow_up_on_unknown_thread_is_not_found(tmp_path):
    r = client(tmp_path / "s.db").post("/threads/nope/messages", json={"message": "Hi"})
    assert r.status_code == 404


def test_invalid_submissions_are_rejected_with_a_clear_error(tmp_path):
    c = client(tmp_path / "s.db")
    for bad in [
        {**FORM, "message": "   "},
        {**FORM, "name": ""},
        {**FORM, "email": "not-an-email"},
    ]:
        r = c.post("/requests", json=bad)
        assert r.status_code == 422
        assert r.json()["detail"]


def test_empty_follow_up_is_rejected(tmp_path):
    c = client(tmp_path / "s.db", "HR", "First answer.")
    thread_id = c.post("/requests", json=FORM).json()["thread_id"]
    assert c.post(f"/threads/{thread_id}/messages", json={"message": " "}).status_code == 422


def test_unknown_thread_id_is_not_found(tmp_path):
    r = client(tmp_path / "s.db").get("/threads/nope")
    assert r.status_code == 404
    assert r.json()["detail"] == "Support Thread not found"


def test_model_replies_are_matched_tolerantly(tmp_path):
    c = client(tmp_path / "a.db", " hr. ", "Seats added.")
    assert c.post("/requests", json=FORM).json()["specialist"] == "HR"
    d = client(tmp_path / "b.db", "IT", "unknown.")
    assert "don't know" in d.post("/requests", json=FORM).json()["answer"]


def test_oversized_messages_are_rejected(tmp_path):
    c = client(tmp_path / "s.db")
    assert c.post("/requests", json={**FORM, "message": "x" * 5000}).status_code == 422


def test_thread_stops_accepting_follow_ups_at_the_cap(tmp_path, monkeypatch):
    monkeypatch.setattr("support.app.MAX_THREAD_MESSAGES", 4)
    c = client(tmp_path / "s.db", "HR", "a1", "a2", "a3")
    thread_id = c.post("/requests", json=FORM).json()["thread_id"]
    assert c.post(f"/threads/{thread_id}/messages", json={"message": "one"}).status_code == 200
    assert c.post(f"/threads/{thread_id}/messages", json={"message": "two"}).status_code == 429


def test_web_form_is_served_at_the_root(tmp_path):
    r = client(tmp_path / "s.db").get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert '<form id="request-form"' in r.text
