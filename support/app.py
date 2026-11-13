from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from support.agents import answer, delegate
from support.store import Store


class SupportRequest(BaseModel):
    name: str
    email: str
    message: str


def create_app(model_client, db_path):
    app = FastAPI()
    store = Store(db_path)

    @app.post("/requests")
    async def submit(req: SupportRequest):
        specialist = await delegate(model_client, req.message)
        reply = await answer(model_client, specialist, req.message)
        thread_id = store.create_thread(req.name, req.email, specialist)
        store.add_message(thread_id, "customer", req.message)
        store.add_message(thread_id, specialist, reply)
        return {"thread_id": thread_id, "specialist": specialist, "answer": reply}

    @app.get("/threads/{thread_id}")
    def read_thread(thread_id: str):
        thread = store.get_thread(thread_id)
        if thread is None:
            raise HTTPException(404, "Support Thread not found")
        return thread

    return app
