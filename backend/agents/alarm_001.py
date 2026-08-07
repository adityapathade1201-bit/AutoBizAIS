"""
Agent: Alarmy  (alarm-001)
----------------------------
Scheduling and reminder assistant — manages tasks, appointments, follow-ups,
and Google Calendar reminders for busy SME owners.
"""

from services import memory
from workflow.graph import build_agent_graph

AGENT_ID   = "alarm-001"
AGENT_NAME = "Alarmy"

SYSTEM_PROMPT = """You are Alarmy.
Role: Personal Executive Assistant.
Expert in: Reminders, Meetings, Deadlines, Scheduling, Follow-ups, Daily planning.
Tone: Helpful, Short, Organized.

Rules:
- You share business memory with all agents. Use it automatically. Do not ask for facts already known.
- Avoid one-line answers. Provide structured professional responses.
- Explain reasoning. Suggest next steps. Offer practical recommendations.
- When appropriate use bullet points and action plans.
"""

_graph = build_agent_graph(SYSTEM_PROMPT)


async def process(message: str) -> str:
    result = await _graph.ainvoke({
        "agent_id":       AGENT_ID,
        "agent_name":     AGENT_NAME,
        "system_prompt":  SYSTEM_PROMPT,
        "user_message":   message,
        "history":        [],
        "reply":          "",
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
