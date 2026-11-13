"""HTTP interface: the web form, Support Requests, follow-ups and Support Threads."""

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, StringConstraints

from support.agents import answer, delegate
from support.store import Store

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Email = Annotated[str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class FollowUp(BaseModel):
    message: Text


class SupportRequest(BaseModel):
    name: Text
    email: Email
    message: Text


INDEX_HTML = Path(__file__).parent / "static" / "index.html"
DEFAULT_FALLBACK_NUMBER = "+1-800-555-0100"
# Bound model cost per thread: messages stored, and turns sent to the model per follow-up.
MAX_THREAD_MESSAGES = 50
MAX_HISTORY_TURNS = 20


def create_app(model_client, db_path, fallback_number=DEFAULT_FALLBACK_NUMBER):
    app = FastAPI(title="Customer Support")
    store = Store(db_path)
    no_fit_reply = f"Sorry, we can't help with that here. Please call {fallback_number}."
    unknown_reply = f"I don't know the answer to that. Please call {fallback_number}."

    async def respond(specialist, message, history=()):
        """Return (sender, reply): the Manager's Fallback Number reply, or the Specialist's."""
        if specialist is None:
            return "Manager", no_fit_reply
        reply = await answer(model_client, specialist, message, history)
        return specialist, reply or unknown_reply

    @app.post("/requests")
    async def submit(req: SupportRequest):
        specialist = await delegate(model_client, req.message)
        sender, reply = await respond(specialist, req.message)
        thread_id = store.create_thread(
            req.name, req.email, specialist, [("customer", req.message), (sender, reply)]
        )
        return {"thread_id": thread_id, "specialist": specialist, "answer": reply}

    @app.post("/threads/{thread_id}/messages")
    async def follow_up(thread_id: str, req: FollowUp):
        thread = store.get_thread(thread_id)
        if thread is None:
            raise HTTPException(404, "Support Thread not found")
        specialist = thread["specialist"]
        if len(thread["messages"]) >= MAX_THREAD_MESSAGES:
            raise HTTPException(429, "This Support Thread is full")
        history = [(m["sender"], m["text"]) for m in thread["messages"]][-MAX_HISTORY_TURNS:]
        sender, reply = await respond(specialist, req.message, history)
        store.add_messages(thread_id, [("customer", req.message), (sender, reply)])
        return {"specialist": specialist, "answer": reply}

    @app.get("/", include_in_schema=False)
    async def web_form():
        return FileResponse(INDEX_HTML)

    # Endpoints are all async so the single shared SQLite connection stays on one thread.
    @app.get("/threads/{thread_id}")
    async def read_thread(thread_id: str):
        thread = store.get_thread(thread_id)
        if thread is None:
            raise HTTPException(404, "Support Thread not found")
        return thread

    return app
