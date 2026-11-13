from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from support.agents import answer, delegate
from support.store import Store


class FollowUp(BaseModel):
    message: str


class SupportRequest(BaseModel):
    name: str
    email: str
    message: str


DEFAULT_FALLBACK_NUMBER = "+1-800-555-0100"


def create_app(model_client, db_path, fallback_number=DEFAULT_FALLBACK_NUMBER):
    app = FastAPI()
    store = Store(db_path)
    no_fit_reply = f"Sorry, we can't help with that here. Please call {fallback_number}."
    unknown_reply = f"I don't know the answer to that. Please call {fallback_number}."

    @app.post("/requests")
    async def submit(req: SupportRequest):
        specialist = await delegate(model_client, req.message)
        if specialist is None:
            sender = "Manager"
            reply = no_fit_reply
        else:
            sender = specialist
            reply = await answer(model_client, specialist, req.message)
            reply = reply or unknown_reply
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
        if specialist is None:
            sender, reply = "Manager", no_fit_reply
        else:
            sender = specialist
            history = [(m["sender"], m["text"]) for m in thread["messages"]]
            reply = await answer(model_client, specialist, req.message, history) or unknown_reply
        store.add_messages(thread_id, [("customer", req.message), (sender, reply)])
        return {"specialist": specialist, "answer": reply}

    @app.get("/threads/{thread_id}")
    def read_thread(thread_id: str):
        thread = store.get_thread(thread_id)
        if thread is None:
            raise HTTPException(404, "Support Thread not found")
        return thread

    return app
