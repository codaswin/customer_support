import os

from autogen_ext.models.openai import OpenAIChatCompletionClient

from support.demo import DemoModelClient
from support.app import DEFAULT_FALLBACK_NUMBER, create_app

def _model_client():
    if os.environ.get("SUPPORT_DEMO"):
        return DemoModelClient()  # canned keyword replies, no API key needed
    return OpenAIChatCompletionClient(model=os.environ.get("SUPPORT_MODEL", "gpt-4o-mini"))


# Run with: OPENAI_API_KEY=... uvicorn support.main:app   (or SUPPORT_DEMO=1 for demo mode)
app = create_app(
    _model_client(),
    os.environ.get("SUPPORT_DB", "support.db"),
    os.environ.get("SUPPORT_FALLBACK_NUMBER", DEFAULT_FALLBACK_NUMBER),
)
