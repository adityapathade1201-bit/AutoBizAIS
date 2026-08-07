"""
agents/registry.py
==================
Central registry of all available agents for multi-agent delegation.

This file contains ONLY data — no imports of agent modules — to avoid
circular imports when used by tools/delegate_to_agent.py.

Each entry:
    key        : short alias used by the planner / delegate_to_agent tool
    id         : agent_id used in memory (matches agents.json)
    module     : Python module name inside the agents/ package
    name       : Human-readable display name
    description: What this agent specialises in (shown to planner)
"""

AGENT_REGISTRY: dict[str, dict] = {
    "manager": {
        "id":          "mgr-001",
        "module":      "mgr_001",
        "name":        "Manager",
        "description": "Big-picture strategy, delegation, business planning, cross-functional decisions.",
    },
    "finance": {
        "id":          "fin-001",
        "module":      "fin_001",
        "name":        "Finance Expert",
        "description": "Cash flow, P&L, budgeting, pricing, break-even, funding options.",
    },
    "marketing": {
        "id":          "mkt-001",
        "module":      "mkt_001",
        "name":        "Marketing Lead",
        "description": "Campaigns, social media, branding, content calendar, ad copy.",
    },
    "sales": {
        "id":          "sales-001",
        "module":      "sales_001",
        "name":        "Sales Agent",
        "description": "Leads, pipeline, follow-ups, negotiation scripts, proposals.",
    },
    "messenger": {
        "id":          "msg-001",
        "module":      "msg_001",
        "name":        "Messenger & Drafter",
        "description": "Professional emails, WhatsApp messages, formal letters, document drafts.",
    },
    "legal": {
        "id":          "legal-001",
        "module":      "legal_001",
        "name":        "Legal Assistance",
        "description": "Contracts, compliance, business registration, legal awareness.",
    },
    "data": {
        "id":          "data-001",
        "module":      "data_001",
        "name":        "Data Analyser",
        "description": "Sales trends, customer behaviour, sentiment analysis, business reports.",
    },
    "ledger": {
        "id":          "ledger-001",
        "module":      "ledger_001",
        "name":        "Ledgerer",
        "description": "Invoices, expense records, accounts, GST entries, Tally guidance.",
    },
    "alarmy": {
        "id":          "alarm-001",
        "module":      "alarm_001",
        "name":        "Alarmy",
        "description": "Reminders, scheduling, Google Calendar, task prioritisation.",
    },
}
