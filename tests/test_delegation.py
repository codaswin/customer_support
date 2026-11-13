"""Support Requests: Delegation to a Specialist, the Fallback Number, and the Knowledge Base."""

import pytest

from tests.conftest import FALLBACK, FORM


def submit(client):
    r = client.post("/requests", json=FORM)
    assert r.status_code == 200
    return r.json()


def test_it_specialist_answers_and_the_manager_does_not(make_client):
    body = submit(make_client("IT", "Try reinstalling the app."))
    assert body["specialist"] == "IT"
    assert body["answer"] == "Try reinstalling the app."
    assert body["thread_id"]


@pytest.mark.parametrize("label", ["HR", "Billing"])
def test_each_specialist_is_chosen_for_its_domain(make_client, label):
    body = submit(make_client(label, "An answer."))
    assert (body["specialist"], body["answer"]) == (label, "An answer.")


def test_request_fitting_two_domains_goes_to_exactly_one_specialist(make_client):
    client = make_client("Billing", "Your invoice is corrected.")
    body = submit(client)
    thread = client.get(f"/threads/{body['thread_id']}").json()
    assert [m["sender"] for m in thread["messages"]] == ["customer", "Billing"]


def test_manager_labels_are_matched_tolerantly(make_client):
    assert submit(make_client(" hr. ", "Seats added."))["specialist"] == "HR"


def test_request_fitting_no_specialist_gets_the_fallback_number(make_client):
    client = make_client("NONE")
    body = submit(client)
    assert body["specialist"] is None
    assert FALLBACK in body["answer"]
    thread = client.get(f"/threads/{body['thread_id']}").json()
    assert [m["sender"] for m in thread["messages"]] == ["customer", "Manager"]


def test_unrecognised_manager_label_is_treated_as_no_fit(make_client):
    assert submit(make_client("Marketing"))["specialist"] is None


@pytest.mark.parametrize("reply", ["UNKNOWN", "unknown."])
def test_specialist_without_an_answer_says_so_and_gives_the_fallback_number(make_client, reply):
    body = submit(make_client("IT", reply))
    assert body["specialist"] == "IT"
    assert "don't know" in body["answer"]
    assert FALLBACK in body["answer"]


def test_each_specialist_is_given_only_its_own_knowledge_base(make_client):
    client = make_client("Billing", "Refund issued.")
    submit(client)
    specialist_prompt = client.model.create_calls[1]["messages"][0].content
    assert "Refunds are available within 30 days" in specialist_prompt
    assert "reinstall it" not in specialist_prompt
