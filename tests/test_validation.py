"""Input validation and not-found handling."""

import pytest

from tests.conftest import FORM


@pytest.mark.parametrize(
    "bad",
    [
        {**FORM, "message": "   "},
        {**FORM, "message": "x" * 5000},
        {**FORM, "name": ""},
        {**FORM, "email": "not-an-email"},
    ],
)
def test_invalid_submissions_are_rejected_with_a_clear_error(make_client, bad):
    r = make_client().post("/requests", json=bad)
    assert r.status_code == 422
    assert r.json()["detail"]


def test_empty_follow_up_is_rejected(make_client):
    client = make_client("HR", "First answer.")
    thread_id = client.post("/requests", json=FORM).json()["thread_id"]
    assert client.post(f"/threads/{thread_id}/messages", json={"message": " "}).status_code == 422


def test_unknown_thread_id_is_not_found(make_client):
    client = make_client()
    for r in (
        client.get("/threads/nope"),
        client.post("/threads/nope/messages", json={"message": "Hi"}),
    ):
        assert r.status_code == 404
        assert r.json()["detail"] == "Support Thread not found"
