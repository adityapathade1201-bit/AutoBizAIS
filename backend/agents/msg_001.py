"""
Agent: Messenger & Drafter  (msg-001)
--------------------------------------
Handles all written communication — emails, WhatsApp messages, formal letters,
and document drafts.
"""

from services import memory
from workflow.graph import build_agent_graph

AGENT_ID   = "msg-001"
AGENT_NAME = "Messenger & Drafter"

SYSTEM_PROMPT = """You are the Messenger & Drafter.
Role: Professional communication assistant.
Expert in: Emails, WhatsApp, Meeting notes, Business letters, Follow-up messages, Announcements.
Tone: Professional, Friendly, Polite.

Rules:
- Never answer finance, legal or marketing questions directly. Instead politely recommend the appropriate specialist.
- You share business memory with all agents. Use it automatically. Do not ask for facts already known.
- Avoid one-line answers. Provide structured professional responses.
- Explain reasoning. Suggest next steps. Offer practical recommendations.
- When appropriate use bullet points and action plans.
"""

# Compile the LangGraph once at import — reused for every message
_graph = build_agent_graph(SYSTEM_PROMPT)


async def process(message: str) -> str:
    """Invoke the LangGraph workflow and return the agent's reply."""
    result = await _graph.ainvoke({
        "agent_id":       AGENT_ID,
        "agent_name":     AGENT_NAME,
        "system_prompt":  SYSTEM_PROMPT,
        "user_message":   message,
        "history":        [],    # populated by node_load_memory
        "reply":          "",
        # Future fields (defaults)
        "plan":           "",
        "needs_tools":    False,
        "tool_calls":     [],
        "tool_results":   [],
        "awaiting_human":       False,
        "is_approval_response": False,
        "approval_decision":    "",
        "pending_action":       {},
    })
    reply = result["reply"]
    memory.save_turn(AGENT_ID, AGENT_NAME, message, reply)
    return reply
