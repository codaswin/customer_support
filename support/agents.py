"""The agents: a Manager that delegates and Specialists that answer from a Knowledge Base."""

from pathlib import Path

from autogen_agentchat.agents import AssistantAgent

NO_FIT = "NONE"
UNKNOWN = "UNKNOWN"
MANAGER_PROMPT = (
    "You are the Manager of a customer support team. Read the Support Request and "
    "reply with ONLY the name of the best-matching Specialist: IT (product and technical "
    "issues), HR (accounts and contracts: seats, ownership, terms) or Billing (money only: "
    "invoices, refunds, plan changes). If a request spans two, pick the single best match. "
    f"If none fits, reply {NO_FIT}."
)
KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
SPECIALIST_PROMPTS = {
    "IT": "You are the IT Specialist. Answer product and technical questions concisely.",
    "HR": "You are the HR Specialist. Answer account and contract questions concisely.",
    "Billing": "You are the Billing Specialist. Answer invoice, refund and plan questions "
    "concisely.",
}


def _normalise(text):
    return text.strip().strip(".!\"' ").upper()


async def _reply(agent, text):
    result = await agent.run(task=text)
    return result.messages[-1].content.strip()


async def delegate(model_client, message):
    """Return the chosen Specialist's name, or None when no Specialist fits."""
    manager = AssistantAgent("manager", model_client, system_message=MANAGER_PROMPT)
    label = await _reply(manager, message)
    wanted = _normalise(label)
    return next((name for name in SPECIALIST_PROMPTS if name.upper() == wanted), None)


def _system_message(specialist):
    kb = (KNOWLEDGE_DIR / f"{specialist}.md").read_text()
    return (
        f"{SPECIALIST_PROMPTS[specialist]}\nAnswer ONLY from this Knowledge Base:\n{kb}\n"
        f"If it does not contain the answer, reply with exactly {UNKNOWN}."
    )


async def answer(model_client, specialist, message, history=()):
    """Return the Specialist's reply, or None when its Knowledge Base has no answer.

    history is the thread so far as (sender, text) pairs, for follow-ups.
    """
    agent = AssistantAgent(
        specialist.lower(), model_client, system_message=_system_message(specialist)
    )
    transcript = "".join(f"{sender}: {text}\n" for sender, text in history)
    reply = await _reply(agent, f"{transcript}Customer: {message}" if transcript else message)
    return None if _normalise(reply) == UNKNOWN else reply
