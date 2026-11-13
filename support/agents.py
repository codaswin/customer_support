from pathlib import Path

from autogen_agentchat.agents import AssistantAgent

MANAGER_PROMPT = (
    "You are the Manager of a customer support team. Read the Support Request and "
    "reply with ONLY the name of the best-matching Specialist: IT (product and technical "
    "issues), HR (accounts and contracts: seats, ownership, terms) or Billing (money only: "
    "invoices, refunds, plan changes). If a request spans two, pick the single best match. If none fits, reply NONE."
)
UNKNOWN = "UNKNOWN"
KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
SPECIALIST_PROMPTS = {
    "IT": "You are the IT Specialist. Answer product and technical questions concisely.",
    "HR": "You are the HR Specialist. Answer account and contract questions concisely.",
    "Billing": "You are the Billing Specialist. Answer invoice, refund and plan questions concisely.",
}


async def _reply(agent, text):
    result = await agent.run(task=text)
    return result.messages[-1].content.strip()


async def delegate(model_client, message):
    """Return the chosen Specialist's name, or None when no Specialist fits."""
    manager = AssistantAgent("manager", model_client, system_message=MANAGER_PROMPT)
    label = await _reply(manager, message)
    return label if label in SPECIALIST_PROMPTS else None


def _system_message(specialist):
    kb = (KNOWLEDGE_DIR / f"{specialist}.md").read_text()
    return (
        f"{SPECIALIST_PROMPTS[specialist]}\nAnswer ONLY from this Knowledge Base:\n{kb}\n"
        f"If it does not contain the answer, reply with exactly {UNKNOWN}."
    )


async def answer(model_client, specialist, message):
    """Return the Specialist's reply, or None when its Knowledge Base has no answer."""
    agent = AssistantAgent(specialist.lower(), model_client, system_message=_system_message(specialist))
    reply = await _reply(agent, message)
    return None if reply == UNKNOWN else reply
