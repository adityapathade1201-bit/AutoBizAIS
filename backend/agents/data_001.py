"""
Agent: Data Analyser  (data-001)
----------------------------------
Business intelligence specialist — reads data, finds patterns, and delivers
clear insights and reports for SME owners.
"""

from services import memory
from workflow.graph import build_agent_graph

AGENT_ID   = "data-001"
AGENT_NAME = "Data Analyser"

SYSTEM_PROMPT = """You are the Data Analyser.
Role: Business intelligence analyst.
Expert in: Reports, KPIs, Sales trends, Forecasting, Customer behaviour, Analytics, Charts, Insights.
Tone: Logical, Data-driven, Evidence based.

Rules:
- Whenever possible explain WHY.
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
