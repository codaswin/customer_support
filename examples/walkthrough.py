"""Scripted tour of the system in demo mode. No server and no API key needed.

Run from the repo root:  python examples/walkthrough.py
"""

import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="Using `httpx` with")  # upstream notice

from fastapi.testclient import TestClient  # noqa: E402

from support.app import create_app  # noqa: E402
from support.demo import DemoModelClient  # noqa: E402

CUSTOMER = {"name": "Ada Lovelace", "email": "ada@example.com"}


def show(who, text):
    print(f"  {who:>9}: {text}")


def scenario(client, title, message):
    print(f"\n== {title}")
    reply = client.post("/requests", json={**CUSTOMER, "message": message}).json()
    show("Customer", message)
    show(reply["specialist"] or "Manager", reply["answer"])
    return reply["thread_id"]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "walkthrough.db"
        client = TestClient(create_app(DemoModelClient(), db))

        scenario(client, "IT: technical issue", "My app crashes on start, what should I do?")
        scenario(client, "HR: account and contract", "How do I add more seats to my team?")
        thread = scenario(client, "Billing: money", "How do I get a refund?")

        print("\n== Follow-up stays with the same Specialist (Billing)")
        follow_up = "How do I change my plan?"
        reply = client.post(f"/threads/{thread}/messages", json={"message": follow_up}).json()
        show("Customer", follow_up)
        show(reply["specialist"], reply["answer"])

        scenario(
            client,
            "No Specialist fits: the Manager gives the Fallback Number",
            "What is the weather today?",
        )
        scenario(
            client,
            "Specialist has no answer: says so, gives the Fallback Number",
            "Which error colour theme exists?",
        )

        print("\n== The Support Thread survives an app restart")
        restarted = TestClient(create_app(DemoModelClient(), db))
        messages = restarted.get(f"/threads/{thread}").json()["messages"]
        print(f"  thread {thread[:8]}... still has {len(messages)} messages after restart")


if __name__ == "__main__":
    main()
