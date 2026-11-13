"""Keyword-based stand-in for the language model, so the app runs without an API key."""
import re

from autogen_ext.models.replay import ReplayChatCompletionClient

ROUTES = {
    "Billing": ("invoice", "refund", "bill", "charge", "plan", "price", "payment"),
    "HR": ("seat", "owner", "contract", "account", "renew", "cancel", "team"),
    "IT": ("crash", "password", "browser", "install", "error", "login", "app", "bug"),
}


def _words(text):
    # first five letters as a crude stem, so "refund" matches "refunds"
    return {w[:5] for w in re.findall(r"[a-z]+", text.lower())}


def _route(message):
    words = re.findall(r"[a-z]+", message.lower())
    for name, keys in ROUTES.items():
        if any(w.startswith(k) for w in words for k in keys):
            return name
    return "NONE"


def _from_knowledge_base(system, message):
    kb = system.split("Knowledge Base:\n", 1)[1].split("\nIf it does not", 1)[0]
    asked = _words(message) - _words("the a to i how do my is can and of what which")
    best = max(kb.splitlines(), key=lambda line: len(asked & _words(line)), default="")
    return best.lstrip("- ") if asked & _words(best) else "UNKNOWN"


class DemoModelClient(ReplayChatCompletionClient):
    """Replays one computed reply per call: a Manager label or a Knowledge Base line."""

    def __init__(self):
        super().__init__([""])

    async def create(self, messages, **kwargs):
        system, user = messages[0].content, messages[-1].content
        message = user.rsplit("Customer: ", 1)[-1]
        self.chat_completions = [
            _from_knowledge_base(system, message) if "Knowledge Base:" in system else _route(message)
        ]
        self._current_index = 0
        return await super().create(messages, **kwargs)
