from autogen_agentchat.agents import AssistantAgent

MANAGER_PROMPT = (
    "You are the Manager of a customer support team. Read the Support Request and "
    "reply with ONLY the name of the best-matching Specialist: IT (product and technical "
    "issues), HR (accounts and contracts: seats, ownership, terms) or Billing (money only: "
    "invoices, refunds, plan changes). If a request spans two, pick the single best match."
)
SPECIALIST_PROMPTS = {
    "IT": "You are the IT Specialist. Answer product and technical questions concisely.",
    "HR": "You are the HR Specialist. Answer account and contract questions concisely.",
    "Billing": "You are the Billing Specialist. Answer invoice, refund and plan questions concisely.",
}


async def _reply(agent, text):
    result = await agent.run(task=text)
    return result.messages[-1].content.strip()


async def delegate(model_client, message):
    manager = AssistantAgent("manager", model_client, system_message=MANAGER_PROMPT)
    label = await _reply(manager, message)
    # shortcut: unknown labels fall back to IT; the No-fit ticket replaces this
    return label if label in SPECIALIST_PROMPTS else "IT"


async def answer(model_client, specialist, message):
    agent = AssistantAgent(
        specialist.lower(), model_client, system_message=SPECIALIST_PROMPTS[specialist]
    )
    return await _reply(agent, message)
