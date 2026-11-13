import os

from autogen_ext.models.openai import OpenAIChatCompletionClient

from support.app import create_app

# Run with: OPENAI_API_KEY=... uvicorn support.main:app
app = create_app(
    OpenAIChatCompletionClient(model=os.environ.get("SUPPORT_MODEL", "gpt-4o-mini")),
    os.environ.get("SUPPORT_DB", "support.db"),
)
