# Customer Support

A multi-agent system that answers support requests from customers of a software company, routing each request to the specialist agent best placed to resolve it.

## Language

**Customer**:
A person who uses the software company's product and submits a Support Request, identified only by an unverified name and email.
_Avoid_: User, client

**Support Request**:
A single issue a Customer submits through the web form.
_Avoid_: Ticket, query, case

**Agent**:
An AI participant in the system. There are four: Manager and three Specialists (IT, HR, Billing).
_Avoid_: Bot, assistant, worker

**Manager**:
The Agent that is the first point of contact for each Support Request. It works out what the request is about and which Specialist can answer it, then delegates. It never replies to the Customer.
_Avoid_: Router, orchestrator, supervisor

**Specialist**:
An Agent that answers Support Requests within one domain and replies to the Customer directly. Answer-only: it takes no actions on accounts.
_Avoid_: Expert, worker agent

**Delegation**:
The Manager's hand-off of a Support Request to the Specialist chosen to answer it.
_Avoid_: Routing, escalation, transfer

**Support Thread**:
The conversation about one Support Request: the original question plus any Customer follow-ups, all answered by the same Specialist. It is persisted and resumed by its id.
_Avoid_: Ticket, chat, session

**Knowledge Base**:
The per-domain set of documents a Specialist answers from. Contents are mock data (this is an assignment, not a real client project).
_Avoid_: Docs, FAQ store, corpus

**Fallback Number**:
The phone number the Manager gives a Customer when no Specialist fits their Support Request, telling them to call it. This is the one case where the Manager replies.
_Avoid_: Helpline, escalation number
