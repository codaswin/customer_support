"""ASGI entrypoint: `uvicorn support.main:app`.

Uses the real OpenAI model when OPENAI_API_KEY is set, otherwise the keyword-based demo model
(force it with SUPPORT_DEMO=1).
"""

import os

from support.app import DEFAULT_FALLBACK_NUMBER, create_app
from support.demo import DemoModelClient


def _model_client():
    if os.environ.get("OPENAI_API_KEY") and not os.environ.get("SUPPORT_DEMO"):
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        return OpenAIChatCompletionClient(model=os.environ.get("SUPPORT_MODEL", "gpt-4o-mini"))
    return DemoModelClient()


app = create_app(
    _model_client(),
    os.environ.get("SUPPORT_DB", "support.db"),
    os.environ.get("SUPPORT_FALLBACK_NUMBER", DEFAULT_FALLBACK_NUMBER),
)
